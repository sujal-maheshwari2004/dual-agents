from time import perf_counter

from fastapi import APIRouter

from backend.assistants import AssistantRunInput, get_assistant
from backend.guardrails import check_input, check_output
from backend.memory import extract_memory_candidates, get_long_term_memory, get_short_term_memory
from backend.observability import record_chat_metrics, trace_assistant_call
from backend.schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def create_chat_completion(payload: ChatRequest) -> ChatResponse:
    started_at = perf_counter()
    input_guard = check_input(payload.message, payload.model)
    if input_guard.blocked:
        latency_ms = int((perf_counter() - started_at) * 1000)
        short_term_memory = get_short_term_memory()
        record_chat_metrics(
            model=payload.model.value,
            latency_ms=latency_ms,
            outcome="blocked",
            tokens_used=0,
            tool_calls=[],
            guardrail_flags=input_guard.flags,
            active_sessions=short_term_memory.active_session_count(),
            memory_writes=0,
        )
        return ChatResponse(
            reply=input_guard.safe_reply or "I can't help with that request.",
            tool_calls=[],
            model=payload.model.value,
            latency_ms=latency_ms,
            tokens_used=0,
            guardrail_flags=input_guard.flags,
        )

    short_term_memory = get_short_term_memory()
    long_term_memory = get_long_term_memory()
    prior_turns = short_term_memory.get_history(payload.session_id)
    remembered_context = await long_term_memory.get_recent(payload.user_id)
    assistant = get_assistant(payload.model)
    run_input = AssistantRunInput(
        session_id=payload.session_id,
        user_id=payload.user_id,
        message=payload.message,
        history=prior_turns,
        long_term_memory=remembered_context,
    )

    result = await trace_assistant_call(
        assistant=assistant,
        request=run_input,
        requested_model=payload.model.value,
    )
    output_guard = check_output(result.reply)
    latency_ms = int((perf_counter() - started_at) * 1000)

    short_term_memory.append_turn(
        session_id=payload.session_id,
        user_message=payload.message,
        assistant_reply=output_guard.reply,
    )
    memory_writes = 0
    for key, value in extract_memory_candidates(payload.message):
        if await long_term_memory.save_memory(payload.user_id, key, value):
            memory_writes += 1

    guardrail_flags = input_guard.flags + output_guard.flags
    outcome = "flagged" if guardrail_flags else "success"
    record_chat_metrics(
        model=payload.model.value,
        latency_ms=latency_ms,
        outcome=outcome,
        tokens_used=result.tokens_used,
        tool_calls=result.tool_calls,
        guardrail_flags=guardrail_flags,
        active_sessions=short_term_memory.active_session_count(),
        memory_writes=memory_writes,
    )

    return ChatResponse(
        reply=output_guard.reply,
        tool_calls=result.tool_calls,
        model=result.model_name,
        latency_ms=latency_ms,
        tokens_used=result.tokens_used,
        guardrail_flags=guardrail_flags,
    )
