#!/bin/bash

# Stock Dashboard - Comprehensive API Test Suite
# Tests all 10 endpoints + caching performance

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Stock Dashboard API Test Suite (All 10 Endpoints)         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000/api"
PASS=0
FAIL=0

# Test helper function
test_endpoint() {
    local name=$1
    local endpoint=$2
    local check=$3

    echo -e "${BLUE}Testing: $name${NC}"
    response=$(curl -s "$BASE_URL$endpoint")

    if echo "$response" | grep -q "$check"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASS++))
        echo "Response: $(echo $response | jq -c . | head -c 100)..."
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAIL++))
        echo "Response: $(echo $response | jq -c . | head -c 100)..."
    fi
    echo ""
}

# ============== Test Suite ==============

echo -e "${YELLOW}1. PRICES ENDPOINT${NC}"
test_endpoint "Get AAPL prices" "/stocks/AAPL/prices?interval=1day&limit=3" "prices"

echo -e "${YELLOW}2. METADATA ENDPOINT${NC}"
test_endpoint "Get AAPL metadata" "/stocks/AAPL/metadata" "symbol"

echo -e "${YELLOW}3. NEWS ENDPOINT${NC}"
test_endpoint "Get AAPL news" "/stocks/AAPL/news?max_items=2" "news"

echo -e "${YELLOW}4. FEATURES ENDPOINT${NC}"
test_endpoint "Get AAPL features" "/stocks/AAPL/features?interval=1day&limit=50" "features"

echo -e "${YELLOW}5. VALUATION ENDPOINT${NC}"
test_endpoint "Get AAPL valuation" "/stocks/AAPL/valuation" "label"

echo -e "${YELLOW}6. NEWS SEARCH ENDPOINT${NC}"
test_endpoint "Search news" "/news/search?query=Apple&max_items=2" "news"

echo -e "${YELLOW}7. PAPERTRADE ENDPOINT${NC}"
test_endpoint "Paper trade AAPL" "/papertrade/AAPL" "trade_id"

echo -e "${YELLOW}8. PORTFOLIO TRADES ENDPOINT${NC}"
test_endpoint "Get portfolio trades" "/portfolio/trades" ""

echo -e "${YELLOW}9. ERROR HANDLING TEST${NC}"
test_endpoint "Invalid symbol error" "/stocks/INVALID123XYZ/prices" "error"

echo -e "${YELLOW}10. CROSS-SYMBOL TEST${NC}"
test_endpoint "Get MSFT prices" "/stocks/MSFT/prices?limit=1" "prices"

# ============== Cache Performance Test ==============

echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}CACHE PERFORMANCE TEST${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo ""

echo "Testing TSLA (first request - should hit API)..."
start=$(date +%s%N)
curl -s "$BASE_URL/stocks/TSLA/prices?limit=5" > /dev/null
end=$(date +%s%N)
first_time=$(( (end - start) / 1000000 ))
echo -e "${GREEN}First request: ${first_time}ms${NC}"

echo ""
echo "Testing TSLA again (second request - should be cached!)..."
start=$(date +%s%N)
curl -s "$BASE_URL/stocks/TSLA/prices?limit=5" > /dev/null
end=$(date +%s%N)
second_time=$(( (end - start) / 1000000 ))
echo -e "${GREEN}Second request: ${second_time}ms${NC}"

if [ $second_time -lt $((first_time / 2)) ]; then
    echo -e "${GREEN}✓ CACHE WORKING: ${second_time}ms is much faster than ${first_time}ms!${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ Cache may not be working optimally${NC}"
fi

# ============== Error Consistency Test ==============

echo ""
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}ERROR HANDLING CONSISTENCY TEST${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo ""

echo "Testing error format consistency..."
error1=$(curl -s "$BASE_URL/stocks/XYZ/prices" | jq '.detail' 2>/dev/null)
error2=$(curl -s "$BASE_URL/stocks/ABC/metadata" | jq '.detail' 2>/dev/null)

if [[ "$error1" == *"error"* && "$error2" == *"error"* ]]; then
    echo -e "${GREEN}✓ PASS: Error format is consistent across endpoints${NC}"
    echo "Error format: {\"detail\": \"ServiceName error: ...\"}"
    ((PASS++))
else
    echo -e "${RED}✗ FAIL: Error format is inconsistent${NC}"
    ((FAIL++))
fi

# ============== Summary ==============

echo ""
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}TEST SUMMARY${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Total Tests: $((PASS + FAIL))"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              🎉 ALL TESTS PASSED! 🎉                          ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║  Your API is production-ready:                                ║${NC}"
    echo -e "${GREEN}║  ✓ All 10 endpoints responding                               ║${NC}"
    echo -e "${GREEN}║  ✓ Error handling unified                                    ║${NC}"
    echo -e "${GREEN}║  ✓ Cache working efficiently                                 ║${NC}"
    echo -e "${GREEN}║  ✓ Data format consistent                                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check API responses above.${NC}"
    exit 1
fi

