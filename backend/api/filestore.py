# backend/api/filestore.py
from __future__ import annotations
import os, json, time, hashlib, tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Data locations
DATA_DIR = Path(os.getenv("DATA_DIR", "./backend/data"))
TRADES_FILE = DATA_DIR / "paper_trades.json"
CACHE_DIR = DATA_DIR / "cache"

def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)

def preload() -> None:
    """Ensure required files/dirs exist on startup."""
    _ensure_dirs()
    if not TRADES_FILE.exists():
        _atomic_write(TRADES_FILE, "[]")

# -------------------- Trades --------------------
def load_trades() -> List[Dict[str, Any]]:
    try:
        txt = TRADES_FILE.read_text(encoding="utf-8")
        return json.loads(txt or "[]")
    except Exception:
        return []

def save_trades(items: List[Dict[str, Any]]) -> None:
    _atomic_write(TRADES_FILE, json.dumps(items, separators=(",", ":"), ensure_ascii=False))

def append_trade(t: Dict[str, Any]) -> None:
    items = load_trades()
    tid = t.get("id")
    if tid:
        items = [x for x in items if x.get("id") != tid]
    items.insert(0, t)  # newest first
    save_trades(items)

def update_trade_eval(trade_id: str, *, last: float, ret: float, correct: bool) -> None:
    items = load_trades()
    ts = int(time.time())
    for it in items:
        if it.get("id") == trade_id:
            it["status"] = "CLOSED"
            it["_eval"] = {"asOf": ts, "last": float(last), "ret": float(ret), "correct": bool(correct)}
            break
    save_trades(items)

# -------------------- Disk cache --------------------
def _key_to_path(key: str) -> Path:
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{h}.json"

def cache_get(key: str, ttl_seconds: int) -> Optional[Dict[str, Any]]:
    p = _key_to_path(key)
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    ts = int(obj.get("ts", 0))
    if int(time.time()) - ts > int(ttl_seconds):
        return None
    return obj.get("payload")

def cache_set(key: str, payload: Dict[str, Any]) -> None:
    obj = {"ts": int(time.time()), "payload": payload}
    _atomic_write(_key_to_path(key), json.dumps(obj, separators=(",", ":"), ensure_ascii=False))