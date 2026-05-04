# API Response Caching Analysis

## Summary
Your application implements **multi-layer in-memory caching on the backend** with **no HTTP caching headers**. All frontend requests bypass browser cache.

---

## Caching Strategy Overview

### Frontend HTTP Caching
**Status**: ❌ **DISABLED**
- All requests use `'Cache-Control': 'no-cache'` header
- Every fetch bypasses browser cache and hits the backend
- No browser-side storage of responses

### Backend In-Memory Caching
**Status**: ✅ **ACTIVE**
- Each service maintains its own cache dictionary
- TTL-based expiration (configurable via environment variables)
- Survives server restarts: ❌ NO (memory-only, lost on reboot)

---

## Detailed Caching Configuration

### 1. **Price Data Cache**
📊 **Service**: `backend/api/services/prices.py`
- **TTL**: 60 seconds (default)
- **Configuration**: `PRICE_CACHE_TTL` env var
- **Storage**: In-memory dictionary
- **Key**: `(symbol, interval, limit)` tuple
- **Behavior**: Each unique combination cached independently
- **Example**: 
  - Request 1: `(AAPL, 1day, 100)` → API call, cached 60s
  - Request 2 (30s later): `(AAPL, 1day, 100)` → Cache HIT ✓
  - Request 3 (90s later): `(AAPL, 1day, 100)` → Cache EXPIRED, API call

**Providers Cascade**: Alpha Vantage → Twelve Data → Finnhub
- If first provider succeeds, result is cached
- Subsequent requests use cache before trying providers

---

### 2. **News Search Cache**
📰 **Service**: `backend/api/services/news.py`
- **TTL**: 1800 seconds = **30 minutes** (default)
- **Configuration**: `NEWS_CACHE_TTL` env var
- **Storage**: In-memory dictionary
- **Key**: `(query, max_items)` tuple
- **Sources**: GNews API
- **Example**:
  - Request 1: Search "AAPL" → API call, cached 30m
  - Request 2 (5m later): Search "AAPL" → Cache HIT ✓

---

### 3. **Article Text Cache**
📄 **Service**: `backend/api/services/news.py`
- **TTL**: 86400 seconds = **24 hours** (default)
- **Configuration**: `ARTICLE_CACHE_TTL` env var
- **Storage**: In-memory dictionary
- **Key**: Full article URL (string)
- **Purpose**: Cache fetched HTML → text for news articles
- **Example**:
  - Request 1: Fetch article from "https://reuters.com/..." → API call, cached 24h
  - Request 2 (later): Same URL → Cache HIT ✓

---

### 4. **Company Metadata Cache**
🏢 **Service**: `backend/api/services/metadata_services.py`
- **TTL**: 7200 seconds = **2 hours** (default)
- **Configuration**: `METADATA_CACHE_TTL` env var
- **Storage**: In-memory dictionary
- **Key**: Symbol (string)
- **Sources**: Alpha Vantage (optional: Finnhub fallback)
- **Example**:
  - Request 1: Get AAPL metadata → API call, cached 2h
  - Request 2 (30m later): Get AAPL metadata → Cache HIT ✓

---

### 5. **Technical Features Cache**
📈 **Service**: `backend/api/services/features.py`
- **TTL**: 600 seconds = **10 minutes** (default)
- **Configuration**: `FEATURES_CACHE_TTL` env var
- **Storage**: In-memory dictionary
- **Key**: `(symbol, interval, limit, max_news)` tuple
- **Includes**: Price technical indicators + news sentiment
- **Example**:
  - Request 1: Get AAPL features → Compute indicators, cache 10m
  - Request 2 (2m later): Get AAPL features → Cache HIT ✓

---

### 6. **File-Based Trade Persistence (NOT for caching)**
💾 **Service**: `backend/api/filestore.py`
- **TTL**: Configurable per request (not auto-expiring)
- **Storage**: Disk files in `./backend/data/cache/`
- **Purpose**: Persistent storage for:
  - Paper trades (`paper_trades.json`)
  - Article text cache (SHA1 hashed filename)
- **Key Difference**: These are **file-based backups**, not HTTP response caching

---

## Cache Configuration Matrix

| Service | Default TTL | Env Variable | Storage | Scope |
|---------|-----------|-------------|---------|-------|
| Prices | 60s | `PRICE_CACHE_TTL` | Memory | Per (symbol, interval, limit) |
| News Search | 1800s (30m) | `NEWS_CACHE_TTL` | Memory | Per (query, max_items) |
| Article Text | 86400s (24h) | `ARTICLE_CACHE_TTL` | Memory | Per URL |
| Metadata | 7200s (2h) | `METADATA_CACHE_TTL` | Memory | Per symbol |
| Features | 600s (10m) | `FEATURES_CACHE_TTL` | Memory | Per (symbol, interval, limit, news) |

---

## How to Configure Caching

### Option 1: Environment Variables
```bash
# Set in backend/.env
PRICE_CACHE_TTL=120          # 2 minutes for prices
NEWS_CACHE_TTL=3600          # 1 hour for news
ARTICLE_CACHE_TTL=172800     # 2 days for articles
METADATA_CACHE_TTL=14400     # 4 hours for metadata
FEATURES_CACHE_TTL=1800      # 30 minutes for features
```

