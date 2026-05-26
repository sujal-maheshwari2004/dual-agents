from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from openai import AsyncOpenAI, OpenAIError

from backend.assistants.base import AssistantRunInput, AssistantRunResult, BaseAssistant
from backend.config import Settings


class OssAssistantState(MessagesState):
    reply: str
    tokens_used: int


class OssAssistant(BaseAssistant):
    def __init__(self, settings: Settings) -> None:
        super().__init__(model_name=settings.hf_model_id)
        self._settings = settings
        self._client = (
            AsyncOpenAI(
                api_key=settings.hf_token,
                base_url=settings.hf_base_url,
            )
            if settings.hf_token
            else None
        )
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(OssAssistantState)
        graph.add_node("draft_response", self._draft_response)
        graph.add_edge(START, "draft_response")
        graph.add_edge("draft_response", END)
        return graph.compile()

    async def _draft_response(self, state: OssAssistantState) -> dict[str, Any]:
        if self._client is None:
            reply = (
                "OSS assistant wiring now runs through LangGraph, "
                "but HF_TOKEN is not configured yet."
            )
            return {
                "messages": [AIMessage(content=reply)],
                "reply": reply,
                "tokens_used": 0,
            }

        try:
            completion = await self._client.chat.completions.create(
                model=self._settings.hf_model_id,
                messages=self._to_openai_messages(state["messages"]),
                temperature=0.2,
                max_tokens=512,
            )
        except OpenAIError as exc:
            reply = f"OSS assistant request failed: {exc}"
            return {
                "messages": [AIMessage(content=reply)],
                "reply": reply,
                "tokens_used": 0,
            }

        message = completion.choices[0].message
        reply = message.content or ""
        usage = completion.usage
        return {
            "messages": [AIMessage(content=reply)],
            "reply": reply,
            "tokens_used": int(usage.total_tokens if usage else 0),
        }

    def _to_openai_messages(self, messages: list[BaseMessage]) -> list[dict[str, str]]:
        converted: list[dict[str, str]] = []
        for message in messages:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                continue

            content = self.coerce_content(message.content)
            if content:
                converted.append({"role": role, "content": content})
        return converted

    async def generate_reply(self, request: AssistantRunInput) -> AssistantRunResult:
        state = await self._graph.ainvoke(
            {
                "messages": self.build_messages(request),
                "reply": "",
                "tokens_used": 0,
            }
        )
        return AssistantRunResult(
            reply=state["reply"],
            tool_calls=[],
            tokens_used=state["tokens_used"],
            model_name=self.model_name,
        )
