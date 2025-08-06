# backend/api/services/valuation_graham.py

def calculate_graham_valuation(
    eps: float,
    growth_rate: float = 0.12  # 12% default growth
) -> dict:
    """
    Graham formula: Intrinsic Value = EPS * (8.5 + 2 * growth rate)
    """
    intrinsic_value = eps * (8.5 + 2 * (growth_rate * 100))  # convert growth to %
    explanation = (
        f"Graham valuation is based on EPS={eps}, "
        f"and an estimated growth rate of {growth_rate * 100:.1f}%."
    )

    return {
        "fair_value": round(intrinsic_value, 2),
        "eps": eps,
        "growth_rate": growth_rate,
        "explanation": explanation
    }