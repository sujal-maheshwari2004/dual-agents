from collections import defaultdict
from threading import RLock
from typing import Any

from fastapi import FastAPI, Response

from backend.schemas import GuardrailFlag, ToolCall


try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except ModuleNotFoundError:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    Counter = Gauge = Histogram = None
    generate_latest = None

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ModuleNotFoundError:
    Instrumentator = None


_fallback_lock = RLock()
_fallback_counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_fallback_gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_fallback_histograms: dict[tuple[str, tuple[tuple[str, str], ...]], dict[str, float]] = defaultdict(
    lambda: {"count": 0.0, "sum": 0.0}
)

if Counter and Gauge and Histogram:
    CHAT_REQUESTS = Counter(
        "dual_agents_chat_requests_total",
        "Total chat requests handled by the assistant backend.",
        ("model", "outcome"),
    )
    CHAT_LATENCY = Histogram(
        "dual_agents_chat_latency_seconds",
        "End-to-end chat request latency in seconds.",
        ("model",),
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
    )
    LLM_TOKENS = Counter(
        "dual_agents_llm_tokens_total",
        "Total LLM tokens reported by model providers.",
        ("model",),
    )
    TOOL_CALLS = Counter(
        "dual_agents_tool_calls_total",
        "Tool calls made by LangGraph assistants.",
        ("model", "tool"),
    )
    GUARDRAIL_FLAGS = Counter(
        "dual_agents_guardrail_flags_total",
        "Guardrail flags emitted by input and output checks.",
        ("source", "code", "blocked"),
    )
    MEMORY_WRITES = Counter(
        "dual_agents_memory_writes_total",
        "Long-term memory write attempts from chat requests.",
        ("model",),
    )
    OBSERVABILITY_READY = Gauge(
        "dual_agents_observability_ready",
        "Whether backend observability hooks are initialized.",
    )
    ACTIVE_SESSIONS = Gauge(
        "dual_agents_active_sessions",
        "Current in-process short-term memory sessions.",
    )
else:
    CHAT_REQUESTS = CHAT_LATENCY = LLM_TOKENS = TOOL_CALLS = None
    GUARDRAIL_FLAGS = MEMORY_WRITES = OBSERVABILITY_READY = ACTIVE_SESSIONS = None


def configure_metrics(app: FastAPI) -> None:
    if OBSERVABILITY_READY is not None:
        OBSERVABILITY_READY.set(1)
    else:
        _fallback_set("dual_agents_observability_ready", {}, 1)

    if Instrumentator is not None:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        return

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        if generate_latest is not None:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
        return Response(_render_fallback_metrics(), media_type=CONTENT_TYPE_LATEST)


def record_chat_metrics(
    *,
    model: str,
    latency_ms: int,
    outcome: str,
    tokens_used: int,
    tool_calls: list[ToolCall],
    guardrail_flags: list[GuardrailFlag],
    active_sessions: int,
    memory_writes: int,
) -> None:
    latency_seconds = latency_ms / 1000

    if Counter and Gauge and Histogram:
        CHAT_REQUESTS.labels(model=model, outcome=outcome).inc()
        CHAT_LATENCY.labels(model=model).observe(latency_seconds)
        LLM_TOKENS.labels(model=model).inc(tokens_used)
        ACTIVE_SESSIONS.set(active_sessions)
        if memory_writes:
            MEMORY_WRITES.labels(model=model).inc(memory_writes)
        for tool_call in tool_calls:
            TOOL_CALLS.labels(model=model, tool=tool_call.name).inc()
        for flag in guardrail_flags:
            GUARDRAIL_FLAGS.labels(
                source=flag.source,
                code=flag.code,
                blocked=str(flag.blocked).lower(),
            ).inc()
        return

    labels = {"model": model, "outcome": outcome}
    _fallback_inc("dual_agents_chat_requests_total", labels)
    _fallback_observe("dual_agents_chat_latency_seconds", {"model": model}, latency_seconds)
    _fallback_inc("dual_agents_llm_tokens_total", {"model": model}, tokens_used)
    _fallback_set("dual_agents_active_sessions", {}, active_sessions)
    if memory_writes:
        _fallback_inc("dual_agents_memory_writes_total", {"model": model}, memory_writes)
    for tool_call in tool_calls:
        _fallback_inc("dual_agents_tool_calls_total", {"model": model, "tool": tool_call.name})
    for flag in guardrail_flags:
        _fallback_inc(
            "dual_agents_guardrail_flags_total",
            {
                "source": flag.source,
                "code": flag.code,
                "blocked": str(flag.blocked).lower(),
            },
        )


def _fallback_inc(name: str, labels: dict[str, str], amount: float = 1.0) -> None:
    with _fallback_lock:
        _fallback_counters[_metric_key(name, labels)] += amount


def _fallback_set(name: str, labels: dict[str, str], value: float) -> None:
    with _fallback_lock:
        _fallback_gauges[_metric_key(name, labels)] = value


def _fallback_observe(name: str, labels: dict[str, str], value: float) -> None:
    with _fallback_lock:
        metric = _fallback_histograms[_metric_key(name, labels)]
        metric["count"] += 1
        metric["sum"] += value


def _metric_key(name: str, labels: dict[str, str]) -> tuple[str, tuple[tuple[str, str], ...]]:
    return name, tuple(sorted((key, str(value)) for key, value in labels.items()))


def _render_fallback_metrics() -> str:
    lines: list[str] = []
    with _fallback_lock:
        for (name, labels), value in sorted(_fallback_counters.items()):
            lines.append(f"{name}{_format_labels(labels)} {value:g}")
        for (name, labels), value in sorted(_fallback_gauges.items()):
            lines.append(f"{name}{_format_labels(labels)} {value:g}")
        for (name, labels), values in sorted(_fallback_histograms.items()):
            lines.append(f"{name}_count{_format_labels(labels)} {values['count']:g}")
            lines.append(f"{name}_sum{_format_labels(labels)} {values['sum']:g}")
    return "\n".join(lines) + "\n"


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    rendered = ",".join(f'{key}="{_escape_label(value)}"' for key, value in labels)
    return f"{{{rendered}}}"


def _escape_label(value: Any) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
