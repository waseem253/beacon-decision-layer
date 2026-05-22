"""Beacon — AI knowledge & decision-support layer.

FastAPI service that federates retrieval across the firm's knowledge sources,
synthesises a grounded answer, keeps conversation context, and — for decision
questions — returns a structured, review-gated decision brief. Every answer
carries full source provenance.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from .decisions import build_decision_brief, is_decision_query
from .knowledge import FIRM, SOURCES, source_catalog
from .memory import memory
from .retriever import KnowledgeRetriever
from .synthesizer import AnswerSynthesizer

app = FastAPI(title="Beacon", version="1.0.0")

# Built once per process: the index is read-only after construction.
_retriever = KnowledgeRetriever()
_synthesizer = AnswerSynthesizer()

_STATIC = Path(__file__).resolve().parent.parent / "static"


class _Stats:
    """Lightweight operational counters that back the dashboard."""

    def __init__(self) -> None:
        self.queries = 0
        self.decision_queries = 0
        self.review_flagged = 0
        self._confidence_sum = 0.0
        self.recent: deque[dict] = deque(maxlen=8)

    def record(self, *, query: str, confidence_value: float, confidence: str,
               mode: str, is_decision: bool, needs_review: bool) -> None:
        self.queries += 1
        self._confidence_sum += confidence_value
        if is_decision:
            self.decision_queries += 1
        if needs_review:
            self.review_flagged += 1
        self.recent.appendleft({
            "query": query,
            "confidence": confidence,
            "mode": mode,
            "is_decision": is_decision,
            "needs_review": needs_review,
        })

    @property
    def average_confidence(self) -> float:
        return self._confidence_sum / self.queries if self.queries else 0.0

    @property
    def review_rate(self) -> float:
        return self.review_flagged / self.queries if self.queries else 0.0


_stats = _Stats()


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    session_id: str = Field(default="default", max_length=120)
    source: str | None = None


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((_STATIC / "index.html").read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "synthesis_mode": _synthesizer.mode,
        "documents": sum(s["document_count"] for s in source_catalog()),
    }


@app.get("/api/sources")
def api_sources() -> dict:
    return {"firm": FIRM, "sources": source_catalog()}


@app.post("/api/query")
def api_query(req: QueryRequest) -> JSONResponse:
    """Core pipeline: retrieve → synthesise → (decision brief) → remember."""
    if req.source and req.source not in SOURCES:
        return JSONResponse(
            {"error": f"unknown source '{req.source}'"}, status_code=400
        )

    context_text = memory.context_text(req.session_id)

    # Retrieve on the query; if it is a terse follow-up that finds little,
    # widen the search with recent conversation context.
    results = _retriever.search(req.query, k=4, source=req.source)
    if context_text and (not results or results[0].score < 0.12):
        widened = _retriever.search(f"{context_text} {req.query}", k=4, source=req.source)
        if widened and (not results or widened[0].score > results[0].score):
            results = widened

    confidence_label, confidence_value = _retriever.confidence(results)
    synthesis = _synthesizer.synthesize(req.query, results, context_text)

    decision = is_decision_query(req.query)
    decision_brief = None
    needs_review = False
    if decision:
        decision_brief = build_decision_brief(
            req.query, synthesis.answer, results, confidence_label, confidence_value
        )
        needs_review = decision_brief["needs_human_review"]

    memory.add(req.session_id, req.query, synthesis.answer)
    _stats.record(
        query=req.query,
        confidence_value=confidence_value,
        confidence=confidence_label,
        mode=synthesis.mode,
        is_decision=decision,
        needs_review=needs_review,
    )

    return JSONResponse({
        "query": req.query,
        "session_id": req.session_id,
        "answer": synthesis.answer,
        "synthesis_mode": synthesis.mode,
        "confidence": confidence_label,
        "confidence_value": round(confidence_value, 3),
        "citations": [r.as_citation() for r in results],
        "is_decision": decision,
        "decision_brief": decision_brief,
        "source_filter": req.source,
    })


@app.get("/api/history")
def api_history(session_id: str = "default") -> dict:
    turns = memory.history(session_id)
    return {
        "session_id": session_id,
        "turns": [
            {"query": t.query, "answer": t.answer, "timestamp": t.timestamp}
            for t in turns
        ],
    }


@app.get("/api/dashboard")
def api_dashboard() -> dict:
    catalog = source_catalog()
    return {
        "firm": FIRM,
        "synthesis_mode": _synthesizer.mode,
        "sources": catalog,
        "source_count": len(catalog),
        "total_documents": sum(s["document_count"] for s in catalog),
        "queries_handled": _stats.queries,
        "decision_queries": _stats.decision_queries,
        "average_confidence": round(_stats.average_confidence, 3),
        "review_rate": round(_stats.review_rate, 3),
        "active_sessions": memory.session_count(),
        "recent_queries": list(_stats.recent),
    }
