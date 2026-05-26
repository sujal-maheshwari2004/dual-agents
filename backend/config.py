from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = Field(default="Dual AI Personal Assistant", validation_alias="APP_NAME")
    environment: str = Field(default="local", validation_alias="ENVIRONMENT")
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")
    mongodb_uri: str | None = Field(default=None, validation_alias="MONGODB_URI")
    azure_translator_key: str | None = Field(
        default=None,
        validation_alias="AZURE_TRANSLATOR_KEY",
    )
    azure_translator_region: str | None = Field(
        default=None,
        validation_alias="AZURE_TRANSLATOR_REGION",
    )
    langchain_api_key: str | None = Field(default=None, validation_alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(
        default="dual-agents",
        validation_alias="LANGCHAIN_PROJECT",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_local(self) -> bool:
        return self.environment.lower() == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
