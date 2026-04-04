"""Server configuration via environment variables."""

from __future__ import annotations

import json

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
from pydantic_settings.sources.providers.dotenv import DotEnvSettingsSource
from pydantic_settings.sources.providers.env import EnvSettingsSource


def _comma_sep_decode(field_name: str, field: FieldInfo, value: str) -> object:
    """Parse value as JSON first, fall back to comma-separated for list fields."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        origin = getattr(field.annotation, "__origin__", None)
        if origin is list:
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


class _CommaSepEnvSource(EnvSettingsSource):
    """Env source that falls back to comma-separated parsing for list fields."""

    def decode_complex_value(self, field_name: str, field: FieldInfo, value: str) -> object:
        return _comma_sep_decode(field_name, field, value)


class _CommaSepDotEnvSource(DotEnvSettingsSource):
    """DotEnv source that falls back to comma-separated parsing for list fields."""

    def decode_complex_value(self, field_name: str, field: FieldInfo, value: str) -> object:
        return _comma_sep_decode(field_name, field, value)


class ServerConfig(BaseSettings):
    """Configuration loaded from environment variables or .env file."""

    bigquery_project: str
    bigquery_datasets: list[str]
    google_application_credentials: str | None = None
    bigquery_max_bytes: int = 1_073_741_824  # 1 GB
    cache_ttl_seconds: int = 3600
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            _CommaSepEnvSource(settings_cls),
            _CommaSepDotEnvSource(settings_cls, env_file=".env", env_file_encoding="utf-8"),
            file_secret_settings,
        )
