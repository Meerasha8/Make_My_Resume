"""Text embeddings and relevance scoring for the RAG features (resume content selection and the profile chat).

Relevance is a hybrid of:
- semantic similarity from a small local embedding model (fastembed + BAAI/bge-small-en-v1.5, 384 dims), and
- lexical similarity from a hashed bag of words, which rewards exact matches on technology names.
If the model can't be loaded, scoring degrades to lexical-only instead of failing.
"""

import functools
import hashlib
import logging
import os
import re
from typing import List, Sequence

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384
SEMANTIC_WEIGHT = 0.75
_CACHE_LIMIT = 5000

_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9+#]*(?:\.[a-z0-9]+)*")
_STOPWORDS = frozenset(
    "a an and are as at be by for from has have i in is it its me my of on or our that the their this to we with you your "
    "what which who where when how do does did am was were will would can could should any all".split()
)

_embedding_cache: dict[tuple[str, str], List[float]] = {}


def _tokens(text: str) -> List[str]:
    return [token for token in _TOKEN_PATTERN.findall((text or "").lower()) if token not in _STOPWORDS]


def lexical_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Feature-hashed bag of unigrams and bigrams, L2-normalised: cosine similarity approximates keyword overlap."""
    tokens = _tokens(text)
    vector = [0.0] * dim
    for feature in tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]:
        digest = int.from_bytes(hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest(), "big")
        vector[digest % dim] += 1.0 if (digest >> 32) & 1 else -1.0
    norm = sum(value * value for value in vector) ** 0.5
    return [value / norm for value in vector] if norm else vector


@functools.lru_cache(maxsize=1)
def _load_model():
    if os.getenv("EMBEDDING_BACKEND", "fastembed").lower() == "lexical":
        return None
    try:
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"))
    except Exception as exc:
        logger.warning("Embedding model unavailable, using lexical relevance only: %s", exc)
        return None


def embed_texts(texts: Sequence[str], kind: str = "passage") -> List[List[float]]:
    """Embed texts in one batch. kind="query" for questions/job descriptions, "passage" for profile content."""
    model = _load_model()
    if model is None:
        return [lexical_embedding(text) for text in texts]

    missing = list(dict.fromkeys(text for text in texts if (kind, text) not in _embedding_cache))
    if missing:
        vectors = model.query_embed(missing) if kind == "query" else model.passage_embed(missing)
        if len(_embedding_cache) + len(missing) > _CACHE_LIMIT:
            _embedding_cache.clear()
        for text, vector in zip(missing, vectors):
            _embedding_cache[(kind, text)] = [float(value) for value in vector]
    return [_embedding_cache[(kind, text)] for text in texts]


def embed_text(text: str) -> List[float]:
    return embed_texts([text], kind="query")[0]


def cosine_similarity(vec1: Sequence[float], vec2: Sequence[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = sum(a * a for a in vec1) ** 0.5
    norm_b = sum(b * b for b in vec2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def relevance_scores(query: str, documents: Sequence[str]) -> List[float]:
    """Hybrid semantic + lexical relevance of each document to the query (higher is more relevant)."""
    if not documents:
        return []
    query_lexical = lexical_embedding(query)
    lexical = [cosine_similarity(query_lexical, lexical_embedding(document)) for document in documents]
    if _load_model() is None:
        return lexical
    query_vector = embed_texts([query], kind="query")[0]
    semantic = [cosine_similarity(query_vector, vector) for vector in embed_texts(documents, kind="passage")]
    return [SEMANTIC_WEIGHT * s + (1 - SEMANTIC_WEIGHT) * l for s, l in zip(semantic, lexical)]
