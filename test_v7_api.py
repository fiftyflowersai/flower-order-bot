#!/usr/bin/env python3
"""
Test script for v7 API - iteratively tests the web server
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "error": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": "Connection refused - is the server running?"
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": str(e)
        }

def test_chat_query(message, session_id="test"):
    """Test a chat query"""
    return test_endpoint("/chat", "POST", {
        "message": message,
        "session_id": session_id
    })

def run_tests():
    """Run all tests"""
    print("="*80)
    print("V7 API TEST SUITE")
    print("="*80)
    
    # Test 1: Check if server is running
    print("\n1. Testing server connection...")
    result = test_endpoint("/")
    if result["success"]:
        print("   ✅ Server is running")
    else:
        print(f"   ❌ Server not responding: {result['error']}")
        return False
    
    # Test 2: Simple query
    print("\n2. Testing simple query: 'red flowers'")
    result = test_chat_query("red flowers")
    if result["success"]:
        print("   ✅ Query successful")
        if "response" in result["data"]:
            print(f"   Response length: {len(result['data']['response'])} chars")
            print(f"   Memory: {result['data'].get('memory', {})}")
        else:
            print(f"   ⚠️  Unexpected response format: {result['data']}")
    else:
        print(f"   ❌ Query failed: {result['error']}")
        if result.get("data"):
            print(f"   Response: {result['data']}")
    
    # Test 3: Complex query
    print("\n3. Testing complex query: 'red roses for a wedding'")
    result = test_chat_query("red roses for a wedding", session_id="test2")
    if result["success"]:
        print("   ✅ Query successful")
        if "response" in result["data"]:
            response_text = result["data"]["response"]
            print(f"   Response length: {len(response_text)} chars")
            if "error" in response_text.lower() or "SQL" in response_text:
                print(f"   ⚠️  Possible error in response:")
                print(f"   {response_text[:500]}")
            else:
                print(f"   ✅ Response looks good")
                print(f"   First 200 chars: {response_text[:200]}...")
        else:
            print(f"   ⚠️  Unexpected response format")
    else:
        print(f"   ❌ Query failed: {result['error']}")
        if result.get("data"):
            print(f"   Response: {result['data']}")
    
    # Test 4: Budget filter
    print("\n4. Testing budget filter: 'under $100'")
    result = test_chat_query("under $100", session_id="test3")
    if result["success"]:
        print("   ✅ Query successful")
    else:
        print(f"   ❌ Query failed: {result['error']}")
    
    # Test 5: DIY level filter
    print("\n5. Testing DIY level: 'ready to go flowers'")
    result = test_chat_query("ready to go flowers", session_id="test4")
    if result["success"]:
        print("   ✅ Query successful")
    else:
        print(f"   ❌ Query failed: {result['error']}")
    
    # Test 6: Combined filters
    print("\n6. Testing combined filters: 'red and white flowers under $200'")
    result = test_chat_query("red and white flowers under $200", session_id="test5")
    if result["success"]:
        print("   ✅ Query successful")
    else:
        print(f"   ❌ Query failed: {result['error']}")
    
    # Test 7: Reset
    print("\n7. Testing reset endpoint...")
    result = test_endpoint("/reset", "POST", {"session_id": "test"})
    if result["success"]:
        print("   ✅ Reset successful")
    else:
        print(f"   ❌ Reset failed: {result['error']}")
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80)
    
    return True

if __name__ == "__main__":
    print("Starting V7 API tests...")
    print("Make sure web_demo_v2.py is running on http://localhost:5000")
    print()
    
    # Wait a moment for user to start server
    time.sleep(2)
    
    success = run_tests()
    
    if not success:
        print("\n⚠️  Some tests failed. Check the output above.")
        sys.exit(1)
    else:
        print("\n✅ All tests completed!")

