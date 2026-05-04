"""
Rate limiting utilities to avoid hitting third-party API limits
"""
import time
from functools import wraps
from typing import Dict

# Track last request time per API
_last_request: Dict[str, float] = {}

def rate_limit(provider: str, min_interval: float):
    """
    Decorator to rate-limit API calls.
    
    Args:
        provider: Name of the API provider (e.g., "alpha_vantage")
        min_interval: Minimum seconds between requests to this provider
    
    Example:
        @rate_limit("alpha_vantage", 0.2)  # Max 5 calls/second
        def fetch_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            last = _last_request.get(provider, 0)
            elapsed = now - last
            
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                print(f"⏱️  Rate limiting {provider}: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            _last_request[provider] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def batch_requests(items, delay=1.0):
    """
    Generator to yield items with delay between them.
    Useful for multiple API calls.
    
    Example:
        for symbol in batch_requests(['AAPL', 'GOOGL', 'MSFT'], delay=0.3):
            data = get_prices(symbol)
    """
    for item in items:
        yield item
        time.sleep(delay)


def adaptive_backoff(max_retries=3, base_delay=1.0):
    """
    Decorator for retrying failed requests with exponential backoff.
    
    Example:
        @adaptive_backoff(max_retries=3, base_delay=2.0)
        def get_data():
            # Will retry up to 3 times with 2s, 4s, 8s delays
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    delay = base_delay * (2 ** attempt)
                    print(f"⚠️  Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)[:50]}")
                    time.sleep(delay)
        return wrapper
    return decorator

