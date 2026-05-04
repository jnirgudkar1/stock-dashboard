"""
Debug utility to test API connectivity
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("TESTING THIRD-PARTY API CONNECTIVITY")
print("="*70)

# Test Alpha Vantage
print("\n1. Testing Alpha Vantage API:")
av_key = os.getenv("ALPHA_VANTAGE_KEY")
if av_key:
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": "AAPL",
            "apikey": av_key,
        }
        r = requests.get(url, params=params, timeout=5)
        print(f"   Status: {r.status_code}")
        json_data = r.json()
        
        if "Symbol" in json_data:
            print(f"   ✓ Success: Got data for {json_data.get('Symbol')}")
        elif "Note" in json_data:
            print(f"   ⚠️  Rate limit: {json_data['Note'][:60]}...")
        elif "Error Message" in json_data:
            print(f"   ✗ Error: {json_data['Error Message']}")
        else:
            print(f"   ? Unexpected response: {str(json_data)[:100]}")
    except Exception as e:
        print(f"   ✗ Exception: {str(e)[:60]}")
else:
    print("   ✗ API key not configured")

# Test Twelve Data
print("\n2. Testing Twelve Data API:")
td_key = os.getenv("TWELVE_DATA_KEY")
if td_key:
    try:
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": "AAPL",
            "interval": "1day",
            "apikey": td_key,
            "outputsize": 10,
        }
        r = requests.get(url, params=params, timeout=5)
        print(f"   Status: {r.status_code}")
        json_data = r.json()
        
        if "values" in json_data and len(json_data["values"]) > 0:
            print(f"   ✓ Success: Got {len(json_data['values'])} price bars")
        elif "message" in json_data:
            print(f"   ? Response: {json_data['message'][:60]}")
        else:
            print(f"   ? Unexpected response: {str(json_data)[:100]}")
    except Exception as e:
        print(f"   ✗ Exception: {str(e)[:60]}")
else:
    print("   ✗ API key not configured")

# Test Finnhub
print("\n3. Testing Finnhub API:")
fh_key = os.getenv("FINNHUB_KEY")
if fh_key:
    try:
        url = "https://finnhub.io/api/v1/stock/candle"
        params = {
            "symbol": "AAPL",
            "resolution": "D",
            "from": "1609459200",
            "to": "1609545600",
            "token": fh_key,
        }
        r = requests.get(url, params=params, timeout=5)
        print(f"   Status: {r.status_code}")
        json_data = r.json()
        
        if json_data.get("s") == "ok":
            print(f"   ✓ Success: Got {len(json_data.get('t', []))} candles")
        else:
            print(f"   ? Response: {json_data}")
    except Exception as e:
        print(f"   ✗ Exception: {str(e)[:60]}")
else:
    print("   ✗ API key not configured")

# Test GNews
print("\n4. Testing GNews API:")
gn_key = os.getenv("GNEWS_API_KEY") or os.getenv("GNEWS_KEY")
if gn_key:
    try:
        url = "https://gnews.io/api/v4/search"
        params = {
            "q": "AAPL",
            "lang": "en",
            "max": 1,
            "token": gn_key,
        }
        r = requests.get(url, params=params, timeout=5)
        print(f"   Status: {r.status_code}")
        json_data = r.json()
        
        if "articles" in json_data and len(json_data["articles"]) > 0:
            print(f"   ✓ Success: Got {len(json_data['articles'])} articles")
        elif "message" in json_data:
            print(f"   ? Response: {json_data['message'][:60]}")
        else:
            print(f"   ? Unexpected response: {str(json_data)[:100]}")
    except Exception as e:
        print(f"   ✗ Exception: {str(e)[:60]}")
else:
    print("   ✗ API key not configured")

print("\n" + "="*70)
print("\nIf any API failed, check:")
print("1. API keys are correct in .env")
print("2. API rate limits haven't been exceeded")
print("3. Your internet connection")
print("4. The API service status page")
print("="*70 + "\n")

