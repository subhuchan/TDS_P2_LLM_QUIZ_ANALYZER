"""Quick test to verify deployment is working."""
import requests
import json
import time

BASE_URL = "https://tds-p2-llm-quiz-analyzer-1.onrender.com"

print("🧪 Quick Deployment Test\n")

# Test 1: Health
print("1️⃣ Health Check...", end=" ")
try:
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    if r.status_code == 200:
        print("✅ PASS")
    else:
        print(f"❌ FAIL ({r.status_code})")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 2: Quiz submission
print("2️⃣ Quiz Submission...", end=" ")
try:
    payload = {
        "email": "23f3003784@ds.study.iitm.ac.in",
        "secret": "subhashree_secret_123",
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
    r = requests.post(f"{BASE_URL}/quiz", json=payload, timeout=5)
    if r.status_code == 200:
        print("✅ PASS")
        print("   📝 Quiz processing started in background")
    else:
        print(f"❌ FAIL ({r.status_code})")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test 3: Invalid secret
print("3️⃣ Security Check...", end=" ")
try:
    payload = {
        "email": "23f3003784@ds.study.iitm.ac.in",
        "secret": "wrong-secret",
        "url": "https://tds-llm-analysis.s-anand.net/demo"
    }
    r = requests.post(f"{BASE_URL}/quiz", json=payload, timeout=5)
    if r.status_code == 403:
        print("✅ PASS")
    else:
        print(f"❌ FAIL (expected 403, got {r.status_code})")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n✨ All basic tests completed!")
print("📊 Check Render logs for detailed quiz processing")
