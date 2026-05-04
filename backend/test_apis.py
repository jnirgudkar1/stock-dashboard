#!/usr/bin/env python3
"""
Quick API test script to verify third-party APIs are working
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("API CONFIGURATION TEST")
print("=" * 60)

# Check environment variables
print("\n1. Environment Variables:")
alpha_key = os.getenv("ALPHA_VANTAGE_KEY", "").strip()
twelve_key = os.getenv("TWELVE_DATA_KEY", "").strip()
finnhub_key = os.getenv("FINNHUB_KEY", "").strip()
gnews_key = os.getenv("GNEWS_API_KEY") or os.getenv("GNEWS_KEY", "").strip()

print(f"   ALPHA_VANTAGE_KEY: {'✓ Set' if alpha_key else '✗ Missing'} ({len(alpha_key)} chars)")
print(f"   TWELVE_DATA_KEY: {'✓ Set' if twelve_key else '✗ Missing'} ({len(twelve_key)} chars)")
print(f"   FINNHUB_KEY: {'✓ Set' if finnhub_key else '✗ Missing'} ({len(finnhub_key)} chars)")
print(f"   GNEWS_KEY: {'✓ Set' if gnews_key else '✗ Missing'} ({len(gnews_key)} chars)")

# Test imports
print("\n2. Testing Imports:")
try:
    from api.services.prices import get_prices
    print("   ✓ Prices service imports OK")
except Exception as e:
    print(f"   ✗ Prices service failed: {e}")

try:
    from api.services.metadata_services import get_metadata
    print("   ✓ Metadata service imports OK")
except Exception as e:
    print(f"   ✗ Metadata service failed: {e}")

try:
    from api.services.news import search_news
    print("   ✓ News service imports OK")
except Exception as e:
    print(f"   ✗ News service failed: {e}")

try:
    from api.services.features import get_features
    print("   ✓ Features service imports OK")
except Exception as e:
    print(f"   ✗ Features service failed: {e}")

# Test API calls
print("\n3. Testing API Calls (AAPL):")

try:
    from api.services.prices import get_prices
    result = get_prices("AAPL", interval="1day", limit=5)
    if result and "prices" in result:
        print(f"   ✓ Prices: Got {len(result['prices'])} bars from {result.get('provider', 'unknown')}")
    else:
        print(f"   ✗ Prices: Invalid response: {result}")
except Exception as e:
    print(f"   ✗ Prices: {str(e)[:80]}")

try:
    from api.services.metadata_services import get_metadata
    result = get_metadata("AAPL")
    if result and "symbol" in result:
        print(f"   ✓ Metadata: Got {result['symbol']} - {result.get('name', 'N/A')}")
    else:
        print(f"   ✗ Metadata: Invalid response: {result}")
except Exception as e:
    print(f"   ✗ Metadata: {str(e)[:80]}")

try:
    from api.services.news import search_news
    result = search_news("AAPL", max_items=1)
    if result and isinstance(result, list) and len(result) > 0:
        print(f"   ✓ News: Got {len(result)} article(s)")
    else:
        print(f"   ✗ News: Invalid response: {result}")
except Exception as e:
    print(f"   ✗ News: {str(e)[:80]}")

try:
    from api.services.features import get_features
    result = get_features("AAPL", interval="1day", limit=100, max_news=5)
    if result and "features" in result:
        features = result.get("features", {})
        print(f"   ✓ Features: Got {len(features)} features")
    else:
        print(f"   ✗ Features: Invalid response: {result}")
except Exception as e:
    print(f"   ✗ Features: {str(e)[:80]}")

print("\n" + "=" * 60)
