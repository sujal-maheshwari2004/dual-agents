from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from backend.config import get_settings
from backend.schemas import MemoryRecord


class LongTermMemoryStore:
    """MongoDB-backed user memory with a no-op mode for local development."""

    def __init__(
        self,
        mongodb_uri: str | None,
        database_name: str,
        collection_name: str,
    ) -> None:
        if mongodb_uri:
            try:
                from motor.motor_asyncio import AsyncIOMotorClient
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "MongoDB memory requires the 'motor' package. Run 'uv sync' "
                    "or install project dependencies before setting MONGODB_URI."
                ) from exc
            self._client = AsyncIOMotorClient(mongodb_uri)
        else:
            self._client = None

        self._collection = (
            self._client[database_name][collection_name] if self._client is not None else None
        )

    @property
    def is_configured(self) -> bool:
        return self._collection is not None

    async def get_recent(self, user_id: str, limit: int = 10) -> list[MemoryRecord]:
        if self._collection is None:
            return []

        cursor = (
            self._collection.find({"user_id": user_id}, {"_id": 0, "key": 1, "value": 1, "source": 1})
            .sort("created_at", -1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [self._document_to_record(document) for document in documents]

    async def save_memory(self, user_id: str, key: str, value: str, source: str = "chat") -> bool:
        if self._collection is None:
            return False

        now = datetime.now(UTC)
        await self._collection.update_one(
            {"user_id": user_id, "key": key},
            {
                "$set": {
                    "value": value,
                    "source": source,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        return True

    async def clear(self, user_id: str) -> bool:
        if self._collection is None:
            return True

        result = await self._collection.delete_many({"user_id": user_id})
        return result.acknowledged

    @staticmethod
    def _document_to_record(document: dict[str, Any]) -> MemoryRecord:
        return MemoryRecord(
            key=str(document.get("key", "")),
            value=str(document.get("value", "")),
            source=str(document.get("source", "long_term")),
        )


def extract_memory_candidates(message: str) -> list[tuple[str, str]]:
    lowered = message.lower().strip()
    candidates: list[tuple[str, str]] = []

    def add_candidate(key: str, value: str) -> None:
        normalized_value = value.strip(" .")
        if normalized_value and all(existing_value != normalized_value for _, existing_value in candidates):
            candidates.append((key, normalized_value))

    remember_markers = ("remember that ", "remember this: ", "please remember ")
    for marker in remember_markers:
        if marker in lowered:
            value = message[lowered.index(marker) + len(marker) :]
            add_candidate("remembered_fact", value)

    preference_markers = ("i prefer ", "i like ", "my favorite ", "my favourite ")
    for marker in preference_markers:
        if marker in lowered:
            value = message[lowered.index(marker) :]
            add_candidate("preference", value)
            break

    identity_markers = ("my name is ", "i live in ", "i work at ")
    for marker in identity_markers:
        if marker in lowered:
            value = message[lowered.index(marker) :]
            key = marker.strip().replace(" ", "_")
            add_candidate(key, value)
            break

    return candidates[:3]


@lru_cache
def get_long_term_memory() -> LongTermMemoryStore:
    settings = get_settings()
    return LongTermMemoryStore(
        mongodb_uri=settings.mongodb_uri,
        database_name=settings.mongodb_database,
        collection_name=settings.mongodb_memory_collection,
    )
