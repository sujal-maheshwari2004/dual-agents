from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from backend.memory import ConversationTurn
from backend.schemas import MemoryRecord, ToolCall


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful personal assistant. "
    "Use the provided conversation history when it is relevant, "
    "answer honestly, and avoid inventing facts."
)


@dataclass(slots=True)
class AssistantRunInput:
    session_id: str
    user_id: str
    message: str
    history: Sequence[ConversationTurn]
    long_term_memory: Sequence[MemoryRecord] = ()


@dataclass(slots=True)
class AssistantRunResult:
    reply: str
    tool_calls: list[ToolCall]
    tokens_used: int
    model_name: str


class BaseAssistant(ABC):
    def __init__(self, model_name: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        self.model_name = model_name
        self.system_prompt = system_prompt

    def build_messages(self, request: AssistantRunInput) -> list[BaseMessage]:
        system_prompt = self.system_prompt
        if request.long_term_memory:
            memory_lines = [
                f"- {memory.key}: {memory.value}" for memory in request.long_term_memory
            ]
            system_prompt = (
                f"{system_prompt}\n\nRelevant long-term user memory:\n"
                + "\n".join(memory_lines)
            )

        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        for turn in request.history:
            messages.append(HumanMessage(content=turn.user_message))
            messages.append(AIMessage(content=turn.assistant_reply))
        messages.append(HumanMessage(content=request.message))
        return messages

    @staticmethod
    def coerce_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(part for part in parts if part).strip()
        return str(content)

    @abstractmethod
    async def generate_reply(self, request: AssistantRunInput) -> AssistantRunResult:
        raise NotImplementedError
