from __future__ import annotations

import os
import time
import typing as t
from dataclasses import dataclass

# ---- Path resolution (repo root -> training_pipeline/models/...) ----
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "training_pipeline", "models", "price_direction_model.pkl")
MODEL_PATH = os.getenv("PREDICT_MODEL_PATH", DEFAULT_MODEL_PATH)

# Default calibration temperature; UI can override per-request via ?temp=
PREDICT_TEMP = float(os.getenv("PREDICT_TEMP", "1.0"))

# ---- Optional sklearn imports (graceful fallback) ----
try:
    import joblib  # type: ignore
except Exception:
    joblib = None

try:
    from sklearn.linear_model import LogisticRegression  # type: ignore
except Exception:
    LogisticRegression = None  # type: ignore

# ---- Services used (in-memory) ----
from .metadata_services import get_metadata
from .prices import get_prices
from .features import get_features  # technical + news features

# --------------------------------------------------------------------------------------
# Model loading wrapper
# --------------------------------------------------------------------------------------
@dataclass
class ModelWrapper:
    model: t.Any | None = None
    loaded_at: float | None = None
    n_features_in_: int | None = None

    def load(self):
        if joblib is not None and os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.loaded_at = time.time()
                self.n_features_in_ = getattr(self.model, "n_features_in_", None)
                return
            except Exception:
                pass
        # Fallback tiny model (if sklearn available); otherwise dummy probabilities
        if LogisticRegression is not None:
            import numpy as np  # type: ignore
            X = np.array([
                [1.0, 0.0, 0.0, 0.0],
                [0.8, 0.2, 0.0, 0.0],
                [0.0, 0.5, 0.8, 0.0],
                [0.0, 0.0, 0.2, 1.0],
            ])
            y = np.array([1, 1, 0, 0])
            m = LogisticRegression(max_iter=200)
            m.fit(X, y)
            self.model = m
            self.loaded_at = time.time()
            self.n_features_in_ = getattr(self.model, "n_features_in_", 4)
        else:
            self.model = None
            self.loaded_at = time.time()
            self.n_features_in_ = None

_wrap = ModelWrapper()
_wrap.load()

# --------------------------------------------------------------------------------------
# Feature pipelines
# --------------------------------------------------------------------------------------
TECH_FEATURE_ORDER = [
    "return_1d",
    "volatility_21d",
    "rsi_14",
    "macd_hist",
    "bb_percent_b",
    "volume_zscore_20",
    "news_sent_mean_24h",
    "news_sent_mean_7d",
]

LEGACY_FEATURE_ORDER = [
    "close_price",
    "pe_ratio",
    "eps",
    "revenue_growth",
]

def _safe_float(x: t.Any, default: float = 0.0) -> float:
    try:
        if x is None: return default
        return float(x)
    except Exception:
        return default

def _build_legacy_features(symbol: str) -> tuple[dict, list[str]]:
    symbol = symbol.upper()
    price_payload = get_prices(symbol, interval="1day", limit=2) or {}
    prices = price_payload.get("prices", [])
    close_price = prices[-1]["close"] if prices else None
    meta = get_metadata(symbol) or {}
    pe = meta.get("peRatio")
    eps = meta.get("eps")
    growth = 0.0
    feats = {
        "close_price": _safe_float(close_price),
        "pe_ratio": _safe_float(pe),
        "eps": _safe_float(eps),
        "revenue_growth": _safe_float(growth),
    }
    return feats, LEGACY_FEATURE_ORDER

def _build_tech_features(symbol: str) -> tuple[dict, list[str]]:
    payload = get_features(symbol, interval="1day", limit=240, max_news=50) or {}
    feats = payload.get("features", {}) if isinstance(payload, dict) else {}
    out = {k: _safe_float(feats.get(k)) for k in TECH_FEATURE_ORDER}
    return out, TECH_FEATURE_ORDER

# --------------------------------------------------------------------------------------
# Calibration + diagnostics
# --------------------------------------------------------------------------------------
def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    import math
    return math.log(p / (1 - p))

def _sigmoid(x: float) -> float:
    import math
    return 1.0 / (1.0 + math.exp(-x))

