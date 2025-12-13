"""Answer submission module with retry logic for the LLM Analysis Quiz System."""

import asyncio
import time
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from src.config import settings
from src.logging_config import get_logger
from src.models import SubmitPayload, SubmitResponse
from src.error_handler import (
    error_handler,
    NetworkError,
    ValidationError as QuizValidationError
)

logger = get_logger(__name__)


class AnswerSubmitter:
    """Handles answer submission to quiz endpoints with retry logic."""
    
    def __init__(self, max_retries: Optional[int] = None, timeout: int = 30):
        """
        Initialize the AnswerSubmitter.
        
        Args:
            max_retries: Maximum number of retry attempts (defaults to settings.max_retries)
            timeout: HTTP request timeout in seconds
        """
        self.max_retries = max_retries if max_retries is not None else settings.max_retries
        self.timeout = timeout
        self.submission_times = []
        
    async def submit_answer(
        self,
        submit_url: str,
        email: str,
        secret: str,
        quiz_url: str,
        answer: Any,
        retry_count: int = 0
    ) -> SubmitResponse:
        """
        Submit answer to the specified endpoint with retry logic.
        
        Args:
            submit_url: Endpoint URL to submit the answer to
            email: Student email address
            secret: Authentication secret string
            quiz_url: Original quiz URL
            answer: Computed answer in the required format
            retry_count: Current retry attempt number (internal use)
        
        Returns:
            SubmitResponse with correct flag, reason, and optional next URL
            
        Raises:
            httpx.HTTPError: If submission fails after all retries
            ValidationError: If response cannot be parsed
        """
        start_time = time.time()
        
        try:
            # Construct the payload
            payload = SubmitPayload(
                email=email,
                secret=secret,
                url=quiz_url,
                answer=answer
            )
            
            logger.info(
                "Submitting answer",
                extra={
                    "submit_url": submit_url,
                    "quiz_url": quiz_url,
                    "answer_format": type(answer).__name__,
                    "retry_count": retry_count
                }
            )
            
            # Make the POST request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    submit_url,
                    json=payload.model_dump(mode="json"),
                    headers={"Content-Type": "application/json"}
                )
                
                # Track submission timing
                elapsed_time = time.time() - start_time
                self.submission_times.append(elapsed_time)
                
                logger.info(
                    "Received submission response",
                    extra={
                        "status_code": response.status_code,
                        "elapsed_time": elapsed_time,
                        "retry_count": retry_count
                    }
                )
                
                # Raise for HTTP errors (4xx, 5xx)
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json()
                submit_response = SubmitResponse(**response_data)
                
                logger.info(
                    "Answer submission result",
                    extra={
                        "correct": submit_response.correct,
                        "reason": submit_response.reason,
                        "has_next_url": submit_response.url is not None,
                        "elapsed_time": elapsed_time
                    }
                )
                
                return submit_response
                
        except httpx.HTTPStatusError as e:
            network_error = NetworkError(
                f"HTTP error during submission: {e.response.status_code}",
                original_error=e,
                context={
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "submit_url": submit_url
                }
            )
            error_handler.handle_error(
                network_error,
                "answer_submission_http_error",
                {
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "retry_count": retry_count,
                    "submit_url": submit_url
                }
            )
            logger.error(
                "HTTP error during submission",
                extra={
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "retry_count": retry_count
                }
            )
            
            # Retry on server errors (5xx) if retries are available
            if e.response.status_code >= 500 and retry_count < self.max_retries:
                return await self._retry_submission(
                    submit_url, email, secret, quiz_url, answer, retry_count
                )
            raise network_error
            
        except httpx.RequestError as e:
            network_error = NetworkError(
                f"Network error during submission: {str(e)}",
                original_error=e,
                context={"submit_url": submit_url}
            )
            error_handler.handle_error(
                network_error,
                "answer_submission_network_error",
                {
                    "error": str(e),
                    "retry_count": retry_count,
                    "submit_url": submit_url
                }
            )
            logger.error(
                "Request error during submission",
                extra={
                    "error": str(e),
                    "retry_count": retry_count
                }
            )
            
            # Retry on network errors if retries are available
            if retry_count < self.max_retries:
                return await self._retry_submission(
                    submit_url, email, secret, quiz_url, answer, retry_count
                )
            raise network_error
            
        except ValidationError as e:
            validation_error = QuizValidationError(
                "Failed to parse submission response",
                original_error=e,
                context={"submit_url": submit_url}
            )
            error_handler.handle_error(
                validation_error,
                "answer_submission_validation_error",
                {
                    "error": str(e),
                    "retry_count": retry_count,
                    "submit_url": submit_url
                }
            )
            logger.error(
                "Failed to parse submission response",
                extra={
                    "error": str(e),
                    "retry_count": retry_count
                }
            )
            raise validation_error
            
        except Exception as e:
            error_handler.handle_error(
                e,
                "answer_submission_unexpected_error",
                {
                    "exception_message": str(e),
                    "exception_type": type(e).__name__,
                    "retry_count": retry_count,
                    "submit_url": submit_url
                }
            )
            logger.error(
                "Unexpected error during submission",
                extra={
                    "exception_message": str(e),
                    "exception_type": type(e).__name__,
                    "retry_count": retry_count
                }
            )
            raise
    
    async def _retry_submission(
        self,
        submit_url: str,
        email: str,
        secret: str,
        quiz_url: str,
        answer: Any,
        retry_count: int
    ) -> SubmitResponse:
        """
        Retry submission after a delay.
        
        Args:
            submit_url: Endpoint URL to submit the answer to
            email: Student email address
            secret: Authentication secret string
            quiz_url: Original quiz URL
            answer: Computed answer
            retry_count: Current retry attempt number
            
        Returns:
            SubmitResponse from retry attempt
        """
        retry_count += 1
        delay = min(2 ** retry_count, 10)  # Exponential backoff, max 10 seconds
        
        logger.info(
            "Retrying submission",
            extra={
                "retry_count": retry_count,
                "delay_seconds": delay
            }
        )
        
        await asyncio.sleep(delay)
        
        return await self.submit_answer(
            submit_url, email, secret, quiz_url, answer, retry_count
        )
    
    def get_total_submission_time(self) -> float:
        """
        Get the total time spent on submissions.
        
        Returns:
            Total submission time in seconds
        """
        return sum(self.submission_times)
    
    def get_submission_count(self) -> int:
        """
        Get the number of submissions made.
        
        Returns:
            Number of submissions
        """
        return len(self.submission_times)
    
    def reset_metrics(self) -> None:
        """Reset submission timing metrics."""
        self.submission_times = []
