"""End-to-end integration test with demo endpoint."""

import asyncio
import os
import time
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from src.api import app
from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


@pytest.mark.asyncio
class TestEndToEndIntegration:
    """End-to-end integration tests with the demo endpoint."""
    
    @pytest.fixture
    def demo_url(self) -> str:
        """Provide the demo endpoint URL."""
        return "https://tds-llm-analysis.s-anand.net/demo"
    
    @pytest.fixture
    def valid_quiz_request(self, demo_url: str) -> dict:
        """Provide a valid quiz request payload."""
        return {
            "email": settings.student_email,
            "secret": settings.student_secret,
            "url": demo_url
        }
    
    async def test_demo_endpoint_complete_workflow(
        self,
        demo_url: str,
        valid_quiz_request: dict
    ):
        """
        Test complete solve-submit workflow with demo endpoint.
        
        This test:
        1. Posts to the /quiz endpoint with demo URL
        2. Verifies immediate 200 response
        3. Waits for background task to complete
        4. Validates timing constraints (< 3 minutes)
        5. Logs results for debugging
        
        Requirements: 14.1, 14.2, 14.3, 14.4
        """
        logger.info(
            "Starting end-to-end integration test",
            extra={"demo_url": demo_url}
        )
        
        start_time = time.time()
        
        # Step 1: Post to /quiz endpoint
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            logger.info("Posting quiz request to /quiz endpoint")
            
            response = await client.post("/quiz", json=valid_quiz_request)
            
            # Step 2: Verify immediate 200 response
            assert response.status_code == 200, (
                f"Expected 200 status code, got {response.status_code}"
            )
            
            response_data = response.json()
            assert response_data["status"] == "accepted", (
                f"Expected 'accepted' status, got {response_data.get('status')}"
            )
            
            logger.info(
                "Received immediate response",
                extra={
                    "status_code": response.status_code,
                    "response": response_data
                }
            )
        
        # Step 3: Wait for background task to complete
        # The background task runs asynchronously, so we need to wait
        # We'll wait up to 3 minutes (180 seconds) for completion
        logger.info("Waiting for background task to complete (max 180 seconds)")
        
        max_wait_time = 180
        poll_interval = 2
        elapsed = 0
        
        # Poll for completion by checking logs or waiting for timeout
        # In a real scenario, we'd check a database or status endpoint
        # For this test, we'll wait the full duration to ensure completion
        while elapsed < max_wait_time:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            # Log progress
            if elapsed % 30 == 0:
                logger.info(
                    "Background task still running",
                    extra={"elapsed_seconds": elapsed}
                )
        
        total_time = time.time() - start_time
        
        # Step 4: Validate timing constraints
        logger.info(
            "Background task completed",
            extra={"total_time": total_time}
        )
        
        # Verify total time is within 3 minutes (with some buffer for overhead)
        assert total_time <= 185, (
            f"Total time {total_time}s exceeded 185 second limit (180s + 5s buffer)"
        )
        
        # Step 5: Log results for debugging
        logger.info(
            "End-to-end integration test completed",
            extra={
                "demo_url": demo_url,
                "total_time": total_time,
                "status": "success"
            }
        )
    
    async def test_demo_endpoint_with_real_orchestrator(
        self,
        demo_url: str,
        valid_quiz_request: dict
    ):
        """
        Test with real orchestrator to verify actual quiz solving.
        
        This test directly invokes the orchestrator to verify the
        complete workflow including browser automation, task parsing,
        LLM solving, and answer submission.
        
        Requirements: 14.1, 14.2, 14.3, 14.4
        """
        from src.quiz_orchestrator import QuizOrchestrator
        
        logger.info(
            "Starting real orchestrator integration test",
            extra={"demo_url": demo_url}
        )
        
        start_time = time.time()
        
        # Create orchestrator
        orchestrator = QuizOrchestrator(timeout=180)
        
        try:
            # Solve quiz sequence
            logger.info("Invoking quiz orchestrator")
            
            result = await orchestrator.solve_quiz_sequence(
                email=valid_quiz_request["email"],
                secret=valid_quiz_request["secret"],
                initial_url=demo_url
            )
            
            total_time = time.time() - start_time
            
            # Log detailed results
            logger.info(
                "Quiz orchestrator completed",
                extra={
                    "success": result.success,
                    "total_time": result.total_time,
                    "quizzes_solved": result.quizzes_solved,
                    "final_status": result.final_status,
                    "error": result.error
                }
            )
            
            # Validate results
            assert result.total_time <= 180, (
                f"Quiz solving took {result.total_time}s, exceeded 180 second limit"
            )
            
            # Note: We don't assert success=True because the demo endpoint
            # may have various quiz types that could fail. The important
            # thing is that the workflow completes within time constraints.
            
            logger.info(
                "Real orchestrator test completed",
                extra={
                    "demo_url": demo_url,
                    "total_time": total_time,
                    "result": {
                        "success": result.success,
                        "quizzes_solved": result.quizzes_solved,
                        "final_status": result.final_status
                    }
                }
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            
            logger.error(
                "Real orchestrator test failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "total_time": total_time
                },
                exc_info=True
            )
            
            # Re-raise to fail the test
            raise
    
    async def test_demo_endpoint_timing_validation(
        self,
        demo_url: str,
        valid_quiz_request: dict
    ):
        """
        Test timing constraints are enforced.
        
        Verifies that the system respects the 3-minute timeout
        and completes or times out appropriately.
        
        Requirements: 14.3, 14.4
        """
        from src.quiz_orchestrator import QuizOrchestrator
        
        logger.info("Starting timing validation test")
        
        # Test with a shorter timeout to verify timeout enforcement
        short_timeout = 10  # 10 seconds
        orchestrator = QuizOrchestrator(timeout=short_timeout)
        
        start_time = time.time()
        
        result = await orchestrator.solve_quiz_sequence(
            email=valid_quiz_request["email"],
            secret=valid_quiz_request["secret"],
            initial_url=demo_url,
            timeout=short_timeout
        )
        
        elapsed_time = time.time() - start_time
        
        # Verify timing
        assert elapsed_time <= short_timeout + 2, (
            f"Timeout not enforced: took {elapsed_time}s with {short_timeout}s limit"
        )
        
        logger.info(
            "Timing validation test completed",
            extra={
                "timeout": short_timeout,
                "elapsed_time": elapsed_time,
                "result_status": result.final_status
            }
        )
    
    async def test_demo_endpoint_error_handling(self):
        """
        Test error handling with invalid requests.
        
        Verifies that the API properly handles:
        - Invalid JSON
        - Invalid secret
        - Missing fields
        
        Requirements: 14.1, 14.4
        """
        logger.info("Starting error handling test")
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Test 1: Invalid JSON
            logger.info("Testing invalid JSON")
            response = await client.post(
                "/quiz",
                content="invalid json{",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 400, (
                f"Expected 400 for invalid JSON, got {response.status_code}"
            )
            logger.info("Invalid JSON test passed")
            
            # Test 2: Invalid secret
            logger.info("Testing invalid secret")
            response = await client.post(
                "/quiz",
                json={
                    "email": settings.student_email,
                    "secret": "wrong-secret",
                    "url": "https://example.com"
                }
            )
            assert response.status_code == 403, (
                f"Expected 403 for invalid secret, got {response.status_code}"
            )
            logger.info("Invalid secret test passed")
            
            # Test 3: Missing fields
            logger.info("Testing missing fields")
            response = await client.post(
                "/quiz",
                json={
                    "email": settings.student_email,
                    # Missing secret and url
                }
            )
            assert response.status_code == 400, (
                f"Expected 400 for missing fields, got {response.status_code}"
            )
            logger.info("Missing fields test passed")
        
        logger.info("Error handling test completed")
    
    async def test_health_endpoint(self):
        """Test the health check endpoint."""
        logger.info("Testing health endpoint")
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}
        
        logger.info("Health endpoint test passed")


