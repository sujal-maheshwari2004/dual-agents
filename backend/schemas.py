from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AssistantModel(StrEnum):
    OSS = "oss"
    FRONTIER = "frontier"


class ToolCall(BaseModel):
    name: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: Any | None = None


class GuardrailFlag(BaseModel):
    source: str
    code: str
    message: str
    severity: str = "warning"
    blocked: bool = False


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    model: AssistantModel
    user_id: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model: str
    latency_ms: int = Field(ge=0)
    tokens_used: int = Field(ge=0)
    guardrail_flags: list[GuardrailFlag] = Field(default_factory=list)


class MemoryRecord(BaseModel):
    key: str
    value: str
    source: str = "long_term"


class MemoryResponse(BaseModel):
    user_id: str
    memories: list[MemoryRecord] = Field(default_factory=list)


class MemoryDeleteResponse(BaseModel):
    user_id: str
    cleared: bool


class HealthResponse(BaseModel):
    status: str
    environment: str
    uptime_seconds: float = Field(ge=0)
    model_availability: dict[str, bool]
