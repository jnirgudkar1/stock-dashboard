"""
API module initialization - shared utilities and consolidated imports
"""
try:
    from .cache_persistence import save_cache, load_cache
except ImportError:
    def save_cache(cache_type: str, cache: dict) -> None:
        """Fallback cache save - no-op if persistence module unavailable."""
        pass
    
    def load_cache(cache_type: str) -> dict:
        """Fallback cache load - returns empty dict if persistence module unavailable."""
        return {}

__all__ = ["save_cache", "load_cache"]

