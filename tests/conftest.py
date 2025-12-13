"""Pytest configuration and shared fixtures."""

import os
import pytest
from typing import Generator

# Set test environment variables before any imports
os.environ.update({
    "STUDENT_EMAIL": "23f3003784@ds.study.iitm.ac.in",
    "STUDENT_SECRET": "subhashree_secret_123",
    "API_ENDPOINT_URL": "https://tds-llm-analysis.s-anand.net/submit",
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "test-openai-key"),
    "LOG_LEVEL": "DEBUG",
    "LOG_FORMAT": "console",
})


@pytest.fixture(scope="session")
def test_env() -> Generator[None, None, None]:
    """Set up test environment variables."""
    # Environment variables are already set at module level
    yield


@pytest.fixture
def sample_quiz_url() -> str:
    """Provide a sample quiz URL for testing."""
    return "https://tds-llm-analysis.s-anand.net/demo"
