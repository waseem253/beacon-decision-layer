"""Session-scoped conversation memory.

Keeps recent turns per session so follow-up questions ("what about the second
one?") can be resolved with prior context. In-memory by design for the demo;
the :class:`ConversationMemory` API is small enough that swapping the dict for
Redis or a database is a contained change — noted in the README.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Turn:
    query: str
    answer: str
    timestamp: float = field(default_factory=time.time)


class ConversationMemory:
    """Per-session ring of recent turns."""

    def __init__(self, max_turns: int = 6) -> None:
        self._max_turns = max_turns
        self._sessions: dict[str, list[Turn]] = {}

    def add(self, session_id: str, query: str, answer: str) -> None:
        turns = self._sessions.setdefault(session_id, [])
        turns.append(Turn(query=query, answer=answer))
        # Keep only the most recent window.
        if len(turns) > self._max_turns:
            del turns[: -self._max_turns]

    def history(self, session_id: str, limit: int | None = None) -> list[Turn]:
        turns = self._sessions.get(session_id, [])
        return turns[-limit:] if limit else list(turns)

    def context_text(self, session_id: str, limit: int = 3) -> str:
        """Recent turns rendered as text, to widen retrieval and ground the
        synthesizer when a query is a terse follow-up."""
        recent = self.history(session_id, limit=limit)
        if not recent:
            return ""
        return " ".join(f"{t.query} {t.answer}" for t in recent)

    def session_count(self) -> int:
        return len(self._sessions)

    def total_turns(self) -> int:
        return sum(len(t) for t in self._sessions.values())


# One process-wide store. Fine for a single-instance demo; see README.
memory = ConversationMemory()
