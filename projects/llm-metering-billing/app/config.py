from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    base_url: str = Field(default="http://localhost:8000", alias="BASE_URL")
    database_url: str = Field(default="sqlite:///./billing.db", alias="DATABASE_URL")

    # Stripe Configuration (Test Mode Only)
    stripe_secret_key: str = Field(default="sk_test_placeholder", alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="whsec_placeholder", alias="STRIPE_WEBHOOK_SECRET")

    # Pricing Constants in integer micro-units (1 USD = 1,000,000 micro-units, 1 cent = 10,000 micro-units)
    price_standard_input_per_1m_micros: int = Field(default=2_500_000, alias="PRICE_STANDARD_INPUT_PER_1M_MICROS")
    price_cached_input_per_1m_micros: int = Field(default=625_000, alias="PRICE_CACHED_INPUT_PER_1M_MICROS")
    price_output_per_1m_micros: int = Field(default=10_000_000, alias="PRICE_OUTPUT_PER_1M_MICROS")
    price_reasoning_per_1m_micros: int = Field(default=10_000_000, alias="PRICE_REASONING_PER_1M_MICROS")
    price_per_api_call_micros: int = Field(default=500, alias="PRICE_PER_API_CALL_MICROS")

    # Plan definitions
    free_plan_api_limit: int = 1_000
    free_plan_token_limit: int = 100_000
    free_plan_price_cents: int = 0

    pro_plan_api_limit: int = 50_000
    pro_plan_token_limit: int = 10_000_000
    pro_plan_price_cents: int = 2_900  # $29.00 / month

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

