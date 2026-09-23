from dataclasses import dataclass
from app.config import settings


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass(frozen=True)
class PricingResult:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    effective_input_tokens: int
    effective_output_tokens: int
    total_tokens: int
    input_cost_micros: int
    cached_input_cost_micros: int
    output_cost_micros: int
    reasoning_cost_micros: int
    api_call_cost_micros: int
    total_cost_micros: int
    cost_usd: str


class PricingEngine:
    """
    Calculates token usage and per-call charges using integer micro-units.
    1 USD = 1,000,000 micros.
    """

    @staticmethod
    def calculate_cost(
        usage: TokenUsage,
        include_api_call: bool = True
    ) -> PricingResult:
        # Effective outputs: standard output + reasoning tokens
        effective_output_tokens = usage.output_tokens + usage.reasoning_tokens
        effective_input_tokens = usage.input_tokens + usage.cached_input_tokens
        total_tokens = effective_input_tokens + effective_output_tokens

        # Scaled integer math (scaled by 1,000 to keep fractional micro-units exact before truncation)
        # Price constants are defined per 1,000,000 tokens
        # nano_units = (tokens * price_per_1m * 1000) // 1_000_000
        input_micros = (usage.input_tokens * settings.price_standard_input_per_1m_micros) // 1_000_000
        cached_input_micros = (usage.cached_input_tokens * settings.price_cached_input_per_1m_micros) // 1_000_000
        output_micros = (usage.output_tokens * settings.price_output_per_1m_micros) // 1_000_000
        # Reasoning tokens are billed as output tokens:
        reasoning_micros = (usage.reasoning_tokens * settings.price_reasoning_per_1m_micros) // 1_000_000

        api_call_micros = settings.price_per_api_call_micros if include_api_call else 0

        total_micros = (
            input_micros
            + cached_input_micros
            + output_micros
            + reasoning_micros
            + api_call_micros
        )

        # Format USD string with 6 decimal places ($0.000000)
        dollars = total_micros // 1_000_000
        fractional_micros = total_micros % 1_000_000
        cost_usd = f"${dollars}.{fractional_micros:06d}"

        return PricingResult(
            input_tokens=usage.input_tokens,
            cached_input_tokens=usage.cached_input_tokens,
            output_tokens=usage.output_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            effective_input_tokens=effective_input_tokens,
            effective_output_tokens=effective_output_tokens,
            total_tokens=total_tokens,
            input_cost_micros=input_micros,
            cached_input_cost_micros=cached_input_micros,
            output_cost_micros=output_micros,
            reasoning_cost_micros=reasoning_micros,
            api_call_cost_micros=api_call_micros,
            total_cost_micros=total_micros,
            cost_usd=cost_usd,
        )

