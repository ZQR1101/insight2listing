"""Application settings.

Configuration is read from the environment and a local ``.env`` file via
pydantic-settings. Model API keys are handled here (backend only) and must
never be exposed to the browser or written to logs (see plan section 18).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

#: Directory two levels above this file: apps/api/
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_PROJECT_ROOT / ".env", extra="ignore")

    app_name: str = "insight2listing-api"
    app_env: str = "development"
    app_locale: str = "zh-CN"

    # Backend-only secrets. Never render these into responses or logs.
    openai_api_key: str = ""
    openai_text_model: str = ""
    openai_image_model: str = "gpt-image-2"

    database_url: str = (
        "postgresql+psycopg://insight2listing:insight2listing@localhost:5432/insight2listing"
    )
    redis_url: str = "redis://localhost:6379/0"

    object_storage_endpoint: str = "http://localhost:9000"
    object_storage_bucket: str = "insight2listing"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""

    amazon_sp_api_enabled: bool = False
    amazon_marketplace_id: str = "ATVPDKIKX0DER"

    # Import guardrails (plan section 18.4).
    max_upload_bytes: int = 25 * 1024 * 1024
    #: Allow a deterministic message when a raw secret would otherwise leak.
    secret_redaction: str = "[REDACTED]"

    def redact(self, value: str) -> str:
        """Return a redacted placeholder for a secret value (e.g. for logging)."""
        return self.secret_redaction if value else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