def _calibrate(p: float, temperature: float) -> float:
    try:
        if temperature and abs(float(temperature) - 1.0) > 1e-6:
            return _sigmoid(_logit(p) / float(temperature))
    except Exception:
        pass
    return p

def _confidence(prob_up: float) -> float:
    return round(abs(prob_up - 0.5) * 2.0, 4)

def _top_features(model: t.Any, x_vec: list[float], order: list[str], top_k: int = 5) -> list[dict]:
    contribs: list[tuple[str, float, float]] = []
    coef = getattr(model, "coef_", None)
    if coef is not None:
        try:
            row = coef[0]
            for name, val, w in zip(order, x_vec, row):
                contribs.append((name, float(w), float(w) * float(val)))
        except Exception:
            contribs = []
    if not contribs:
        fi = getattr(model, "feature_importances_", None)
        if fi is not None:
            try:
                for name, val, imp in zip(order, x_vec, fi):
                    contribs.append((name, float(imp), float(imp) * abs(float(val))))
            except Exception:
                contribs = []
    if not contribs:
        for name, val in zip(order, x_vec):
            contribs.append((name, 0.0, abs(float(val))))
    contribs.sort(key=lambda t3: abs(t3[2]), reverse=True)
    return [{"name": n, "weight": round(w, 6), "contribution": round(c, 6)} for n, w, c in contribs[:top_k]]

# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------
def score_valuation(symbol: str) -> dict:
    meta = get_metadata(symbol) or {}
    return {
        "symbol": symbol.upper(),
        "sentiment_score": 0.5,
        "financial_score": 0.5,
        "growth_score": 0.5,
        "total_score": 0.5,
        "verdict": "Hold",
        "explain": {"metadata_used": meta},
    }

def predict_direction(symbol: str, temp: float | None = None) -> dict:
    """
    Smart predictor with per-request temperature override:
      - If 'temp' is provided, it is used; otherwise uses PREDICT_TEMP.
      - Uses TECH features if model expects len(TECH_FEATURE_ORDER), else LEGACY.
    """
    effective_temp = float(temp) if (temp is not None) else float(PREDICT_TEMP)

    if _wrap.model is None:
        return {
            "prob_up": 0.5,
            "prob_down": 0.5,
            "label": "HOLD",
            "features": {},
            "feature_order": [],
            "model_loaded_at": _wrap.loaded_at,
            "confidence": 0.0,
            "top_features": [],
            "calibration": {"temperature": effective_temp, "applied": bool(abs(effective_temp - 1.0) > 1e-6)},
            "mode": "legacy",
            "timestamp": int(time.time()),
        }

    n_in = int(getattr(_wrap.model, "n_features_in_", 0) or 0)
    use_tech = (n_in == len(TECH_FEATURE_ORDER))
    if use_tech:
        feats, order = _build_tech_features(symbol)
    else:
        feats, order = _build_legacy_features(symbol)
    x_vec = [_safe_float(feats.get(k, 0.0)) for k in order]

    try:
        proba = _wrap.model.predict_proba([x_vec])[0]
        if len(proba) == 2:
            prob_up = float(proba[1])
        else:
            df = getattr(_wrap.model, "decision_function", None)
            if callable(df):
                raw = float(df([x_vec])[0])
                import math
                prob_up = 1.0 / (1.0 + math.exp(-raw))
            else:
                prob_up = 0.5
    except Exception:
        y = _wrap.model.predict([x_vec])[0]
        prob_up = 0.7 if int(y) == 1 else 0.3

    prob_up_cal = _calibrate(prob_up, effective_temp)
    prob_down_cal = 1.0 - prob_up_cal
    label = "UP" if prob_up_cal >= 0.5 else "DOWN"

    return {
        "prob_up": round(prob_up_cal, 4),
        "prob_down": round(prob_down_cal, 4),
        "label": label,
        "features": {k: _safe_float(feats.get(k, 0.0)) for k in order},
        "feature_order": order,
        "model_loaded_at": _wrap.loaded_at,
        "confidence": _confidence(prob_up_cal),
        "top_features": _top_features(_wrap.model, x_vec, order, top_k=5),
        "calibration": {
            "temperature": effective_temp,
            "applied": bool(abs(effective_temp - 1.0) > 1e-6),
        },
        "mode": "tech" if use_tech else "legacy",
        "timestamp": int(time.time()),
    }