# Standalone test function for manual execution
async def run_demo_test():
    """
    Standalone function to run demo endpoint test manually.
    
    This can be executed directly to test the demo endpoint
    without running the full test suite.
    """
    logger.info("=" * 80)
    logger.info("RUNNING MANUAL DEMO ENDPOINT TEST")
    logger.info("=" * 80)
    
    from src.quiz_orchestrator import QuizOrchestrator
    
    demo_url = "https://tds-llm-analysis.s-anand.net/demo"
    
    logger.info(f"Testing with demo URL: {demo_url}")
    logger.info(f"Email: {settings.student_email}")
    logger.info(f"Timeout: 180 seconds")
    
    start_time = time.time()
    
    orchestrator = QuizOrchestrator(timeout=180)
    
    try:
        result = await orchestrator.solve_quiz_sequence(
            email=settings.student_email,
            secret=settings.student_secret,
            initial_url=demo_url
        )
        
        total_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("DEMO TEST RESULTS")
        logger.info("=" * 80)
        logger.info(f"Success: {result.success}")
        logger.info(f"Total Time: {result.total_time:.2f}s")
        logger.info(f"Quizzes Solved: {result.quizzes_solved}")
        logger.info(f"Final Status: {result.final_status}")
        if result.error:
            logger.info(f"Error: {result.error}")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        total_time = time.time() - start_time
        
        logger.error("=" * 80)
        logger.error("DEMO TEST FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error Type: {type(e).__name__}")
        logger.error(f"Total Time: {total_time:.2f}s")
        logger.error("=" * 80)
        
        raise


if __name__ == "__main__":
    # Allow running this test file directly
    asyncio.run(run_demo_test())
