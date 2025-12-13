#!/usr/bin/env python3
"""Quick test script to verify demo endpoint integration."""

import asyncio
import httpx
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

async def test_demo_endpoint():
    """Test posting to the demo endpoint."""
    
    email = os.getenv("STUDENT_EMAIL")
    secret = os.getenv("STUDENT_SECRET")
    submit_url = os.getenv("API_ENDPOINT_URL")
    demo_url = "https://tds-llm-analysis.s-anand.net/demo"
    
    print("=" * 80)
    print("Testing Demo Endpoint Integration")
    print("=" * 80)
    print(f"Email: {email}")
    print(f"Submit URL: {submit_url}")
    print(f"Demo URL: {demo_url}")
    print()
    
    # Test 1: Submit a test answer
    print("Test 1: Submitting test answer to demo endpoint...")
    
    payload = {
        "email": email,
        "secret": secret,
        "url": demo_url,
        "answer": "test answer"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(submit_url, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Success!")
                print(f"  - Correct: {data.get('correct')}")
                print(f"  - Reason: {data.get('reason')}")
                print(f"  - Next URL: {data.get('url')}")
            else:
                print(f"✗ Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_demo_endpoint())
