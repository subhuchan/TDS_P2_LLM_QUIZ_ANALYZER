#!/usr/bin/env python3
"""Final system validation script."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("=" * 80)
print("LLM ANALYSIS QUIZ SYSTEM - FINAL VALIDATION")
print("=" * 80)
print()

# Check 1: Environment Variables
print("✓ Checking environment variables...")
required_vars = [
    "STUDENT_EMAIL",
    "STUDENT_SECRET",
    "API_ENDPOINT_URL",
    "OPENAI_API_KEY"
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if not value:
        missing_vars.append(var)
        print(f"  ✗ {var}: MISSING")
    else:
        # Mask sensitive values
        if "KEY" in var or "SECRET" in var:
            display_value = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display_value = value
        print(f"  ✓ {var}: {display_value}")

if missing_vars:
    print(f"\n✗ Missing required environment variables: {', '.join(missing_vars)}")
    print("  Please update your .env file")
    sys.exit(1)

print()

# Check 2: Required Files
print("✓ Checking required files...")
required_files = [
    "src/main.py",
    "src/api.py",
    "src/config.py",
    "src/quiz_orchestrator.py",
    "src/browser_manager.py",
    "src/task_parser.py",
    "src/llm_agent.py",
    "src/answer_submitter.py",
    "requirements.txt",
    "README.md",
    "LICENSE",
    "render.yaml",
    ".env"
]

missing_files = []
for file in required_files:
    if Path(file).exists():
        print(f"  ✓ {file}")
    else:
        print(f"  ✗ {file}: MISSING")
        missing_files.append(file)

if missing_files:
    print(f"\n✗ Missing required files: {', '.join(missing_files)}")
    sys.exit(1)

print()

# Check 3: Python Dependencies
print("✓ Checking Python dependencies...")
try:
    import fastapi
    print(f"  ✓ fastapi: {fastapi.__version__}")
except ImportError:
    print("  ✗ fastapi: NOT INSTALLED")
    sys.exit(1)

try:
    import playwright
    print(f"  ✓ playwright: installed")
except ImportError:
    print("  ✗ playwright: NOT INSTALLED")
    sys.exit(1)

try:
    import openai
    print(f"  ✓ openai: {openai.__version__}")
except ImportError:
    print("  ✗ openai: NOT INSTALLED")
    sys.exit(1)

try:
    import pandas
    print(f"  ✓ pandas: {pandas.__version__}")
except ImportError:
    print("  ✗ pandas: NOT INSTALLED")
    sys.exit(1)

print()

# Check 4: Import Application Modules
print("✓ Checking application modules...")
try:
    from src.config import settings
    print("  ✓ src.config")
    
    from src.api import app
    print("  ✓ src.api")
    
    from src.quiz_orchestrator import QuizOrchestrator
    print("  ✓ src.quiz_orchestrator")
    
    from src.browser_manager import BrowserManager
    print("  ✓ src.browser_manager")
    
    from src.task_parser import TaskParser
    print("  ✓ src.task_parser")
    
    from src.llm_agent import LLMAgent
    print("  ✓ src.llm_agent")
    
    from src.answer_submitter import AnswerSubmitter
    print("  ✓ src.answer_submitter")
    
    from src.monitoring import get_metrics_collector
    print("  ✓ src.monitoring")
    
except Exception as e:
    print(f"  ✗ Import error: {e}")
    sys.exit(1)

print()

# Check 5: API Endpoints
print("✓ Checking API configuration...")
from src.api import app

routes = [route.path for route in app.routes]
required_routes = ["/quiz", "/health", "/metrics"]

for route in required_routes:
    if route in routes:
        print(f"  ✓ {route}")
    else:
        print(f"  ✗ {route}: MISSING")
        sys.exit(1)

print()

# Check 6: Test Demo Endpoint
print("✓ Testing demo endpoint connection...")
import httpx

async def test_demo():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                os.getenv("API_ENDPOINT_URL"),
                json={
                    "email": os.getenv("STUDENT_EMAIL"),
                    "secret": os.getenv("STUDENT_SECRET"),
                    "url": "https://tds-llm-analysis.s-anand.net/demo",
                    "answer": "test"
                }
            )
            
            if response.status_code == 200:
                print(f"  ✓ Demo endpoint accessible (status: {response.status_code})")
                data = response.json()
                print(f"  ✓ Response: {data}")
                return True
            else:
                print(f"  ✗ Demo endpoint returned status: {response.status_code}")
                print(f"     Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"  ✗ Failed to connect to demo endpoint: {e}")
        return False

demo_success = asyncio.run(test_demo())

print()

# Check 7: Deployment Configuration
print("✓ Checking deployment configuration...")

# Check render.yaml
if Path("render.yaml").exists():
    print("  ✓ render.yaml exists")
    with open("render.yaml") as f:
        content = f.read()
        if "playwright install" in content:
            print("  ✓ Playwright installation configured")
        else:
            print("  ✗ Playwright installation not configured in render.yaml")
else:
    print("  ✗ render.yaml missing")

# Check documentation
docs = ["README.md", "DEPLOYMENT.md", "RENDER_DEPLOYMENT.md", "TROUBLESHOOTING.md"]
for doc in docs:
    if Path(doc).exists():
        print(f"  ✓ {doc}")
    else:
        print(f"  ⚠ {doc} missing (optional)")

print()

# Final Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

if missing_vars or missing_files or not demo_success:
    print("✗ VALIDATION FAILED")
    print()
    print("Issues found:")
    if missing_vars:
        print(f"  - Missing environment variables: {', '.join(missing_vars)}")
    if missing_files:
        print(f"  - Missing files: {', '.join(missing_files)}")
    if not demo_success:
        print("  - Demo endpoint test failed")
    print()
    print("Please fix the issues above and run validation again.")
    sys.exit(1)
else:
    print("✓ ALL CHECKS PASSED")
    print()
    print("Your system is ready for deployment!")
    print()
    print("Next steps:")
    print("  1. Push code to GitHub")
    print("  2. Deploy to Render.com (see RENDER_DEPLOYMENT.md)")
    print("  3. Test your deployed endpoint")
    print("  4. Submit your API URL")
    print()
    print(f"Your API endpoint will be: https://your-service-name.onrender.com/quiz")
    print()
    sys.exit(0)
