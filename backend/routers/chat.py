from time import perf_counter

from fastapi import APIRouter

from backend.assistants import AssistantRunInput, get_assistant
from backend.memory import extract_memory_candidates, get_long_term_memory, get_short_term_memory
from backend.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def create_chat_completion(payload: ChatRequest) -> ChatResponse:
    short_term_memory = get_short_term_memory()
    long_term_memory = get_long_term_memory()
    prior_turns = short_term_memory.get_history(payload.session_id)
    remembered_context = await long_term_memory.get_recent(payload.user_id)
    assistant = get_assistant(payload.model)

    started_at = perf_counter()
    result = await assistant.generate_reply(
        AssistantRunInput(
            session_id=payload.session_id,
            user_id=payload.user_id,
            message=payload.message,
            history=prior_turns,
            long_term_memory=remembered_context,
        )
    )
    latency_ms = int((perf_counter() - started_at) * 1000)

    short_term_memory.append_turn(
        session_id=payload.session_id,
        user_message=payload.message,
        assistant_reply=result.reply,
    )
    for key, value in extract_memory_candidates(payload.message):
        await long_term_memory.save_memory(payload.user_id, key, value)

    return ChatResponse(
        reply=result.reply,
        tool_calls=result.tool_calls,
        model=result.model_name,
        latency_ms=latency_ms,
        tokens_used=result.tokens_used,
    )
