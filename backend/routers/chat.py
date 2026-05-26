from fastapi import APIRouter

from backend.memory import get_short_term_memory
from backend.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def create_chat_completion(payload: ChatRequest) -> ChatResponse:
    memory = get_short_term_memory()
    prior_turns = memory.get_history(payload.session_id)

    # Stubbed response until assistant orchestration is wired in.
    reply = (
        f"{payload.model.value} assistant is bootstrapped. "
        f"I can see {len(prior_turns)} prior turn(s) in this session, "
        "and full orchestration will be added in the next slice."
    )

    memory.append_turn(
        session_id=payload.session_id,
        user_message=payload.message,
        assistant_reply=reply,
    )

    return ChatResponse(
        reply=reply,
        tool_calls=[],
        model=payload.model.value,
        latency_ms=0,
        tokens_used=0,
    )
