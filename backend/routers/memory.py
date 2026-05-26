from fastapi import APIRouter

from backend.schemas import MemoryDeleteResponse, MemoryResponse

router = APIRouter(tags=["memory"])


@router.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_memory(user_id: str) -> MemoryResponse:
    return MemoryResponse(user_id=user_id, memories=[])


@router.delete("/memory/{user_id}", response_model=MemoryDeleteResponse)
async def clear_memory(user_id: str) -> MemoryDeleteResponse:
    return MemoryDeleteResponse(user_id=user_id, cleared=True)
