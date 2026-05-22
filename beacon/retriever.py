"""Knowledge retrieval — hybrid TF-IDF + keyword scoring, pure Python.

Why pure Python: the retriever runs with zero external services, so the demo
works offline and deploys to a serverless runtime with no vector database to
provision. The :class:`KnowledgeRetriever` API (``search`` returning scored,
source-tagged results) is the seam a production deployment swaps for a real
vector store — pgvector, FAISS, a managed index — without the rest of the
system changing.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .knowledge import Document, documents

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is",
    "are", "was", "were", "be", "been", "this", "that", "it", "as", "at", "by",
    "from", "we", "our", "us", "i", "you", "they", "their", "what", "which",
    "how", "do", "does", "can", "should", "would", "will", "about", "into",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Below this top score, an answer is treated as weakly grounded.
LOW_CONFIDENCE_THRESHOLD = 0.08


def tokenize(text: str) -> list[str]:
    """Lowercase, split on word characters, drop stopwords and 1-char tokens."""
    return [
        t for t in _TOKEN_RE.findall(text.lower())
        if t not in _STOPWORDS and len(t) > 1
    ]


@dataclass
class RetrievalResult:
    document: Document
    score: float
    matched_terms: list[str]

    def as_citation(self) -> dict:
        """Provenance payload — what makes every answer traceable to a source."""
        return {
            "document_id": self.document.id,
            "title": self.document.title,
            "source": self.document.source,
            "source_name": self.document.source_name,
            "date": self.document.date,
            "score": round(self.score, 4),
            "matched_terms": self.matched_terms,
        }


class KnowledgeRetriever:
    """In-memory hybrid retriever over the knowledge corpus.

    Scoring blends TF-IDF cosine similarity (semantic-ish term weighting) with
    a keyword boost for query terms that hit a document's title or tags — the
    title/tag hit is a strong signal that pure TF-IDF under-weights on short
    queries.
    """

    #: Weight of the title/tag keyword boost relative to the cosine score.
    _KEYWORD_BOOST = 0.35

    def __init__(self, docs: list[Document] | None = None) -> None:
        self._docs = docs if docs is not None else documents()
        self._doc_tokens: dict[str, list[str]] = {}
        self._doc_vectors: dict[str, dict[str, float]] = {}
        self._idf: dict[str, float] = {}
        self._build_index()

    def _build_index(self) -> None:
        n = len(self._docs)
        doc_freq: Counter[str] = Counter()
        for doc in self._docs:
            tokens = tokenize(f"{doc.title} {doc.text}")
            self._doc_tokens[doc.id] = tokens
            for term in set(tokens):
                doc_freq[term] += 1

        # Smoothed IDF so a term in every document still has a small weight.
        self._idf = {
            term: math.log((n + 1) / (df + 1)) + 1.0
            for term, df in doc_freq.items()
        }

        for doc in self._docs:
            self._doc_vectors[doc.id] = self._vectorize(self._doc_tokens[doc.id])

    def _vectorize(self, tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        counts = Counter(tokens)
        length = len(tokens)
        return {
            term: (count / length) * self._idf.get(term, 1.0)
            for term, count in counts.items()
        }

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        shared = set(a) & set(b)
        dot = sum(a[t] * b[t] for t in shared)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def search(
        self, query: str, k: int = 4, source: str | None = None
    ) -> list[RetrievalResult]:
        """Return the top-``k`` documents for ``query``, highest score first.

        ``source`` optionally restricts retrieval to one knowledge source.
        """
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        query_vec = self._vectorize(query_tokens)
        query_set = set(query_tokens)

        results: list[RetrievalResult] = []
        for doc in self._docs:
            if source and doc.source != source:
                continue
            cosine = self._cosine(query_vec, self._doc_vectors[doc.id])

            # Keyword boost: query terms hitting the title or tags.
            title_tag_terms = set(tokenize(doc.title)) | {
                t for tag in doc.tags for t in tokenize(tag)
            }
            keyword_hits = query_set & title_tag_terms
            boost = self._KEYWORD_BOOST * (len(keyword_hits) / len(query_set))

            score = cosine + boost
            if score <= 0:
                continue
            matched = sorted(query_set & set(self._doc_tokens[doc.id]))
            results.append(RetrievalResult(doc, score, matched))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]

    @staticmethod
    def confidence(results: list[RetrievalResult]) -> tuple[str, float]:
        """Map the top result's score to a confidence label + 0-1 value."""
        if not results:
            return "none", 0.0
        top = results[0].score
        # Squash an unbounded score into a readable 0-1 range.
        value = min(1.0, top / 0.6)
        if top < LOW_CONFIDENCE_THRESHOLD:
            return "low", value
        if value >= 0.6:
            return "high", value
        return "medium", value
