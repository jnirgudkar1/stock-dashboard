from typing import Optional
from math import pow

def calculate_dcf(
    free_cash_flow: float,
    growth_rate: float,
    discount_rate: float,
    years: int = 5,
    terminal_growth_rate: float = 0.02
) -> dict:
    """
    Calculate the intrinsic value using a simplified DCF model.
    """
    discounted_cash_flows = []
    for year in range(1, years + 1):
        projected_fcf = free_cash_flow * pow((1 + growth_rate), year)
        discounted_fcf = projected_fcf / pow((1 + discount_rate), year)
        discounted_cash_flows.append(discounted_fcf)

    terminal_value = (free_cash_flow * pow(1 + growth_rate, years) * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
    discounted_terminal_value = terminal_value / pow(1 + discount_rate, years)

    intrinsic_value = sum(discounted_cash_flows) + discounted_terminal_value

    explanation = (
        f"This estimate is based on a {years}-year cash flow forecast with a {growth_rate*100:.1f}% annual growth rate, "
        f"{discount_rate*100:.1f}% discount rate, and {terminal_growth_rate*100:.1f}% terminal growth."
    )

    return {
        "fair_value": round(intrinsic_value, 2),
        "details": {
            "yearly_cash_flows": [round(v, 2) for v in discounted_cash_flows],
            "terminal_value": round(discounted_terminal_value, 2)
        },
        "explanation": explanation
    }

def get_dcf_valuation(
    symbol: str,
    current_price: float,
    market_cap: float,
    default_fcf_ratio: float = 0.05,
    growth_rate: float = 0.12,
    discount_rate: float = 0.10
) -> dict:
    """
    Estimate fair value using a simplified model and assumptions.
    """
    # Estimate free cash flow as a percentage of market cap
    free_cash_flow = market_cap * default_fcf_ratio

    dcf_result = calculate_dcf(
        free_cash_flow=free_cash_flow,
        growth_rate=growth_rate,
        discount_rate=discount_rate
    )

    dcf_result["is_undervalued"] = dcf_result["fair_value"] > current_price
    dcf_result["current_price"] = round(current_price, 2)
    dcf_result["symbol"] = symbol

    return dcf_result