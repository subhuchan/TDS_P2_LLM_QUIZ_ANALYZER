"""Comprehensive deployment test script."""
import requests
import json
import time

BASE_URL = "https://tds-p2-llm-quiz-analyzer-1.onrender.com"

def test_health():
    """Test the health endpoint."""
    print("=" * 60)
    print("1. Testing Health Endpoint")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_quiz_submission():
    """Test quiz submission."""
    print("\n" + "=" * 60)
    print("2. Testing Quiz Submission")
    print("=" * 60)
    
    payload = {
        "email": "23f3003784@ds.study.iitm.ac.in",
        "secret": "subhashree_secret_123",
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(f"{BASE_URL}/quiz", json=payload, timeout=10)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ Quiz submission accepted!")
            print("📝 The quiz is being processed in the background.")
            print("🔍 Check Render logs for detailed execution:")
            print("   - Browser launch")
            print("   - Page rendering")
            print("   - Content extraction")
            print("   - Task parsing")
            print("   - Answer generation")
            print("   - Submission")
            return True
        else:
            print(f"\n❌ Quiz submission failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_invalid_secret():
    """Test with invalid secret."""
    print("\n" + "=" * 60)
    print("3. Testing Invalid Secret (Should Fail)")
    print("=" * 60)
    
    payload = {
        "email": "23f3003784@ds.study.iitm.ac.in",
        "secret": "wrong-secret",
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz", json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 403:
            print("✅ Correctly rejected invalid secret")
            return True
        else:
            print("❌ Should have rejected invalid secret")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "🚀" * 30)
    print("DEPLOYMENT TEST SUITE")
    print("🚀" * 30 + "\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    time.sleep(1)
    
    # Test 2: Valid quiz submission
    results.append(("Quiz Submission", test_quiz_submission()))
    time.sleep(1)
    
    # Test 3: Invalid secret
    results.append(("Security Check", test_invalid_secret()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Deployment is working correctly.")
        print("\n📋 Next Steps:")
        print("   1. Monitor Render logs for the quiz processing")
        print("   2. Look for 'Browser launched successfully'")
        print("   3. Look for 'Task parsed' with submit_url")
        print("   4. Look for 'Answer submitted successfully'")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
