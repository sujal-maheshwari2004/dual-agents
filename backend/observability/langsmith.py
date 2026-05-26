import hashlib
import os
from typing import Any

from backend.assistants.base import AssistantRunInput, AssistantRunResult, BaseAssistant
from backend.config import Settings, get_settings


try:
    from langsmith import traceable
    from langsmith.run_helpers import tracing_context
except ModuleNotFoundError:
    traceable = None
    tracing_context = None


def configure_langsmith(settings: Settings) -> None:
    if not settings.langchain_api_key:
        return

    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langchain_api_key)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langchain_project)
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")


async def trace_assistant_call(
    *,
    assistant: BaseAssistant,
    request: AssistantRunInput,
    requested_model: str,
) -> AssistantRunResult:
    settings = get_settings()
    if traceable is None or tracing_context is None or not settings.langchain_api_key:
        return await assistant.generate_reply(request)

    metadata = {
        "requested_model": requested_model,
        "provider_model": assistant.model_name,
        "session_id": request.session_id,
        "user_hash": _stable_hash(request.user_id),
        "history_turns": len(request.history),
        "long_term_memory_count": len(request.long_term_memory),
    }

    with tracing_context(
        enabled=True,
        project_name=settings.langchain_project,
        tags=["chat", requested_model],
        metadata=metadata,
    ):
        return await _traced_generate_reply(
            assistant,
            request,
            requested_model,
            langsmith_extra={
                "metadata": metadata,
                "tags": ["assistant", requested_model],
                "project_name": settings.langchain_project,
            },
        )


if traceable is not None:

    @traceable(
        name="assistant.generate_reply",
        run_type="llm",
        process_inputs=lambda inputs: _process_trace_inputs(inputs),
        process_outputs=lambda output: _process_trace_outputs(output),
    )
    async def _traced_generate_reply(
        assistant: BaseAssistant,
        request: AssistantRunInput,
        requested_model: str,
    ) -> AssistantRunResult:
        return await assistant.generate_reply(request)

else:

    async def _traced_generate_reply(
        assistant: BaseAssistant,
        request: AssistantRunInput,
        requested_model: str,
    ) -> AssistantRunResult:
        return await assistant.generate_reply(request)


def _process_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    request = inputs.get("request")
    assistant = inputs.get("assistant")
    requested_model = inputs.get("requested_model")
    if not isinstance(request, AssistantRunInput):
        return inputs

    return {
        "requested_model": requested_model,
        "provider_model": getattr(assistant, "model_name", None),
        "session_id": request.session_id,
        "user_hash": _stable_hash(request.user_id),
        "message": request.message,
        "history_turns": len(request.history),
        "long_term_memory": [
            {"key": memory.key, "value": memory.value, "source": memory.source}
            for memory in request.long_term_memory
        ],
    }


def _process_trace_outputs(output: AssistantRunResult) -> dict[str, Any]:
    return {
        "reply": output.reply,
        "model_name": output.model_name,
        "tokens_used": output.tokens_used,
        "tool_calls": [tool_call.model_dump() for tool_call in output.tool_calls],
    }


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
