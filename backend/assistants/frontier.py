import operator
from typing import Annotated, Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from backend.assistants.base import AssistantRunInput, AssistantRunResult, BaseAssistant
from backend.config import Settings
from backend.schemas import ToolCall
from backend.tools import get_langchain_tools


class FrontierAssistantState(MessagesState):
    reply: str
    tool_calls: list[ToolCall]
    tokens_used: Annotated[int, operator.add]


class FrontierAssistant(BaseAssistant):
    def __init__(self, settings: Settings) -> None:
        super().__init__(model_name=settings.openai_model)
        self._settings = settings
        self._tools = get_langchain_tools()
        self._llm = (
            ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0,
            )
            if settings.openai_api_key
            else None
        )
        self._llm_with_tools = self._llm.bind_tools(self._tools) if self._llm else None
        self._graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FrontierAssistantState)
        graph.add_node("call_model", self._call_model)
        graph.add_node("tools", ToolNode(self._tools))
        graph.add_edge(START, "call_model")
        graph.add_conditional_edges("call_model", tools_condition)
        graph.add_edge("tools", "call_model")
        return graph.compile()

    async def _call_model(self, state: FrontierAssistantState) -> dict[str, Any]:
        if self._llm_with_tools is None:
            reply = (
                "Frontier assistant wiring now runs through LangGraph, "
                "but OPENAI_API_KEY is not configured yet."
            )
            return {
                "messages": [AIMessage(content=reply)],
                "reply": reply,
                "tool_calls": [],
                "tokens_used": 0,
            }

        response = await self._llm_with_tools.ainvoke(state["messages"])
        usage_metadata = getattr(response, "usage_metadata", {}) or {}
        return {
            "messages": [response],
            "reply": self.coerce_content(response.content),
            "tool_calls": [],
            "tokens_used": int(usage_metadata.get("total_tokens", 0) or 0),
        }

    def _extract_tool_calls(self, messages: list[BaseMessage]) -> list[ToolCall]:
        tool_outputs: dict[str, Any] = {}
        for message in messages:
            if isinstance(message, ToolMessage):
                tool_outputs[message.tool_call_id] = self.coerce_content(message.content)

        calls: list[ToolCall] = []
        for message in messages:
            if not isinstance(message, AIMessage):
                continue

            for tool_call in getattr(message, "tool_calls", []) or []:
                tool_call_id = tool_call.get("id", "")
                calls.append(
                    ToolCall(
                        name=tool_call.get("name", "unknown_tool"),
                        input=tool_call.get("args", {}) or {},
                        output=tool_outputs.get(tool_call_id),
                    )
                )
        return calls

    async def generate_reply(self, request: AssistantRunInput) -> AssistantRunResult:
        state = await self._graph.ainvoke(
            {
                "messages": self.build_messages(request),
                "reply": "",
                "tool_calls": [],
                "tokens_used": 0,
            }
        )
        return AssistantRunResult(
            reply=state["reply"],
            tool_calls=self._extract_tool_calls(state["messages"]),
            tokens_used=state["tokens_used"],
            model_name=self.model_name,
        )
