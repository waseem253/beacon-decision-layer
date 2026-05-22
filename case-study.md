# Beacon — AI Knowledge & Decision-Support Layer

**Live demo:** https://beacon-decision-layer.vercel.app
**Repository:** https://github.com/waseem253/beacon-decision-layer

## The problem

A consulting firm's working knowledge is scattered — project records,
methodology playbooks, per-client context, past deliverables. Teams lose time
searching across those sources and coordinating information by hand. The firm
wanted an internal AI layer that helps people *access, understand and use*
that information efficiently — and supports operational decisions — without
becoming a black box. An internal business platform, not a public chatbot.

## The build

Beacon is a FastAPI service with one query pipeline that handles two shapes of
question. A plain question returns a grounded answer; an operational decision
question returns a structured **decision brief**. Either way, retrieval is
federated across four knowledge sources and every answer carries the exact
document ids it rests on — full traceability by default.

The pipeline: hybrid TF-IDF + keyword retrieval scores and source-tags
documents across all sources; answer synthesis runs on Claude when an API key
is present and a deterministic extractive synthesizer otherwise; conversation
memory resolves follow-up questions; and a decision-detection step decides
whether to wrap the answer as a review-gated brief.

## Architecture

```
Consultant — plain question or operational decision
   → Beacon API (FastAPI · /api/query)
   → Federated retrieval — hybrid TF-IDF + keyword, scored & source-tagged
        → 4 sources: project records · methodology · client KB · deliverables
   → Answer synthesis — Claude, or deterministic extractive fallback
        → conversation memory supplies follow-up context
   → decision question? → decision brief (recommendation + grounding + review gate)
                          → otherwise: grounded answer
   → response: answer + every source cited
```

Retrieval, synthesis, memory and decision logic are separate modules — the
seams a production deployment uses to plug in live connectors and a real
vector store, with the rest of the system unchanged.

## Why it matters

- **Grounded and traceable** — nothing is asserted without a source; every
  response lists the documents it used, so any claim can be checked.
- **Decisions get a gate** — when evidence is thin or partial, the decision
  brief flags that a person should review before the business acts, instead
  of asserting false confidence.
- **Reliable by design** — the extractive synthesizer is a real fallback, not
  a stub; a provider outage degrades answer quality rather than breaking the
  platform. The demo runs fully offline with no API key.
- **Practical to extend** — swapping the bundled corpus for live connectors,
  or the pure-Python retriever for a vector DB, is configuration behind a
  stable interface.

## Verification

A 20-test suite covers retrieval correctness, the synthesis fallback, decision
detection, conversation memory and the HTTP API end to end. The live demo was
driven and verified in-browser.

## Stack

Python · FastAPI · Claude (Anthropic) · hybrid retrieval / RAG · pytest · Vercel

---

**Waseem Iftikhar** — AI / Backend Engineer
