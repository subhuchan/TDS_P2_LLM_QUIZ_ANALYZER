"""Quick test script for the live API."""
import requests
import json

# API endpoint
url = "https://tds-p2-llm-quiz-analyzer-1.onrender.com/quiz"

# Request payload
payload = {
    "email": "23f3003784@ds.study.iitm.ac.in",
    "secret": "subhashree_secret_123",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
}

print("Testing live API...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ Request accepted! Quiz processing started in background.")
        print("Check the Render logs to see the browser automation in action.")
    else:
        print(f"\n❌ Request failed with status {response.status_code}")
        
except requests.exceptions.Timeout:
    print("\n⏱️ Request timed out (this is normal - processing happens in background)")
except Exception as e:
    print(f"\n❌ Error: {e}")
