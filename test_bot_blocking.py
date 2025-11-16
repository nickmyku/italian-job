#!/usr/bin/env python3
"""Test script to verify bot blocking functionality"""

import requests
import sys

# Test URL - adjust if needed
BASE_URL = "http://localhost:3000"

def test_normal_browser():
    """Test with normal browser user agent - should work"""
    print("\n1. Testing normal browser user agent...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(f"{BASE_URL}/", headers=headers, timeout=5)
        if response.status_code == 200:
            print("   ✓ PASS: Normal browser allowed (status 200)")
            return True
        else:
            print(f"   ✗ FAIL: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False

def test_bot_user_agent():
    """Test with bot user agent - should be blocked"""
    print("\n2. Testing bot user agent...")
    bot_agents = [
        'Googlebot/2.1',
        'Mozilla/5.0 (compatible; bingbot/2.0)',
        'python-requests/2.31.0',
        'curl/7.68.0',
        'scrapy/2.5.0'
    ]
    
    passed = 0
    for agent in bot_agents:
        headers = {
            'User-Agent': agent,
            'Accept': 'text/html'
        }
        try:
            response = requests.get(f"{BASE_URL}/", headers=headers, timeout=5)
            if response.status_code == 403:
                print(f"   ✓ PASS: Bot blocked ({agent[:30]}...)")
                passed += 1
            else:
                print(f"   ✗ FAIL: Bot not blocked ({agent[:30]}...) - status {response.status_code}")
        except Exception as e:
            print(f"   ✗ ERROR: {e} ({agent[:30]}...)")
    
    return passed == len(bot_agents)

def test_missing_user_agent():
    """Test with missing user agent - should be blocked"""
    print("\n3. Testing missing user agent...")
    headers = {
        'Accept': 'text/html'
    }
    try:
        response = requests.get(f"{BASE_URL}/", headers=headers, timeout=5)
        if response.status_code == 403:
            print("   ✓ PASS: Request without user agent blocked (status 403)")
            return True
        else:
            print(f"   ✗ FAIL: Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False

def test_missing_accept_header():
    """Test with missing Accept header - should be blocked"""
    print("\n4. Testing missing Accept header...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(f"{BASE_URL}/", headers=headers, timeout=5)
        if response.status_code == 403:
            print("   ✓ PASS: Request without Accept header blocked (status 403)")
            return True
        else:
            print(f"   ✗ FAIL: Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False

def test_robots_txt():
    """Test that robots.txt is accessible"""
    print("\n5. Testing robots.txt access...")
    try:
        response = requests.get(f"{BASE_URL}/robots.txt", timeout=5)
        if response.status_code == 200 and 'Disallow' in response.text:
            print("   ✓ PASS: robots.txt accessible and contains Disallow")
            return True
        else:
            print(f"   ✗ FAIL: robots.txt not working properly (status {response.status_code})")
            return False
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
        return False

def test_api_rate_limiting():
    """Test rate limiting on API endpoints"""
    print("\n6. Testing API rate limiting...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    # Make multiple requests quickly
    success_count = 0
    rate_limited = False
    
    for i in range(25):
        try:
            response = requests.get(f"{BASE_URL}/api/location", headers=headers, timeout=5)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
        except Exception:
            pass
    
    if rate_limited or success_count <= 21:  # Rate limit is 20 per minute
        print(f"   ✓ PASS: Rate limiting working (got {success_count} successful requests)")
        return True
    else:
        print(f"   ✗ FAIL: Rate limiting not working properly ({success_count} requests succeeded)")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Bot Blocking Tests")
    print("=" * 60)
    print("\nMake sure the Flask app is running on http://localhost:3000")
    print("Press Ctrl+C to cancel or wait 3 seconds to continue...")
    
    try:
        import time
        time.sleep(3)
    except KeyboardInterrupt:
        print("\nTest cancelled.")
        sys.exit(0)
    
    results = []
    results.append(test_normal_browser())
    results.append(test_bot_user_agent())
    results.append(test_missing_user_agent())
    results.append(test_missing_accept_header())
    results.append(test_robots_txt())
    results.append(test_api_rate_limiting())
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! Bot blocking is working correctly.")
        sys.exit(0)
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the output above.")
        sys.exit(1)
