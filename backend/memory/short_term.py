from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from threading import RLock


@dataclass(slots=True)
class ConversationTurn:
    user_message: str
    assistant_reply: str


class ShortTermMemoryStore:
    """Stores the last N user/assistant turns for each session."""

    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self._sessions: dict[str, deque[ConversationTurn]] = {}
        self._lock = RLock()

    def get_history(self, session_id: str) -> list[ConversationTurn]:
        with self._lock:
            history = self._sessions.get(session_id)
            return list(history) if history is not None else []

    def append_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_reply: str,
    ) -> list[ConversationTurn]:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = deque(maxlen=self.max_turns)

            self._sessions[session_id].append(
                ConversationTurn(
                    user_message=user_message,
                    assistant_reply=assistant_reply,
                )
            )
            return list(self._sessions[session_id])

    def clear_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None


@lru_cache
def get_short_term_memory() -> ShortTermMemoryStore:
    return ShortTermMemoryStore()
