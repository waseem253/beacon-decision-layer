"""Decision-support layer.

A plain question gets a plain answer. An *operational decision* question gets
a structured decision brief: the recommendation, the knowledge it rests on, a
confidence read, and — when the evidence is not strong enough to act blindly —
a human-review flag. That review gate is the "human review flows where needed"
capability: the system is explicit about when a person should look before the
business acts.
"""

from __future__ import annotations

from .retriever import RetrievalResult

# Phrases that signal the user is asking for a decision, not just a fact.
_DECISION_SIGNALS = (
    "should we", "should i", "should the", "should they",
    "which ", "recommend", "best option", "best approach", "best way",
    "decide", "decision", "prioriti", "go ahead", "approve",
    "next step", "what do we do", "can we start", "is it safe",
    "trade-off", "tradeoff", " versus ", "do we proceed",
)


def is_decision_query(query: str) -> bool:
    """True if the query reads as an operational-decision question."""
    q = f" {query.lower().strip()} "
    return any(signal in q for signal in _DECISION_SIGNALS)


def build_decision_brief(
    query: str,
    answer: str,
    results: list[RetrievalResult],
    confidence_label: str,
    confidence_value: float,
) -> dict:
    """Wrap an answer as a structured, traceable decision brief."""
    relevant_knowledge = [
        {
            "document_id": r.document.id,
            "title": r.document.title,
            "source_name": r.document.source_name,
            "snippet": _snippet(r.document.text),
        }
        for r in results
    ]

    needs_review = confidence_label in ("low", "medium", "none")
    if confidence_label in ("low", "none"):
        review_reason = (
            "Evidence is thin — the knowledge base does not strongly support a "
            "recommendation. A person should confirm before acting."
        )
    elif confidence_label == "medium":
        review_reason = (
            "Evidence is partial. The recommendation is reasonable but a person "
            "should sanity-check it against context the knowledge base may not hold."
        )
    else:
        review_reason = None

    return {
        "type": "decision_brief",
        "question": query,
        "recommendation": answer,
        "relevant_knowledge": relevant_knowledge,
        "confidence": confidence_label,
        "confidence_value": round(confidence_value, 3),
        "needs_human_review": needs_review,
        "review_reason": review_reason,
    }


def _snippet(text: str, limit: int = 180) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"
