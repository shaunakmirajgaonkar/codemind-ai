"""
Splits source files into semantically meaningful chunks for embedding.
Python files are split at function/class boundaries via the `ast` module
(precise, no LLM calls needed). Other languages fall back to a sliding
line-window so every language is still supported.
"""
import ast
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger("codemind.chunking")

EXT_LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "typescript",
    ".jsx": "javascript", ".java": "java", ".go": "go", ".rs": "rust",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".rb": "ruby",
    ".php": "php", ".cs": "csharp", ".swift": "swift", ".kt": "kotlin",
    ".sql": "sql", ".md": "markdown", ".yaml": "yaml", ".yml": "yaml",
    ".json": "json", ".sh": "bash", ".html": "html", ".css": "css",
}


def detect_language(file_path: str) -> str:
    return EXT_LANGUAGE_MAP.get(Path(file_path).suffix.lower(), "unknown")


def _chunk_id(repo_id: str, file_path: str, start: int, end: int) -> str:
    raw = f"{repo_id}:{file_path}:{start}:{end}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _chunk_python_ast(source: str, file_path: str, repo_id: str) -> List[Dict[str, Any]]:
    """Split on top-level function/class definitions; fall back to whole-file
    line chunking if parsing fails (syntax errors, partial files, etc.)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _chunk_by_lines(source, file_path, repo_id)

    lines = source.splitlines()
    top_level_nodes = [
        n for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]

    if not top_level_nodes:
        return _chunk_by_lines(source, file_path, repo_id)

    chunks = []
    covered_end = 0
    for node in top_level_nodes:
        start_line = node.lineno
        end_line = getattr(node, "end_lineno", start_line)

        # capture module-level code between previous node and this one
        if start_line - 1 > covered_end:
            gap_text = "\n".join(lines[covered_end:start_line - 1]).strip()
            if gap_text:
                chunks.append({
                    "id": _chunk_id(repo_id, file_path, covered_end + 1, start_line - 1),
                    "text": gap_text,
                    "repo_id": repo_id,
                    "file_path": file_path,
                    "start_line": covered_end + 1,
                    "end_line": start_line - 1,
                    "language": "python",
                })

        snippet = "\n".join(lines[start_line - 1:end_line])
        label = f"# {file_path} :: {getattr(node, 'name', 'block')} (lines {start_line}-{end_line})\n"
        chunks.append({
            "id": _chunk_id(repo_id, file_path, start_line, end_line),
            "text": label + snippet,
            "repo_id": repo_id,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "language": "python",
        })
        covered_end = end_line

    return chunks


def _chunk_by_lines(source: str, file_path: str, repo_id: str) -> List[Dict[str, Any]]:
    lines = source.splitlines()
    max_lines = settings.CHUNK_MAX_LINES
    overlap = settings.CHUNK_OVERLAP_LINES
    language = detect_language(file_path)

    chunks = []
    i = 0
    while i < len(lines):
        end = min(i + max_lines, len(lines))
        snippet = "\n".join(lines[i:end])
        if snippet.strip():
            chunks.append({
                "id": _chunk_id(repo_id, file_path, i + 1, end),
                "text": f"# {file_path} (lines {i + 1}-{end})\n{snippet}",
                "repo_id": repo_id,
                "file_path": file_path,
                "start_line": i + 1,
                "end_line": end,
                "language": language,
            })
        if end == len(lines):
            break
        i = end - overlap

    return chunks


def chunk_file(source: str, file_path: str, repo_id: str) -> List[Dict[str, Any]]:
    language = detect_language(file_path)
    if language == "python":
        return _chunk_python_ast(source, file_path, repo_id)
    return _chunk_by_lines(source, file_path, repo_id)
