"""
ChromaDB persistent vector store (local disk, no server needed). Stores code
chunks with metadata (repo_id, file_path, start_line, end_line, language) so
retrieval can be scoped per-repository and cited back to exact source lines.
"""
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.embeddings import embed_texts, embed_query

logger = logging.getLogger("codemind.vectorstore")

_client = chromadb.PersistentClient(
    path=settings.CHROMA_PERSIST_DIR,
    settings=ChromaSettings(anonymized_telemetry=False),
)

COLLECTION_NAME = "codemind_chunks"


def get_collection():
    return _client.get_or_create_collection(name=COLLECTION_NAME)


def add_chunks(chunks: List[Dict[str, Any]]) -> int:
    """
    chunks: list of dicts with keys: id, text, repo_id, file_path,
            start_line, end_line, language
    """
    if not chunks:
        return 0

    collection = get_collection()
    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [
        {
            "repo_id": c["repo_id"],
            "file_path": c["file_path"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "language": c.get("language", "unknown"),
        }
        for c in chunks
    ]
    embeddings = embed_texts(texts)

    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    logger.info(f"Indexed {len(chunks)} chunks into vector store")
    return len(chunks)


def query_similar(
    query: str, repo_id: Optional[str] = None, top_k: int = 8
) -> List[Dict[str, Any]]:
    collection = get_collection()
    query_embedding = embed_query(query)

    where = {"repo_id": repo_id} if repo_id else None
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({"text": doc, "metadata": meta, "distance": dist})
    return hits


def delete_repo_chunks(repo_id: str) -> None:
    collection = get_collection()
    collection.delete(where={"repo_id": repo_id})
