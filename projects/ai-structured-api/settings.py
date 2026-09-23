"""Runtime settings from env. No secrets hardcoded."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_enabled: bool = True
    mock_llm: bool = True

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    llm_timeout_seconds: float = 20.0
    llm_max_retries: int = 2

    cost_log_path: str = "logs/cost.jsonl"

    # Rough gpt-4o-mini-ish estimates (USD per 1M tokens)
    cost_per_1m_input: float = 0.15
    cost_per_1m_output: float = 0.60


@lru_cache
def get_settings() -> Settings:
    return Settings()
