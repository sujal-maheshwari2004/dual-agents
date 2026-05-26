from fastapi import APIRouter

from backend.memory import get_long_term_memory
from backend.schemas import MemoryDeleteResponse, MemoryResponse

router = APIRouter(tags=["memory"])


@router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(user_id: str) -> MemoryResponse:
    memory = get_long_term_memory()
    return MemoryResponse(user_id=user_id, memories=await memory.get_recent(user_id))


@router.delete("/memory/{user_id}", response_model=MemoryDeleteResponse)
async def clear_memory(user_id: str) -> MemoryDeleteResponse:
    memory = get_long_term_memory()
    return MemoryDeleteResponse(user_id=user_id, cleared=await memory.clear(user_id))
