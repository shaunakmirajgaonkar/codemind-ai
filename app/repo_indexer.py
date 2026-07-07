"""
Repository ingestion pipeline:
 1. Clone (git URL) or point to a local path.
 2. Walk files, skip binaries/junk (.git, node_modules, venv, build dirs).
 3. Chunk each file (AST-aware for Python).
 4. Embed chunks locally and upsert into ChromaDB.
 5. Persist repo/file metadata to the relational DB.
"""
import json
import logging
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Optional

from git import Repo as GitRepo
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Repository, IndexedFile
from app.utils.chunking import chunk_file, detect_language
from app.vector_store import add_chunks, delete_repo_chunks

logger = logging.getLogger("codemind.indexer")

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build",
    ".idea", ".vscode", "target", ".next", "coverage", "vendor", "storage",
}
IGNORE_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz", ".lock", ".min.js",
    ".mp4", ".mp3", ".db", ".sqlite", ".so", ".pyc", ".class",
}


def _clone_if_url(source: str) -> str:
    """If `source` looks like a git URL, clone it to a temp dir and return
    the local path. Otherwise assume it's already a local path."""
    if source.startswith("http://") or source.startswith("https://") or source.startswith("git@"):
        clone_dir = tempfile.mkdtemp(prefix="codemind_repo_")
        clone_url = source
        if settings.GITHUB_TOKEN and "github.com" in source and source.startswith("https://"):
            clone_url = source.replace("https://", f"https://{settings.GITHUB_TOKEN}@")
        logger.info(f"Cloning {source} -> {clone_dir}")
        GitRepo.clone_from(clone_url, clone_dir, depth=1)
        return clone_dir
    return source


def _should_skip(path: Path) -> bool:
    if any(part in IGNORE_DIRS for part in path.parts):
        return True
    if path.suffix.lower() in IGNORE_EXTS:
        return True
    try:
        if path.stat().st_size > settings.MAX_FILE_SIZE_KB * 1024:
            return True
    except OSError:
        return True
    return False


def index_repository(db: Session, name: str, source: str) -> Repository:
    local_path = _clone_if_url(source)

    repo = Repository(name=name, source_path=source, local_clone_path=local_path)
    db.add(repo)
    db.commit()
    db.refresh(repo)

    total_chunks = 0
    lang_counter = Counter()
    all_chunks = []

    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fname in files:
            fpath = Path(root) / fname
            if _should_skip(fpath):
                continue
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not text.strip():
                continue

            rel_path = str(fpath.relative_to(local_path))
            language = detect_language(rel_path)
            lang_counter[language] += 1

            chunks = chunk_file(text, rel_path, repo.id)
            all_chunks.extend(chunks)

            indexed_file = IndexedFile(
                repository_id=repo.id,
                file_path=rel_path,
                language=language,
                num_lines=len(text.splitlines()),
                num_chunks=len(chunks),
            )
            db.add(indexed_file)
            total_chunks += len(chunks)

    # embed + store in vector DB (batched to keep memory bounded)
    batch_size = 64
    for i in range(0, len(all_chunks), batch_size):
        add_chunks(all_chunks[i:i + batch_size])

    repo.total_files = sum(lang_counter.values())
    repo.total_chunks = total_chunks
    repo.language_summary = json.dumps(dict(lang_counter))
    db.commit()
    db.refresh(repo)

    logger.info(f"Indexed repo '{name}': {repo.total_files} files, {total_chunks} chunks")
    return repo


def reindex_repository(db: Session, repo: Repository) -> Repository:
    delete_repo_chunks(repo.id)
    db.query(IndexedFile).filter(IndexedFile.repository_id == repo.id).delete()
    db.delete(repo)
    db.commit()
    return index_repository(db, repo.name, repo.source_path)


def cleanup_clone(repo: Repository) -> None:
    """Remove temp clone directory once indexing is done, if it was a git clone."""
    if repo.local_clone_path and repo.local_clone_path.startswith(tempfile.gettempdir()):
        shutil.rmtree(repo.local_clone_path, ignore_errors=True)
