from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    openrouter_site_url: str | None = None
    openrouter_app_name: str = "Agent Finance API"
    openrouter_max_tokens: int = Field(default=2048, ge=1, le=65536)
    backend_api_url: str = "http://127.0.0.1:3000"
    backend_timeout_seconds: float = Field(default=20, gt=0, le=120)
    # Mesmo valor do backend: autentica backend -> agente e agente -> backend.
    agent_shared_secret: SecretStr = SecretStr("")


def get_settings() -> Settings:
    return Settings()
