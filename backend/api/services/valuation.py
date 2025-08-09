from __future__ import annotations

import os
import time
import json
import csv
import threading
import typing as t
from dataclasses import dataclass
from datetime import datetime

# ---- Path resolution (repo root -> training_pipeline/models/...) ----
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DEFAULT_MODEL_PATH = os.path.join(PROJECT_ROOT, "training_pipeline", "models", "price_direction_model.pkl")
MODEL_PATH = os.getenv("PREDICT_MODEL_PATH", DEFAULT_MODEL_PATH)

DEFAULT_TRAIN_CSV = os.path.join(PROJECT_ROOT, "training_pipeline", "data", "training_data.csv")
FEATURES_SIDECAR = MODEL_PATH.replace(".pkl", ".features.json")

_MODEL_LOCK = threading.Lock()
_model = None  # lazy
_FEATURE_ORDER: t.List[str] = []  # lazy cache

# ---- Import other services for features/valuation ----
from .metadata_services import get_metadata  # primary fundamentals
from .prices import get_prices, PriceServiceError  # normalized OHLCV
from .news import search_news, sentiment  # news + sentiment
from .metadata_services import ENABLE_FINNHUB_FALLBACK, FINNHUB_API_KEY  # toggle + key for fallback EPS

# Optional: Finnhub for EPS fallback
try:
    import finnhub  # type: ignore
except Exception:  # pragma: no cover
    finnhub = None  # gracefully handle if lib not installed


# =============================================================================
# Valuation scoring (unchanged public API, with EPS helper)
# =============================================================================
def _get_float(d: dict, key: str, default: float = 0.0) -> float:
    try:
        v = d.get(key)
        return float(v) if v is not None else default
    except Exception:
        return default


# ---------- EPS helper (Finnhub fallback only; no DB) ----------
def _eps_from_finnhub(symbol: str) -> float | None:
    """Fetch EPS (TTM) from Finnhub metrics when enabled."""
    if not (ENABLE_FINNHUB_FALLBACK and FINNHUB_API_KEY and finnhub):
        return None
    try:
        client = finnhub.Client(api_key=FINNHUB_API_KEY)
        metrics = client.company_basic_financials(symbol, "all") or {}
        metric = metrics.get("metric", {})
        eps = metric.get("epsInclExtraItemsTTM")
        return float(eps) if eps is not None else None
    except Exception:
        return None


def get_eps(symbol: str, md_hint: dict | None = None) -> float | None:
    """
    Robust EPS getter (no SQLite):
      1) use provided metadata hint if it contains EPS
      2) Finnhub fallback (optional)
    """
    symbol = symbol.upper()

    # 1) metadata hint (Alpha Overview often provides EPS)
    if md_hint:
        eps0 = md_hint.get("eps") or md_hint.get("EPS") or md_hint.get("trailingEps")
        try:
            if eps0 is not None:
                epsf = float(eps0)
                if epsf != 0.0:
                    return epsf
        except Exception:
            pass

    # 2) Finnhub fallback (optional)
    eps = _eps_from_finnhub(symbol)
    if eps is not None and eps != 0.0:
        return eps

    return None


