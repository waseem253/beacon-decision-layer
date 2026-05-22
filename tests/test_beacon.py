"""Verification suite for Beacon.

Covers retrieval correctness, the synthesis fallback, decision detection,
conversation memory, and the HTTP API end to end.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from beacon.app import app
from beacon.decisions import build_decision_brief, is_decision_query
from beacon.memory import ConversationMemory
from beacon.retriever import KnowledgeRetriever
from beacon.synthesizer import AnswerSynthesizer

client = TestClient(app)


# -- retriever -------------------------------------------------------------

def test_retriever_finds_the_relevant_engagement():
    r = KnowledgeRetriever()
    results = r.search("Atterly Retail supply chain status")
    assert results
    assert results[0].document.id == "PR-101"


def test_retriever_source_filter_restricts_results():
    r = KnowledgeRetriever()
    results = r.search("pricing model", source="methodology")
    assert results
    assert all(res.document.source == "methodology" for res in results)


def test_retriever_confidence_high_for_strong_match():
    r = KnowledgeRetriever()
    label, value = r.confidence(r.search("Northwind Bank operating model redesign"))
    assert label in ("high", "medium")
    assert value > 0


def test_retriever_confidence_low_for_irrelevant_query():
    r = KnowledgeRetriever()
    label, _ = r.confidence(r.search("zxqw nonsense xylophone unrelated"))
    assert label in ("low", "none")


def test_retriever_returns_traceable_citations():
    r = KnowledgeRetriever()
    cite = r.search("Vance pricing")[0].as_citation()
    assert cite["document_id"]
    assert cite["source_name"]
    assert "score" in cite


# -- synthesizer -----------------------------------------------------------

def test_extractive_synthesis_produces_a_cited_answer():
    r = KnowledgeRetriever()
    results = r.search("agency staffing spend Halcyon Health")
    synth = AnswerSynthesizer()
    answer = synth._extractive("How high is agency staffing spend?", results)
    assert answer
    # extractive answers always carry an inline [doc-id] citation
    assert "[" in answer and "]" in answer


def test_synthesis_handles_no_results_gracefully():
    synth = AnswerSynthesizer()
    out = synth.synthesize("anything", [])
    assert "No knowledge source" in out.answer


# -- decision support ------------------------------------------------------

def test_decision_query_detection():
    assert is_decision_query("Should we start a new engagement before April?")
    assert is_decision_query("Which pricing approach is best for Vance?")
    assert not is_decision_query("What is the status of the Atterly engagement?")


def test_decision_brief_flags_low_confidence_for_review():
    r = KnowledgeRetriever()
    results = r.search("portfolio capacity new engagement")
    brief = build_decision_brief(
        "Should we start a new engagement?", "Some answer", results, "low", 0.05
    )
    assert brief["type"] == "decision_brief"
    assert brief["needs_human_review"] is True
    assert brief["review_reason"]
    assert brief["relevant_knowledge"]


def test_decision_brief_high_confidence_needs_no_review():
    brief = build_decision_brief("q", "a", [], "high", 0.9)
    assert brief["needs_human_review"] is False
    assert brief["review_reason"] is None


# -- memory ----------------------------------------------------------------

def test_memory_keeps_and_windows_turns():
    mem = ConversationMemory(max_turns=3)
    for i in range(5):
        mem.add("sess", f"q{i}", f"a{i}")
    hist = mem.history("sess")
    assert len(hist) == 3
    assert hist[-1].query == "q4"
    assert "q4" in mem.context_text("sess")


# -- HTTP API --------------------------------------------------------------

def test_health_ok():
    body = client.get("/health").json()
    assert body["ok"] is True
    assert body["documents"] == 18


def test_api_sources_lists_four_sources():
    body = client.get("/api/sources").json()
    assert len(body["sources"]) == 4
    assert sum(s["document_count"] for s in body["sources"]) == 18


def test_api_query_returns_answer_with_citations():
    body = client.post("/api/query", json={
        "query": "What is the status of the Atterly Retail engagement?",
        "session_id": "t-plain",
    }).json()
    assert body["answer"]
    assert body["citations"]
    assert body["citations"][0]["document_id"]
    assert body["is_decision"] is False


def test_api_query_decision_returns_brief():
    body = client.post("/api/query", json={
        "query": "Should we start a new engagement before April?",
        "session_id": "t-decision",
    }).json()
    assert body["is_decision"] is True
    assert body["decision_brief"] is not None
    assert "recommendation" in body["decision_brief"]


def test_api_query_rejects_unknown_source():
    resp = client.post("/api/query", json={
        "query": "anything", "session_id": "t", "source": "no-such-source",
    })
    assert resp.status_code == 400


def test_api_query_source_filter_scopes_results():
    body = client.post("/api/query", json={
        "query": "pricing", "session_id": "t-scope", "source": "methodology",
    }).json()
    assert body["source_filter"] == "methodology"
    assert all(c["source"] == "methodology" for c in body["citations"])


def test_api_history_records_turns():
    client.post("/api/query", json={"query": "first question", "session_id": "t-hist"})
    body = client.get("/api/history", params={"session_id": "t-hist"}).json()
    assert len(body["turns"]) >= 1


def test_api_dashboard_reports_stats():
    client.post("/api/query", json={"query": "methodology pricing", "session_id": "t-dash"})
    body = client.get("/api/dashboard").json()
    assert body["total_documents"] == 18
    assert body["source_count"] == 4
    assert body["queries_handled"] >= 1


def test_index_page_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Beacon" in resp.text
