"""
Local embedding generation via sentence-transformers. Runs entirely on-device
(CPU or Apple Silicon MPS) - no API calls, no per-token cost.
"""
import logging
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger("codemind.embeddings")


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    logger.info(f"Loading local embedding model: {settings.EMBEDDING_MODEL}")
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedder()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]