def score_valuation(symbol: str) -> dict:
    """
    Blend financials, growth, and news sentiment → verdict.
    Returns (legacy fields preserved) + new self-explanatory fields.
    """
    symbol = symbol.upper()

    md = get_metadata(symbol) or {}
    pe = _get_float(md, "peRatio", 0.0)
    dy = _get_float(md, "dividendYield", 0.0)
    mc = _get_float(md, "marketCap", 0.0)

    # bring in EPS (consistent even if metadata cache omitted it)
    eps_val = get_eps(symbol, md_hint=md)

    # ---- Financial score ----
    financial = 0.5
    notes: dict[str, str] = {}
    if pe > 0:
        if pe < 15:
            financial += 0.25; notes["pe"] = "> strong (under 15)"
        elif pe < 25:
            financial += 0.1;  notes["pe"] = "> decent (15–25)"
        elif pe < 40:
            financial -= 0.05; notes["pe"] = "- elevated (25–40)"
        else:
            financial -= 0.2;  notes["pe"] = "- high (40+)"
    if dy >= 2:
        financial += 0.1; notes["dividend"] = "+ yield ≥2%"
    if mc >= 2e11:
        financial += 0.05; notes["size"] = "+ mega-cap stability"

    # ---- Growth score (metadata-driven; keep behavior) ----
    rev_g = _get_float(md, "revenueGrowth", 0.0)
    eps_g = _get_float(md, "epsGrowth", 0.0)
    growth = 0.5 + 0.25 * (1 if rev_g > 0 else -0.5) + 0.25 * (1 if eps_g > 0 else -0.5)

    # ---- Sentiment from recent headlines ----
    try:
        news = search_news(symbol=symbol, max_items=20)
    except Exception:
        news = []
    n = len(news)
    if n:
        vals: list[float] = []
        for it in news:
            try:
                s = it.get("sentiment", {})
                if isinstance(s, dict) and "score" in s:
                    vals.append(float(s["score"]))
                else:
                    text = f"{it.get('title','')}. {it.get('description','')}"
                    vals.append(float(sentiment(text).get("score", 0.0)))
            except Exception:
                pass
        news_sent = (sum(vals) / len(vals)) if vals else 0.0
    else:
        news_sent = 0.0

    # Map sentiment [-1..1] → [0..1]
    sentiment_score = (news_sent + 1.0) / 2.0

    # ---- Blend to total + verdict (weights unchanged) ----
    total = 0.45 * financial + 0.35 * growth + 0.20 * sentiment_score
    verdict = "Buy" if total >= 0.66 else ("Sell" if total <= 0.40 else "Hold")

    # ---------- Bands & explanations ----------
    def _band(v: float | None, lo=0.33, hi=0.66):
        if v is None:
            return ("unknown", "grey")
        if v < lo:   return ("low", "red")
        if v < hi:   return ("medium", "yellow")
        return ("high", "green")

    def _why_sent(v):
        if v is None:      return "No recent news sentiment available."
        if v >= 0.66:      return "News tone is broadly positive; tends to support near‑term strength."
        if v >= 0.33:      return "Mixed news tone; near‑term moves may be range‑bound."
        return "News tone is negative; near‑term pressure is possible."

    def _why_fin(v):
        if v is None:      return "Insufficient fundamentals data."
        if v >= 0.66:      return "Valuation looks attractive vs. earnings and payout."
        if v >= 0.33:      return "Valuation appears fair — neither cheap nor extreme."
        return "Looks expensive vs. earnings; proceed carefully."

    def _why_growth(v):
        if v is None:      return "Growth metrics unavailable."
        if v >= 0.66:      return "Earnings/revenue growth trends are strong."
        if v >= 0.33:      return "Growth is moderate."
        return "Growth is weak or slowing."

    s_lab, s_col = _band(sentiment_score)
    f_lab, f_col = _band(financial)
    g_lab, g_col = _band(growth)
    t_lab, t_col = _band(total)
    v_col = "green" if verdict == "Buy" else ("red" if verdict == "Sell" else "yellow")

    # ---------- Return ----------
    return {
        "symbol": symbol,
        "sentiment_score": round(sentiment_score, 2),
        "financial_score": round(financial, 2),
        "growth_score": round(growth, 2),
        "total_score": round(total, 2),
        "verdict": verdict,
        "scores": {
            "sentiment": {"value": round(sentiment_score, 2), "label": s_lab, "color": s_col, "why": _why_sent(sentiment_score)},
            "financial": {"value": round(financial, 2),        "label": f_lab, "color": f_col, "why": _why_fin(financial)},
            "growth":    {"value": round(growth, 2),           "label": g_lab, "color": g_col, "why": _why_growth(growth)},
            "total":     {"value": round(total, 2),            "label": t_lab, "color": t_col},
        },
        "verdict_detail": {"label": verdict, "color": v_col},
        "explain": {
            "metadata_used": {
                "peRatio": md.get("peRatio"),
                "dividendYield": md.get("dividendYield"),
                "marketCap": md.get("marketCap"),
                "revenueGrowth": md.get("revenueGrowth"),
                "epsGrowth": md.get("epsGrowth"),
                "eps": eps_val,
            },
            "notes": {},
            "news_count": n,
            "news_avg_sentiment": round(news_sent, 4),
        },
    }


# =============================================================================
# Model loader (joblib→pickle) + feature-order detection
# =============================================================================
@dataclass
class _ModelWrapper:
    model: t.Any
    loaded_at: float


def _load_model() -> _ModelWrapper:
    global _model
    if _model is not None:
        return _model
    with _MODEL_LOCK:
        if _model is not None:
            return _model

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

        # Try joblib first
        try:
            from joblib import load as joblib_load  # type: ignore
            m = joblib_load(MODEL_PATH)
            _model = _ModelWrapper(model=m, loaded_at=time.time())
            return _model
        except Exception as e_joblib:
            # Fall back to pickle
            try:
                import pickle  # nosec B403
                with open(MODEL_PATH, "rb") as f:
                    m = pickle.load(f)
                _model = _ModelWrapper(model=m, loaded_at=time.time())
                return _model
            except Exception as e_pickle:
                raise RuntimeError(
                    f"Failed to load model from {MODEL_PATH}. "
                    f"joblib error: {e_joblib}; pickle error: {e_pickle}. "
                    "If saved with joblib.dump(...), ensure joblib is installed "
                    "and sklearn versions are compatible."
                )


