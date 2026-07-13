"""
Semantic-drift backend.

Pluggable by design: `similarity(a, b) -> float in [0, 1]` is the only
contract. The default backend is TF-IDF + cosine similarity via
scikit-learn -- lightweight, offline, fully reproducible, no API key,
no GPU, and fast enough to run on every CI build.

A stronger sentence-embedding backend (e.g. sentence-transformers'
all-MiniLM-L6-v2) can be dropped in behind the same interface for
better paraphrase detection; it's kept optional because the model
download makes it too heavy for a CI cold-start and it isn't required
to demonstrate the core idea.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Protocol


class SimilarityBackend(Protocol):
    def similarity(self, a: str, b: str) -> float:
        ...


class TfidfSimilarity:
    """Cosine similarity over TF-IDF vectors of the two description strings."""

    def __init__(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer  # local import

        self._vectorizer_cls = TfidfVectorizer

    def similarity(self, a: str, b: str) -> float:
        a, b = (a or "").strip(), (b or "").strip()
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        vectorizer = self._vectorizer_cls().fit([a, b])
        vecs = vectorizer.transform([a, b])
        # cosine similarity of two rows without importing sklearn.metrics,
        # to keep the dependency surface minimal
        import numpy as np

        v1, v2 = vecs[0].toarray()[0], vecs[1].toarray()[0]
        denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
        if denom == 0:
            return 0.0
        return float(np.dot(v1, v2) / denom)


class SequenceMatcherSimilarity:
    """Zero-dependency fallback if scikit-learn isn't available."""

    def similarity(self, a: str, b: str) -> float:
        a, b = (a or ""), (b or "")
        return SequenceMatcher(None, a, b).ratio()


def default_backend() -> SimilarityBackend:
    try:
        return TfidfSimilarity()
    except ImportError:  # pragma: no cover
        return SequenceMatcherSimilarity()
