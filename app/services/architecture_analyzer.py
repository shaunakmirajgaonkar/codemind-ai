"""
Builds a real dependency graph by statically parsing Python `import` /
`from ... import` statements with `ast` (no LLM needed for the graph itself —
deterministic and accurate), then renders it as Mermaid and asks the LLM for
a natural-language architecture summary on top of the real structure.
"""
import ast
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx

from app.llm_service import llm

logger = logging.getLogger("codemind.architecture")

IGNORE_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}


def _module_name(file_path: Path, root: Path) -> str:
    rel = file_path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def _extract_imports(source: str) -> List[str]:
    imports = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def build_dependency_graph(local_repo_path: str) -> Tuple[nx.DiGraph, Dict[str, int]]:
    root = Path(local_repo_path)
    graph = nx.DiGraph()
    module_files: Dict[str, Path] = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fname in filenames:
            if fname.endswith(".py"):
                fpath = Path(dirpath) / fname
                mod = _module_name(fpath, root)
                module_files[mod] = fpath
                graph.add_node(mod)

    for mod, fpath in module_files.items():
        try:
            source = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for imported in _extract_imports(source):
            # only keep edges to modules that exist within this repo (internal deps)
            matches = [m for m in module_files if imported == m or imported.startswith(m + ".")]
            for match in matches:
                if match != mod:
                    graph.add_edge(mod, match)

    in_degrees = dict(graph.in_degree())
    return graph, in_degrees


def graph_to_mermaid(graph: nx.DiGraph, max_nodes: int = 60) -> str:
    """Render as a Mermaid flowchart. Truncates very large graphs to the most
    connected nodes so the diagram stays readable."""
    if graph.number_of_nodes() > max_nodes:
        degrees = dict(graph.degree())
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:max_nodes]
        graph = graph.subgraph(top_nodes)

    lines = ["flowchart TD"]

    def safe_id(name: str) -> str:
        return name.replace(".", "_").replace("-", "_")

    for node in graph.nodes():
        lines.append(f'    {safe_id(node)}["{node}"]')
    for src, dst in graph.edges():
        lines.append(f"    {safe_id(src)} --> {safe_id(dst)}")

    return "\n".join(lines)


def detect_circular_dependencies(graph: nx.DiGraph) -> List[List[str]]:
    return [cycle for cycle in nx.simple_cycles(graph)]


def analyze_architecture(local_repo_path: str, language_summary: dict) -> dict:
    graph, in_degrees = build_dependency_graph(local_repo_path)
    mermaid = graph_to_mermaid(graph)
    cycles = detect_circular_dependencies(graph)

    most_depended_on = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]

    system = (
        "You are CodeMind AI's architecture analyst. Given a real, statically "
        "extracted module dependency structure and language breakdown, describe "
        "the likely architecture (layering, entry points, core modules), note "
        "any risks (tight coupling, circular dependencies), and suggest "
        "improvements. Be concrete, referencing actual module names given."
    )
    user = (
        f"Language breakdown: {language_summary}\n\n"
        f"Total modules: {graph.number_of_nodes()}, total internal dependency edges: {graph.number_of_edges()}\n"
        f"Most depended-on modules (module, num_dependents): {most_depended_on}\n"
        f"Circular dependency chains found: {cycles if cycles else 'none'}\n"
    )
    narrative = llm.chat(system, user)

    return {
        "mermaid_diagram": mermaid,
        "total_modules": graph.number_of_nodes(),
        "total_dependencies": graph.number_of_edges(),
        "most_depended_on_modules": most_depended_on,
        "circular_dependencies": cycles,
        "narrative_summary": narrative,
    }
