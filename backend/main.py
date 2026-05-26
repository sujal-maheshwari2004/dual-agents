from fastapi import FastAPI

from backend.config import get_settings
from backend.routers import chat, health, memory


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.include_router(chat.router)
    app.include_router(memory.router)
    app.include_router(health.router)

    @app.get("/", tags=["meta"])
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "environment": settings.environment,
            "status": "bootstrapped",
        }

    return app


app = create_app()
