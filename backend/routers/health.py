from time import monotonic

from fastapi import APIRouter

from backend.config import get_settings
from backend.schemas import HealthResponse

router = APIRouter(tags=["health"])
START_TIME = monotonic()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        uptime_seconds=round(monotonic() - START_TIME, 3),
        model_availability={
            "oss": bool(settings.hf_token),
            "frontier": bool(settings.openai_api_key),
        },
    )
