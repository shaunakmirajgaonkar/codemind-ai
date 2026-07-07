"""
Shared RAG retrieval helper used by every feature (chat, review, bug
detection, test generation, docs). Keeps retrieval logic in one place so
citation formatting stays consistent everywhere.
"""
from typing import List, Optional

from app.vector_store import query_similar


def retrieve_context(query: str, repo_id: Optional[str], top_k: int = 8) -> str:
    hits = query_similar(query, repo_id=repo_id, top_k=top_k)
    if not hits:
        return "No relevant code context found in the indexed repository."

    blocks = []
    for h in hits:
        meta = h["metadata"]
        header = f"### {meta['file_path']} (lines {meta['start_line']}-{meta['end_line']})"
        blocks.append(f"{header}\n```{meta.get('language', '')}\n{h['text']}\n```")
    return "\n\n".join(blocks)


def retrieve_hits(query: str, repo_id: Optional[str], top_k: int = 8):
    return query_similar(query, repo_id=repo_id, top_k=top_k)
