# Beacon — AI Knowledge & Decision-Support Layer

An internal knowledge layer that lets a team **ask its own business information
in plain language**. Beacon federates retrieval across multiple internal
sources, returns a grounded answer with **full source traceability**, keeps
conversation context, and — for operational decision questions — returns a
structured **decision brief with a human-review gate**.

It is an internal business platform, not a public chatbot.

**Live demo:** https://beacon-decision-layer.vercel.app

> Built by Waseem Iftikhar as a demonstration MVP. The sample data models a
> fictional consulting firm, "Meridian Consulting Group".

---

## What it does

| Capability | How Beacon does it |
|---|---|
| Retrieve relevant information | Federated hybrid retrieval (TF-IDF + keyword) across every connected source |
| Maintain context between interactions | Session conversation memory resolves terse follow-ups |
| Support operational decisions | Decision questions return a structured brief, not just an answer |
| Traceability of responses | Every answer carries the exact document ids it rests on |
| Human review where needed | Thin or partial evidence raises a review flag before the business acts |
| Organise knowledge | Four logical sources, each independently scoped or searched together |

Try these on the live demo:

- *"What is the status of the Atterly Retail engagement?"* — a plain answer
- *"Should we start a new engagement before April?"* — a decision brief
- *"Which pricing approach was recommended for Vance Manufacturing?"*

---

## Architecture

```
Consultant — a plain question or an operational decision
   → Beacon API (FastAPI, /api/query — one pipeline for both)
   → Federated retrieval (hybrid TF-IDF + keyword, scored & source-tagged)
        → 4 knowledge sources: project records · methodology · client KB · deliverables
   → Answer synthesis (Claude when an API key is set; extractive fallback otherwise)
        → conversation memory provides follow-up context
   → decision question?  yes → decision brief (recommendation + grounding + review gate)
                          no  → grounded answer
   → response: answer + every source cited (full traceability)
```

Diagrams: [`docs/architecture.png`](docs/architecture.png) ·
[`docs/sequence.png`](docs/sequence.png).

### Design choices

- **One pipeline, two shapes.** A plain question gets a direct grounded
  answer; a decision question gets a structured, review-gated brief. The
  caller does not pick — the system detects.
- **Grounded and traceable.** Nothing is asserted without a source. Every
  response lists the document ids it used; the decision brief shows what it
  is grounded in.
- **Reliable by design.** Answer synthesis uses Claude when an API key is
  present and a deterministic extractive synthesizer otherwise. The fallback
  is not a stub — it always returns a real, cited answer, so a provider
  outage degrades answer quality rather than breaking the platform.
- **Swappable retrieval.** The retriever is pure Python (no vector DB to
  provision) behind a `search()` API. Production swaps it for pgvector / a
  managed index without touching the rest of the system.
- **Practical architecture.** Knowledge sources, retrieval, synthesis,
  memory and decision logic are separate modules — the seams a real
  deployment needs to plug live connectors into.

---

## Run it locally

Requires Python 3.10+.

```bash
git clone https://github.com/waseem253/beacon-decision-layer.git
cd beacon-decision-layer

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn beacon.app:app --reload
# open http://localhost:8000
```

Run the test suite (20 tests):

```bash
pip install pytest
pytest -q
```

### Optional — Claude-powered synthesis

Beacon runs fully without any API key (deterministic extractive synthesis).
To enable Claude synthesis, set:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

The `/health` endpoint reports which mode is active.

---

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | The web UI |
| `/api/query` | POST | `{query, session_id, source?}` → grounded answer (+ decision brief) |
| `/api/sources` | GET | The connected knowledge sources |
| `/api/history` | GET | Conversation history for a session |
| `/api/dashboard` | GET | Operational stats — queries, confidence, review rate |
| `/health` | GET | Liveness + active synthesis mode |

---

## Project layout

```
beacon/
  app.py          FastAPI app — the query pipeline + endpoints
  retriever.py    Hybrid TF-IDF + keyword retrieval (swappable for a vector DB)
  synthesizer.py  Answer synthesis — Claude + deterministic fallback
  decisions.py    Decision detection + structured decision brief
  memory.py       Session-scoped conversation memory
  knowledge.py    Sample corpus, shaped like the real domain model
static/index.html The web UI
api/index.py      Vercel entrypoint
tests/            20-test verification suite
docs/             Architecture + sequence diagrams
```

## Limitations (demo MVP)

- The corpus is bundled sample data. A real deployment feeds `knowledge.py`'s
  document structure from live connectors (document stores, project systems,
  databases) — the retriever and everything above it are unchanged.
- Retrieval is pure-Python TF-IDF — excellent for this corpus size and for a
  zero-dependency demo; production scale swaps in a vector index behind the
  same `search()` API.
- Conversation memory is in-process. On a serverless host it is reliable
  within a warm instance; production uses Redis or a database — a contained
  change behind the `ConversationMemory` API.

## License

MIT
