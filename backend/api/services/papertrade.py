# backend/api/services/papertrade.py
from __future__ import annotations
import math, time
from typing import Optional, Dict, Any

from .valuation import predict_direction, score_valuation
from .prices import get_prices

DEFAULT_BUDGET = 1000.0
DEFAULT_HORIZON_DAYS = 7

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))

def _relu(x: float) -> float:
    return x if x > 0 else 0.0

def _last_close(prices_payload: Dict[str, Any]) -> Optional[float]:
    bars = (prices_payload or {}).get("prices") or []
    if not bars:
        return None
    last = bars[-1]
    for key in ("close", "c", "Close"):
        if key in last:
            try:
                return float(last[key])
            except Exception:
                pass
    return None

def suggest_trade(
    symbol: str,
    *,
    budget: float = DEFAULT_BUDGET,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    temp: Optional[float] = None,
    w_pred: float = 0.6,
    w_val: float = 0.4,
    min_trigger: float = 0.15,   # require ~15% blended conviction to place trade
    min_shares: int = 1,
) -> Dict[str, Any]:
    """
    Long-only V1 paper trade sizing based on prediction + valuation.
    Returns a structured suggestion; caller may persist it.
    """
    symbol = symbol.upper()

    # Get model & valuation
    pred = predict_direction(symbol, temp=temp)
    val  = score_valuation(symbol)

    prob_up = float(pred.get("prob_up", 0.5))
    conf    = float(pred.get("confidence", abs(prob_up - 0.5) * 2))

    # Convert to 0..1 long-conviction
    pred_conv = _relu((prob_up - 0.5) * 2.0)  # 0..1

    total_score = float(val.get("total_score", 0.5))
    val_conv = _clamp((total_score - 0.5) * 2.0, -1.0, 1.0)
    val_conv = _relu(val_conv)  # long-only

    blended = _clamp(w_pred * pred_conv + w_val * val_conv, 0.0, 1.0)

    # Price for sizing
    pxs = get_prices(symbol, interval="1day", limit=2)
    last_price = _last_close(pxs)
    if last_price is None or last_price <= 0:
        raise RuntimeError("No valid price to size position.")

    action = "BUY" if blended >= min_trigger else "SKIP"
    shares = 0
    notional = 0.0
    if action == "BUY":
        raw = (budget * blended) / last_price
        shares = max(min_shares, int(math.floor(raw)))
        if shares < 1:
            action = "SKIP"
        else:
            notional = round(shares * last_price, 2)

    now = int(time.time())
    return {
        "symbol": symbol,
        "action": action,
        "shares": shares,
        "entry_price": round(last_price, 4) if last_price else None,
        "notional": notional,
        "horizon_days": int(horizon_days),
        "timestamp": now,
        "rationale": {
            "blended": round(blended, 4),
            "weights": {"w_pred": w_pred, "w_val": w_val},
            "prediction": {
                "prob_up": round(prob_up, 4),
                "confidence": round(conf, 4),
                "label": pred.get("label"),
                "mode": pred.get("mode"),
                "top_features": pred.get("top_features"),
                "calibration": pred.get("calibration"),
            },
            "valuation": {
                "total_score": round(total_score, 4),
                "verdict": val.get("verdict"),
                "explain": val.get("explain"),
            },
        },
        "inputs": {
            "budget": float(budget),
            "temp": float(temp) if temp is not None else None,
        },
        "provider": pxs.get("provider"),
        "prices_meta": {"interval": pxs.get("interval")},
        "status": "OPEN" if action == "BUY" else "SKIPPED",
    }