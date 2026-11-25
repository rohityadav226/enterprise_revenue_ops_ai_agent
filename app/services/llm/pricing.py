from decimal import Decimal


# OpenAI Standard API pricing per 1 million tokens.
# Verify rates against the provider pricing page when updating models.

MODEL_PRICING_USD_PER_1M = {
    "gpt-6.2-sol": {
        "input": Decimal("2.00"),
        "cached_input": Decimal("0.10"),
        "output": Decimal("10.00"),
    }
}

def calculate_estimated_cost(
        model: str,
        input_tokens: int,
        cached_input_tokens: int,
        output_tokens: int,
) -> Decimal | None:
    
    pricing = MODEL_PRICING_USD_PER_1M.get(model)

    # Do not invent a cost for an unconfigured model.
    if pricing is None:
        return None

    cached_input_tokens = min(
        cached_input_tokens,
        input_tokens,
    )

    uncached_input_tokens = (
        input_tokens - cached_input_tokens
    )

    total_cost = (
        Decimal(uncached_input_tokens)
        * pricing["input"]
        +
        Decimal(cached_input_tokens)
        * pricing["cached_input"]
        +
        Decimal(output_tokens)
        * pricing["output"]
    ) / Decimal("1000000")

    return total_cost.quantize(
        Decimal("0.00000001")
    )