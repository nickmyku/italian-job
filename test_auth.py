#!/usr/bin/env python3
"""
Test script for session-based authentication
"""
import requests

BASE_URL = "http://localhost:3000"

def test_authentication():
    """Test the authentication flow"""
    print("Testing Session-Based Authentication\n")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Test 1: Try to access protected endpoint without auth
    print("\n1. Testing POST /api/update without authentication...")
    try:
        response = session.post(f"{BASE_URL}/api/update")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 401:
            print("   ✓ PASS: Correctly blocked unauthenticated request")
        else:
            print("   ✗ FAIL: Should return 401 for unauthenticated request")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 2: Check authentication status (should be false)
    print("\n2. Testing GET /api/check-auth (before login)...")
    try:
        response = session.get(f"{BASE_URL}/api/check-auth")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Response: {data}")
        if not data.get('authenticated'):
            print("   ✓ PASS: Correctly shows not authenticated")
        else:
            print("   ✗ FAIL: Should not be authenticated yet")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 3: Login with correct credentials
    print("\n3. Testing POST /api/login with correct credentials...")
    try:
        response = session.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "shiptracker2024"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 200 and response.json().get('success'):
            print("   ✓ PASS: Login successful")
        else:
            print("   ✗ FAIL: Login should succeed")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 4: Check authentication status (should be true)
    print("\n4. Testing GET /api/check-auth (after login)...")
    try:
        response = session.get(f"{BASE_URL}/api/check-auth")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Response: {data}")
        if data.get('authenticated') and data.get('username') == 'admin':
            print("   ✓ PASS: Correctly shows authenticated")
        else:
            print("   ✗ FAIL: Should be authenticated")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 5: Try to access protected endpoint with auth
    print("\n5. Testing POST /api/update with authentication...")
    try:
        response = session.post(f"{BASE_URL}/api/update")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code in [200, 500]:  # 500 if scraping fails
            print("   ✓ PASS: Allowed authenticated request")
        else:
            print("   ✗ FAIL: Should allow authenticated request")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 6: Logout
    print("\n6. Testing POST /api/logout...")
    try:
        response = session.post(f"{BASE_URL}/api/logout")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 200:
            print("   ✓ PASS: Logout successful")
        else:
            print("   ✗ FAIL: Logout should succeed")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 7: Check authentication status after logout
    print("\n7. Testing GET /api/check-auth (after logout)...")
    try:
        response = session.get(f"{BASE_URL}/api/check-auth")
        data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Response: {data}")
        if not data.get('authenticated'):
            print("   ✓ PASS: Correctly shows not authenticated")
        else:
            print("   ✗ FAIL: Should not be authenticated after logout")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    # Test 8: Try wrong credentials
    print("\n8. Testing POST /api/login with wrong credentials...")
    try:
        response = session.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "wrongpassword"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 401:
            print("   ✓ PASS: Correctly rejected wrong credentials")
        else:
            print("   ✗ FAIL: Should reject wrong credentials")
    except Exception as e:
        print(f"   ✗ ERROR: {e}")
    
    print("\n" + "=" * 50)
    print("Authentication test complete!\n")
    print("To test manually, visit: http://localhost:3000")
    print("Default credentials: admin / shiptracker2024")

if __name__ == "__main__":
    test_authentication()