### Option 2: Edit Code
Each service has a default value in the code (fallback if env var not set)

---

## Performance Implications

### ✅ **Advantages**
1. **Fast Repeat Requests**: Repeated queries return instantly from memory
2. **API Rate Limit Protection**: Reduces external API calls significantly
3. **Reduced Latency**: Eliminates network round-trip for cached data
4. **Per-Request Keys**: Different intervals/limits have independent caches

### ⚠️ **Limitations**
1. **Memory Growth**: Cache never shrinks (keys accumulate)
2. **Lost on Restart**: All cache cleared when backend restarts
3. **Single-Server Only**: Cache not shared across multiple backend instances
4. **No Invalidation API**: Can't manually clear cache without restarting
5. **Stale Data**: Old data served until TTL expires

### ❌ **Current Issue**
**Frontend always bypasses browser cache** with `'Cache-Control': 'no-cache'`
- Even identical consecutive requests hit the backend
- Browser won't cache responses locally
- Only backend in-memory cache helps

---

## Recommendations

### 1. **Enable Browser Caching (Quick Win)**
Add proper cache headers for static data:

```python
# In routes.py, for price/metadata endpoints:
@router.get("/stocks/{symbol}/prices")
def api_prices(symbol: str, ...):
    response = {...}
    # Add cache headers for prices
    return Response(content=json.dumps(response),
                   media_type="application/json",
                   headers={"Cache-Control": "public, max-age=60"})
```

### 2. **Add Manual Cache Invalidation**
```python
@router.post("/admin/clear-cache/{service}")
def clear_cache(service: str):
    if service == "prices":
        _cache.clear()  # prices.py
    # ... other services
```

### 3. **Monitor Cache Performance**
Add metrics to track:
- Cache hit rate
- Memory usage
- Stale data frequency

### 4. **For Production (Multi-Instance)**
Consider using:
- **Redis** for distributed caching
- **SQLAlchemy with caching** backend
- **Memcached** for shared cache layer

---

## Cache Behavior Examples

### Scenario 1: Rapid Price Checks
```
User selects AAPL
  ↓ Request 1: /api/stocks/AAPL/prices?interval=1day&limit=100
  ↓ Cache MISS → Fetch from Alpha Vantage (~2-3s)
  ↓ Store in cache (TTL: 60s)
  
User switches to TSLA, back to AAPL (25s later)
  ↓ Request 2: /api/stocks/AAPL/prices?interval=1day&limit=100
  ↓ Cache HIT → Return instantly from memory (~0.1ms)
```

### Scenario 2: News Updates
```
Dashboard loads news for AAPL
  ↓ Request 1: /api/stocks/AAPL/news?max_items=25
  ↓ Cache MISS → Fetch from GNews (~1-2s)
  ↓ Store in cache (TTL: 1800s / 30m)
  
User refreshes page (5m later)
  ↓ Request 2: /api/stocks/AAPL/news?max_items=25
  ↓ Cache HIT → Return instantly (~0.1ms)
  ↓ Note: Shows 5min old news (acceptable for this use case)
```

### Scenario 3: Different Intervals Hit Different Caches
```
Request 1: /api/stocks/AAPL/prices?interval=1day&limit=100
  ↓ Key: (AAPL, 1day, 100)
  ↓ Cache MISS

Request 2: /api/stocks/AAPL/prices?interval=1day&limit=500
  ↓ Key: (AAPL, 1day, 500)
  ↓ Cache MISS (different key!)
  
Request 3: /api/stocks/AAPL/prices?interval=1day&limit=100
  ↓ Key: (AAPL, 1day, 100)
  ↓ Cache HIT (exact match)
```

---

## Summary Table

| Metric | Current Status | Recommendation |
|--------|---|---|
| Backend Caching | ✅ Active | Working as intended |
| Browser Caching | ❌ Disabled | Enable HTTP cache headers |
| Persistence | ❌ None | Use Redis for multi-instance |
| Invalidation | ❌ None | Add admin endpoint |
| Monitoring | ❌ None | Add metrics |
| TTLs | ✅ Reasonable | Consider tuning per use case |

---

## Commands to Test Caching

```bash
# Test cache behavior:

# 1. First request (should be slow)
time curl "http://localhost:8000/api/stocks/AAPL/prices?interval=1day&limit=100"

# 2. Immediate second request (should be fast)
time curl "http://localhost:8000/api/stocks/AAPL/prices?interval=1day&limit=100"

# 3. Different limit (cache miss, should be slower)
time curl "http://localhost:8000/api/stocks/AAPL/prices?interval=1day&limit=500"

# 4. After 61 seconds, original request (cache expired, should be slow)
sleep 61
time curl "http://localhost:8000/api/stocks/AAPL/prices?interval=1day&limit=100"
```

---

## Conclusion

**Good**: Backend caching is working with reasonable TTLs
**Bad**: Frontend ignores browser cache, so all requests go to backend
**Solution**: Enable HTTP caching headers for better performance + add Redis for multi-instance support

