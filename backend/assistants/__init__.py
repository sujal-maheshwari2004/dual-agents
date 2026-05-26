"""Assistant implementations."""

from functools import lru_cache

from backend.assistants.base import AssistantRunInput, AssistantRunResult, BaseAssistant
from backend.assistants.frontier import FrontierAssistant
from backend.assistants.oss import OssAssistant
from backend.config import get_settings
from backend.schemas import AssistantModel


@lru_cache
def _assistant_registry() -> dict[AssistantModel, BaseAssistant]:
    settings = get_settings()
    return {
        AssistantModel.FRONTIER: FrontierAssistant(settings),
        AssistantModel.OSS: OssAssistant(settings),
    }


def get_assistant(model: AssistantModel) -> BaseAssistant:
    return _assistant_registry()[model]


__all__ = [
    "AssistantRunInput",
    "AssistantRunResult",
    "BaseAssistant",
    "FrontierAssistant",
    "OssAssistant",
    "get_assistant",
]