def _infer_feature_order_from_sidecar() -> t.List[str]:
    if os.path.exists(FEATURES_SIDECAR):
        try:
            with open(FEATURES_SIDECAR, "r") as f:
                meta = json.load(f)
            fo = meta.get("feature_order")
            if isinstance(fo, list) and fo:
                return [str(x) for x in fo]
        except Exception:
            pass
    return []


def _infer_feature_order_from_csv() -> t.List[str]:
    if os.path.exists(DEFAULT_TRAIN_CSV):
        try:
            with open(DEFAULT_TRAIN_CSV, "r", newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
            drop = {"date", "symbol", "label_next_7d"}
            cols = [h for h in header if h and h not in drop]
            return cols
        except Exception:
            pass
    return []


def _infer_feature_order_from_env() -> t.List[str]:
    raw = os.getenv("PREDICT_FEATURE_ORDER", "")
    if raw.strip():
        return [c.strip() for c in raw.split(",") if c.strip()]
    return []


def _get_feature_order(model) -> t.List[str]:
    """
    Resolve a feature order using sidecar -> CSV -> env,
    then truncate/pad to model.n_features_in_ if available.
    """
    global _FEATURE_ORDER
    if _FEATURE_ORDER:
        return _FEATURE_ORDER

    order = _infer_feature_order_from_sidecar()
    if not order:
        order = _infer_feature_order_from_csv()
    if not order:
        order = _infer_feature_order_from_env()

    # Enforce model's expected size, if exposed
    try:
        n_expected = int(getattr(model, "n_features_in_", 0))
    except Exception:
        n_expected = 0

    if n_expected > 0:
        if len(order) > n_expected:
            order = order[:n_expected]
        elif len(order) < n_expected:
            order = order + [f"_pad_{i}" for i in range(n_expected - len(order))]

    # Final fallback tailored to your training CSV
    if not order:
        order = ["pe_ratio", "eps", "revenue_growth", "close_price"]

    _FEATURE_ORDER = order
    return _FEATURE_ORDER


# =============================================================================
# Feature assembly to match training
# =============================================================================
def _assemble_features(symbol: str) -> dict:
    """
    Build the feature dict your model was trained on:
    - pe_ratio
    - eps
    - revenue_growth
    - close_price (latest close)
    """
    symbol = symbol.upper()
    md = get_metadata(symbol) or {}

    pe_ratio = md.get("pe_ratio") or md.get("peRatio") or md.get("pe") or 0.0

    # EPS with robust fallback (no DB)
    eps_val = md.get("eps") or md.get("trailingEps") or md.get("EPS")
    if not eps_val:
        eps_val = get_eps(symbol, md_hint=md)

    revenue_growth = md.get("revenue_growth") or md.get("revenueGrowth") or 0.0

    # Latest close price from normalized prices API
    close_price = 0.0
    try:
        p = get_prices(symbol, interval="1day", limit=1)
        bars = p.get("prices", [])
        if bars:
            close_price = float(bars[-1].get("close", 0.0))
    except PriceServiceError:
        pass
    except Exception:
        pass

    return {
        "pe_ratio": float(pe_ratio or 0.0),
        "eps": float(eps_val or 0.0),
        "revenue_growth": float(revenue_growth or 0.0),
        "close_price": float(close_price or 0.0),
    }


# =============================================================================
# Prediction API
# =============================================================================
def predict_direction(features: dict | None = None, *, symbol: str | None = None) -> dict:
    if features is None:
        if not symbol:
            raise ValueError("Provide either features or a symbol")
        features = _assemble_features(symbol.upper())

    wrap = _load_model()
    order = _get_feature_order(wrap.model)

    # Build row in that exact order; unknowns → 0.0
    row = [float(features.get(k, 0.0)) for k in order]
    X = [row]

    try:
        proba = wrap.model.predict_proba(X)[0]
        prob_down = float(proba[0])
        prob_up = float(proba[1]) if len(proba) > 1 else 1.0 - prob_down
    except Exception:
        y = wrap.model.predict(X)[0]
        prob_up = 0.7 if int(y) == 1 else 0.3
        prob_down = 1.0 - prob_up

    label = "UP" if prob_up >= 0.5 else "DOWN"
    return {
        "prob_up": round(prob_up, 4),
        "prob_down": round(prob_down, 4),
        "label": label,
        "features": {k: features.get(k, 0.0) for k in order},
        "feature_order": order,
        "model_loaded_at": wrap.loaded_at,
    }