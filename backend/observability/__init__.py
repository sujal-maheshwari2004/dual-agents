"""Observability integrations for traces and metrics."""

from fastapi import FastAPI

from backend.config import get_settings
from backend.observability.langsmith import configure_langsmith, trace_assistant_call
from backend.observability.metrics import configure_metrics, record_chat_metrics


def configure_observability(app: FastAPI) -> None:
    settings = get_settings()
    configure_langsmith(settings)
    configure_metrics(app)


__all__ = [
    "configure_langsmith",
    "configure_metrics",
    "configure_observability",
    "record_chat_metrics",
    "trace_assistant_call",
]
