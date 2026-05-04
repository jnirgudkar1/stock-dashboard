# backend/api/cache_persistence.py
"""
Persistent cache layer for all services
Saves cache to disk on updates and loads on startup
Allows historical data accumulation for ML training
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict
import time

# Data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./backend/data"))
CACHE_DIR = DATA_DIR / "cache"
PRICES_CACHE_FILE = CACHE_DIR / "prices_cache.json"
NEWS_SEARCH_CACHE_FILE = CACHE_DIR / "news_search_cache.json"
ARTICLE_CACHE_FILE = CACHE_DIR / "article_cache.json"
METADATA_CACHE_FILE = CACHE_DIR / "metadata_cache.json"
FEATURES_CACHE_FILE = CACHE_DIR / "features_cache.json"

def _ensure_dirs() -> None:
    """Create cache directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _serialize_cache(cache: Dict[Any, tuple]) -> Dict[str, Any]:
    """Convert in-memory cache dict to JSON-serializable format."""
    serialized = {}
    for key, (ts, data) in cache.items():
        # Convert tuple key to string (for JSON)
        if isinstance(key, tuple):
            key_str = "|".join(str(k) for k in key)
        else:
            key_str = str(key)
        
        serialized[key_str] = {
            "ts": ts,
            "data": data,
        }
    return serialized

def _deserialize_cache(data: Dict[str, Any]) -> Dict[Any, tuple]:
    """Convert JSON data back to in-memory cache dict."""
    cache = {}
    for key_str, value in data.items():
        # Reconstruct cache entry
        cache[key_str] = (value["ts"], value["data"])
    return cache

def save_cache(cache_type: str, cache: Dict[Any, tuple]) -> None:
    """Save cache to disk."""
    _ensure_dirs()
    
    file_map = {
        "prices": PRICES_CACHE_FILE,
        "news_search": NEWS_SEARCH_CACHE_FILE,
        "articles": ARTICLE_CACHE_FILE,
        "metadata": METADATA_CACHE_FILE,
        "features": FEATURES_CACHE_FILE,
    }
    
    filepath = file_map.get(cache_type)
    if not filepath:
        return
    
    try:
        serialized = _serialize_cache(cache)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serialized, f, separators=(",", ":"), ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Failed to save {cache_type} cache: {e}")

def load_cache(cache_type: str) -> Dict[Any, tuple]:
    """Load cache from disk."""
    _ensure_dirs()
    
    file_map = {
        "prices": PRICES_CACHE_FILE,
        "news_search": NEWS_SEARCH_CACHE_FILE,
        "articles": ARTICLE_CACHE_FILE,
        "metadata": METADATA_CACHE_FILE,
        "features": FEATURES_CACHE_FILE,
    }
    
    filepath = file_map.get(cache_type)
    if not filepath or not filepath.exists():
        return {}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _deserialize_cache(data)
    except Exception as e:
        print(f"Warning: Failed to load {cache_type} cache: {e}")
        return {}

def cleanup_expired_entries(cache: Dict[Any, tuple], ttl: int) -> Dict[Any, tuple]:
    """Remove expired entries from cache and return cleaned cache."""
    now = time.time()
    cleaned = {}
    for key, (ts, data) in cache.items():
        if now - ts <= ttl:
            cleaned[key] = (ts, data)
    return cleaned

def get_cache_stats(cache: Dict[Any, tuple]) -> Dict[str, Any]:
    """Get statistics about cache."""
    if not cache:
        return {"entries": 0, "oldest_entry_age_s": 0, "newest_entry_age_s": 0}
    
    now = time.time()
    ages = [now - ts for ts, _ in cache.values()]
    return {
        "entries": len(cache),
        "oldest_entry_age_s": max(ages),
        "newest_entry_age_s": min(ages),
        "avg_entry_age_s": sum(ages) / len(ages),
    }


