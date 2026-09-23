from app.services.pricing_engine import PricingEngine, TokenUsage
from app.config import settings


def test_probe_5_pure_pricing_engine_rules():
    """Verify cached input discounts, reasoning tokens billed as output, and integer micro-units."""
    usage = TokenUsage(
        input_tokens=10_000,
        cached_input_tokens=4_000,
        output_tokens=2_000,
        reasoning_tokens=1_000,
    )
    result = PricingEngine.calculate_cost(usage=usage, include_api_call=True)

    assert result.effective_input_tokens == 14_000
    assert result.effective_output_tokens == 3_000
    assert result.total_tokens == 17_000

    expected_input_micros = (10_000 * settings.price_standard_input_per_1m_micros) // 1_000_000  # 25,000
    expected_cached_micros = (4_000 * settings.price_cached_input_per_1m_micros) // 1_000_000   # 2,500
    expected_output_micros = (2_000 * settings.price_output_per_1m_micros) // 1_000_000         # 20,000
    expected_reasoning_micros = (1_000 * settings.price_reasoning_per_1m_micros) // 1_000_000   # 10,000
    expected_api_call = settings.price_per_api_call_micros                                       # 500

    assert result.input_cost_micros == expected_input_micros == 25_000
    assert result.cached_input_cost_micros == expected_cached_micros == 2_500
    assert result.output_cost_micros == expected_output_micros == 20_000
    assert result.reasoning_cost_micros == expected_reasoning_micros == 10_000
    assert result.api_call_cost_micros == expected_api_call == 500

    assert (result.reasoning_cost_micros / usage.reasoning_tokens) == (result.output_cost_micros / usage.output_tokens)
    assert result.cached_input_cost_micros / usage.cached_input_tokens == 0.625
    assert result.input_cost_micros / usage.input_tokens == 2.5

    expected_total = 25_000 + 2_500 + 20_000 + 10_000 + 500
    assert result.total_cost_micros == expected_total == 58_000
    assert result.cost_usd == "$0.058000"


def test_probe_5_end_to_end_metering_and_usage_rollup_matches(client):
    """Verify /generate cost rolls up accurately in GET /usage."""
    tenant_id = "tenant_pro"
    payload = {
        "prompt": "Explain general relativity and quantum entanglement",
        "simulated_usage": {
            "input_tokens": 10_000,
            "cached_input_tokens": 4_000,
            "output_tokens": 2_000,
            "reasoning_tokens": 1_000
        }
    }
    headers = {"X-Tenant-ID": tenant_id}

    # Meter the request
    gen_res = client.post("/generate", json=payload, headers=headers)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["cost"]["micros"] == 58_000
    assert gen_data["cost"]["usd"] == "$0.058000"

    # Query GET /usage rollup
    usage_res = client.get("/usage", headers=headers)
    assert usage_res.status_code == 200
    rollup = usage_res.json()

    assert rollup["api_calls"]["used"] == 1
    assert rollup["tokens"]["used"] == 17_000
    assert rollup["tokens"]["breakdown"]["standard_input"] == 10_000
    assert rollup["tokens"]["breakdown"]["cached_input"] == 4_000
    assert rollup["tokens"]["breakdown"]["standard_output"] == 2_000
    assert rollup["tokens"]["breakdown"]["reasoning"] == 1_000
    assert rollup["cost"]["total_micros"] == 58_000
    assert rollup["cost"]["formatted_usd"] == "$0.058000"

