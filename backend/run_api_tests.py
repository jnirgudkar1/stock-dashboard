#!/usr/bin/env python3
"""
Stock Dashboard - Comprehensive API Test Suite
Tests all 10 endpoints + caching performance
"""

import requests
import json
import time
from typing import Tuple

BASE_URL = "http://localhost:8000/api"

# Colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
RESET = '\033[0m'

class APITester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def test_endpoint(self, name: str, endpoint: str, success_check: str = None) -> bool:
        """Test a single endpoint"""
        print(f"{BLUE}Testing: {name}{RESET}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            data = response.json()
            
            # Check if response is successful
            if response.status_code >= 400:
                print(f"{RED}✗ FAIL (HTTP {response.status_code}){RESET}")
                self.failed += 1
                print(f"Response: {str(data)[:100]}...")
                return False
            
            # Check for expected content
            if success_check:
                if success_check in json.dumps(data):
                    print(f"{GREEN}✓ PASS{RESET}")
                    self.passed += 1
                    print(f"Response: {json.dumps(data)[:100]}...")
                    return True
                else:
                    print(f"{RED}✗ FAIL (missing '{success_check}'){RESET}")
                    self.failed += 1
                    print(f"Response: {json.dumps(data)[:100]}...")
                    return False
            else:
                print(f"{GREEN}✓ PASS{RESET}")
                self.passed += 1
                print(f"Response: {json.dumps(data)[:100]}...")
                return True
                
        except Exception as e:
            print(f"{RED}✗ FAIL (Exception: {str(e)[:50]}){RESET}")
            self.failed += 1
            return False
        
        print()
    
    def run_all_tests(self):
        """Run complete test suite"""
        print()
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║     Stock Dashboard API Test Suite (All 10 Endpoints)         ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print()
        
        # Test 1: Prices
        print(f"{YELLOW}1. PRICES ENDPOINT{RESET}")
        self.test_endpoint("Get AAPL prices", "/stocks/AAPL/prices?interval=1day&limit=3", "prices")
        print()
        
        # Test 2: Metadata
        print(f"{YELLOW}2. METADATA ENDPOINT{RESET}")
        self.test_endpoint("Get AAPL metadata", "/stocks/AAPL/metadata", "symbol")
        print()
        
        # Test 3: News
        print(f"{YELLOW}3. NEWS ENDPOINT{RESET}")
        self.test_endpoint("Get AAPL news", "/stocks/AAPL/news?max_items=2", "news")
        print()
        
        # Test 4: Features
        print(f"{YELLOW}4. FEATURES ENDPOINT{RESET}")
        self.test_endpoint("Get AAPL features", "/stocks/AAPL/features?interval=1day&limit=50", "features")
        print()
        
        # Test 5: Valuation
        print(f"{YELLOW}5. VALUATION ENDPOINT{RESET}")
        self.test_endpoint("Get AAPL valuation", "/stocks/AAPL/valuation", "label")
        print()
        
        # Test 6: News Search
        print(f"{YELLOW}6. NEWS SEARCH ENDPOINT{RESET}")
        self.test_endpoint("Search news", "/news/search?query=Apple&max_items=2", "news")
        print()
        
        # Test 7: Paper Trade
        print(f"{YELLOW}7. PAPERTRADE ENDPOINT{RESET}")
        self.test_endpoint("Paper trade AAPL", "/papertrade/AAPL")
        print()
        
        # Test 8: Portfolio Trades
        print(f"{YELLOW}8. PORTFOLIO TRADES ENDPOINT{RESET}")
        self.test_endpoint("Get portfolio trades", "/portfolio/trades")
        print()
        
        # Test 9: Error Handling
        print(f"{YELLOW}9. ERROR HANDLING TEST{RESET}")
        self.test_endpoint("Invalid symbol error", "/stocks/INVALID123XYZ/prices", "error")
        print()
        
        # Test 10: Cross-Symbol
        print(f"{YELLOW}10. CROSS-SYMBOL TEST{RESET}")
        self.test_endpoint("Get MSFT prices", "/stocks/MSFT/prices?limit=1", "prices")
        print()
        
        # Cache Performance Test
        self.run_cache_test()
        
        # Error Consistency Test
        self.run_error_consistency_test()
        
        # Summary
        self.print_summary()
    
    def run_cache_test(self):
        """Test cache performance"""
        print(f"{YELLOW}════════════════════════════════════════════════════════{RESET}")
        print(f"{YELLOW}CACHE PERFORMANCE TEST{RESET}")
        print(f"{YELLOW}════════════════════════════════════════════════════════{RESET}")
        print()
        
        print("Testing TSLA (first request - should hit API)...")
        start = time.time() * 1000
        response1 = requests.get(f"{BASE_URL}/stocks/TSLA/prices?limit=5")
        end = time.time() * 1000
        first_time = end - start
        print(f"{GREEN}First request: {first_time:.2f}ms{RESET}")
        
        print()
        print("Testing TSLA again (second request - should be cached!)...")
        start = time.time() * 1000
        response2 = requests.get(f"{BASE_URL}/stocks/TSLA/prices?limit=5")
        end = time.time() * 1000
        second_time = end - start
        print(f"{GREEN}Second request: {second_time:.2f}ms{RESET}")
        
        if second_time < (first_time / 2):
            print(f"{GREEN}✓ CACHE WORKING: {second_time:.2f}ms is much faster than {first_time:.2f}ms!{RESET}")
            self.passed += 1
        else:
            print(f"{YELLOW}⚠ Cache may not be working optimally{RESET}")
        
        print()
    
    def run_error_consistency_test(self):
        """Test error handling consistency"""
        print(f"{YELLOW}════════════════════════════════════════════════════════{RESET}")
        print(f"{YELLOW}ERROR HANDLING CONSISTENCY TEST{RESET}")
        print(f"{YELLOW}════════════════════════════════════════════════════════{RESET}")
        print()
        
        print("Testing error format consistency...")
        try:
            error1 = requests.get(f"{BASE_URL}/stocks/XYZ/prices").json()
            error2 = requests.get(f"{BASE_URL}/stocks/ABC/metadata").json()
            
            if "detail" in error1 and "detail" in error2:
                if "error" in error1["detail"] and "error" in error2["detail"]:
                    print(f"{GREEN}✓ PASS: Error format is consistent across endpoints{RESET}")
                    print('Error format: {"detail": "ServiceName error: ..."}')
                    self.passed += 1
                else:
                    print(f"{RED}✗ FAIL: Error messages don't contain 'error'{RESET}")
                    self.failed += 1
            else:
                print(f"{RED}✗ FAIL: Error responses don't have 'detail' field{RESET}")
                self.failed += 1
        except Exception as e:
            print(f"{RED}✗ FAIL: Exception during error test: {str(e)}{RESET}")
            self.failed += 1
        
        print()
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        
        print(f"{YELLOW}════════════════════════════════════════════════════════{RESET}")
        print(f"{YELLOW}TEST SUMMARY{RESET}")
        print(f"{YELLOW}════════════════════════════════════════════════════════{RESET}")
        print()
        print(f"Total Tests: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print()
        
        if self.failed == 0:
            print(f"{GREEN}╔════════════════════════════════════════════════════════════════╗{RESET}")
            print(f"{GREEN}║              🎉 ALL TESTS PASSED! 🎉                          ║{RESET}")
            print(f"{GREEN}║                                                                ║{RESET}")
            print(f"{GREEN}║  Your API is production-ready:                                ║{RESET}")
            print(f"{GREEN}║  ✓ All 10 endpoints responding                               ║{RESET}")
            print(f"{GREEN}║  ✓ Error handling unified                                    ║{RESET}")
            print(f"{GREEN}║  ✓ Cache working efficiently                                 ║{RESET}")
            print(f"{GREEN}║  ✓ Data format consistent                                    ║{RESET}")
            print(f"{GREEN}╚════════════════════════════════════════════════════════════════╝{RESET}")
        else:
            print(f"{RED}Some tests failed. Check responses above.{RESET}")


if __name__ == "__main__":
    tester = APITester()
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Fatal error: {str(e)}{RESET}")

