"""Answer synthesis over retrieved knowledge.

Two interchangeable backends behind one interface:

* **Claude** — used when ``ANTHROPIC_API_KEY`` is set. Grounded generation with
  inline source citations.
* **Extractive** — a deterministic fallback that composes the answer from the
  highest-overlap sentences of the retrieved documents. No API key, no network.

The fallback is not a stub: it always produces a real, source-cited answer, so
the demo works identically offline and a provider outage degrades quality
rather than breaking the product.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from .retriever import RetrievalResult, tokenize

CLAUDE_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_PROMPT = (
    "You are the answer engine inside an internal knowledge and decision-support "
    "platform for a consulting firm. Answer the question using ONLY the numbered "
    "knowledge excerpts provided. Cite every claim inline with its document id in "
    "square brackets, e.g. [PR-101]. If the excerpts do not fully answer the "
    "question, say so plainly rather than guessing. Be concise and businesslike — "
    "this is an internal operations tool, not a chatbot. Never invent document ids."
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


@dataclass
class SynthesisResult:
    answer: str
    mode: str  # "claude" or "extractive"


class AnswerSynthesizer:
    def __init__(self) -> None:
        self._api_key = os.getenv("ANTHROPIC_API_KEY")

    @property
    def mode(self) -> str:
        return "claude" if self._api_key else "extractive"

    def synthesize(
        self,
        query: str,
        results: list[RetrievalResult],
        context_text: str = "",
    ) -> SynthesisResult:
        if not results:
            return SynthesisResult(
                answer=(
                    "No knowledge source contains information relevant to that "
                    "question. Try rephrasing, or check whether the relevant "
                    "source has been connected."
                ),
                mode=self.mode,
            )
        if self._api_key:
            try:
                return SynthesisResult(self._claude(query, results, context_text), "claude")
            except Exception:
                # Provider failure must not break the product — fall back.
                pass
        return SynthesisResult(self._extractive(query, results), "extractive")

    # -- Claude backend ----------------------------------------------------

    def _claude(self, query: str, results: list[RetrievalResult], context_text: str) -> str:
        import anthropic

        excerpts = "\n\n".join(
            f"[{r.document.id}] {r.document.title} "
            f"(source: {r.document.source_name}, {r.document.date})\n{r.document.text}"
            for r in results
        )
        user_parts = [f"Knowledge excerpts:\n\n{excerpts}"]
        if context_text:
            user_parts.append(f"Recent conversation context:\n{context_text}")
        user_parts.append(f"Question: {query}")

        client = anthropic.Anthropic(api_key=self._api_key)
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=600,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": "\n\n".join(user_parts)}],
        )
        return "".join(
            block.text for block in resp.content if block.type == "text"
        ).strip()

    # -- Extractive fallback ----------------------------------------------

    def _extractive(self, query: str, results: list[RetrievalResult]) -> str:
        """Compose an answer from the sentences that overlap the query most.

        The lead sentence is always the strongest match; trailing sentences are
        only added when they are genuinely relevant (>=2 query terms and a score
        close to the lead) so the answer stays tight rather than padded.
        """
        query_terms = set(tokenize(query))
        # (score, overlap_count, sentence, doc_id)
        picked: list[tuple[float, int, str, str]] = []

        for result in results[:3]:
            for sentence in _SENTENCE_SPLIT.split(result.document.text):
                sentence = sentence.strip()
                if len(sentence) < 30:
                    continue
                overlap = query_terms & set(tokenize(sentence))
                if not overlap:
                    continue
                # Sentence relevance, nudged by the document's own retrieval score.
                score = len(overlap) + 0.5 * result.score
                picked.append((score, len(overlap), sentence, result.document.id))

        if not picked:
            # Query terms hit titles/tags but no sentence — summarise top doc.
            top = results[0].document
            return (
                f"The most relevant source is \"{top.title}\" [{top.id}]. "
                f"{top.text.split('. ')[0]}."
            )

        picked.sort(key=lambda x: x[0], reverse=True)
        top_score = picked[0][0]
        seen: set[str] = set()
        lines: list[str] = []
        for score, overlap_count, sentence, doc_id in picked:
            key = sentence[:50]
            if key in seen:
                continue
            # The lead sentence always lands; later ones must earn their place.
            if lines and (overlap_count < 2 or score < 0.4 * top_score):
                continue
            seen.add(key)
            ending = "" if sentence.endswith((".", "!", "?")) else "."
            lines.append(f"{sentence}{ending} [{doc_id}]")
            if len(lines) >= 3:
                break
        return " ".join(lines)
