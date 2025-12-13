"""Tests for the error handler module."""

import pytest
import asyncio
from src.error_handler import (
    ErrorHandler,
    ErrorCategory,
    QuizSystemError,
    AuthenticationError,
    ValidationError,
    TimeoutError,
    BrowserError,
    NetworkError,
    LLMAPIError,
    DataProcessingError,
    TaskExecutionError,
    error_handler
)


class TestErrorClassification:
    """Test error classification functionality."""
    
    def test_classify_quiz_system_errors(self):
        """Test classification of QuizSystemError subclasses."""
        handler = ErrorHandler()
        
        assert handler.classify_error(AuthenticationError()) == ErrorCategory.AUTHENTICATION
        assert handler.classify_error(ValidationError()) == ErrorCategory.VALIDATION
        assert handler.classify_error(TimeoutError()) == ErrorCategory.TIMEOUT
        assert handler.classify_error(BrowserError()) == ErrorCategory.BROWSER
        assert handler.classify_error(NetworkError()) == ErrorCategory.NETWORK
        assert handler.classify_error(LLMAPIError()) == ErrorCategory.LLM_API
        assert handler.classify_error(DataProcessingError()) == ErrorCategory.DATA_PROCESSING
        assert handler.classify_error(TaskExecutionError()) == ErrorCategory.TASK_EXECUTION
    
    def test_classify_standard_errors(self):
        """Test classification of standard Python exceptions."""
        handler = ErrorHandler()
        
        # Timeout errors
        assert handler.classify_error(asyncio.TimeoutError()) == ErrorCategory.TIMEOUT
        
        # Unknown errors
        assert handler.classify_error(ValueError("test")) == ErrorCategory.UNKNOWN
        assert handler.classify_error(RuntimeError("test")) == ErrorCategory.UNKNOWN
    
    def test_classify_by_message(self):
        """Test classification based on error message."""
        handler = ErrorHandler()
        
        # Authentication
        assert handler.classify_error(Exception("403 Forbidden")) == ErrorCategory.AUTHENTICATION
        assert handler.classify_error(Exception("unauthorized access")) == ErrorCategory.AUTHENTICATION
        
        # Validation
        assert handler.classify_error(Exception("400 Bad Request")) == ErrorCategory.VALIDATION
        assert handler.classify_error(Exception("validation failed")) == ErrorCategory.VALIDATION
        
        # Timeout
        assert handler.classify_error(Exception("timeout occurred")) == ErrorCategory.TIMEOUT


class TestRetryability:
    """Test retry logic determination."""
    
    def test_non_retryable_errors(self):
        """Test that authentication and validation errors are not retryable."""
        handler = ErrorHandler()
        
        assert not handler.is_retryable(AuthenticationError())
        assert not handler.is_retryable(ValidationError())
    
    def test_retryable_errors(self):
        """Test that transient errors are retryable."""
        handler = ErrorHandler()
        
        assert handler.is_retryable(TimeoutError())
        assert handler.is_retryable(BrowserError())
        assert handler.is_retryable(NetworkError())
        assert handler.is_retryable(LLMAPIError())
        assert handler.is_retryable(DataProcessingError())
        assert handler.is_retryable(TaskExecutionError())


class TestExponentialBackoff:
    """Test exponential backoff calculation."""
    
    def test_delay_calculation(self):
        """Test that delays increase exponentially."""
        handler = ErrorHandler(base_delay=1.0, exponential_base=2.0, max_delay=30.0)
        
        assert handler.calculate_delay(0) == 1.0
        assert handler.calculate_delay(1) == 2.0
        assert handler.calculate_delay(2) == 4.0
        assert handler.calculate_delay(3) == 8.0
        assert handler.calculate_delay(4) == 16.0
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        handler = ErrorHandler(base_delay=1.0, exponential_base=2.0, max_delay=10.0)
        
        assert handler.calculate_delay(10) == 10.0
        assert handler.calculate_delay(100) == 10.0


class TestRetryLogic:
    """Test retry logic with actual function execution."""
    
    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self):
        """Test that successful execution doesn't retry."""
        handler = ErrorHandler(max_retries=3)
        call_count = 0
        
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await handler.with_retry(successful_func)
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self):
        """Test that retryable errors trigger retries."""
        handler = ErrorHandler(max_retries=3, base_delay=0.01)
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Network error")
            return "success"
        
        result = await handler.with_retry(failing_then_success)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self):
        """Test that non-retryable errors don't trigger retries."""
        handler = ErrorHandler(max_retries=3)
        call_count = 0
        
        async def auth_failure():
            nonlocal call_count
            call_count += 1
            raise AuthenticationError("Auth failed")
        
        with pytest.raises(AuthenticationError):
            await handler.with_retry(auth_failure)
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that max retries is respected."""
        handler = ErrorHandler(max_retries=2, base_delay=0.01)
        call_count = 0
        
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Network error")
        
        with pytest.raises(NetworkError):
            await handler.with_retry(always_fails)
        
        # Should be called max_retries + 1 times (initial + retries)
        assert call_count == 3


class TestErrorContext:
    """Test error context and logging."""
    
    def test_error_with_context(self):
        """Test that errors can carry context."""
        error = TaskExecutionError(
            "Task failed",
            context={"task_id": "123", "attempt": 2}
        )
        
        assert error.message == "Task failed"
        assert error.category == ErrorCategory.TASK_EXECUTION
        assert error.context["task_id"] == "123"
        assert error.context["attempt"] == 2
    
    def test_error_with_original_error(self):
        """Test that errors can wrap original exceptions."""
        original = ValueError("Invalid value")
        error = DataProcessingError(
            "Processing failed",
            original_error=original
        )
        
        assert error.original_error is original
        assert isinstance(error.original_error, ValueError)


class TestGlobalErrorHandler:
    """Test the global error handler instance."""
    
    def test_global_instance_exists(self):
        """Test that global error_handler instance is available."""
        assert error_handler is not None
        assert isinstance(error_handler, ErrorHandler)
    
    def test_handle_error_logs(self):
        """Test that handle_error method works."""
        # This should not raise an exception
        error_handler.handle_error(
            NetworkError("Test error"),
            "test_context",
            {"test_key": "test_value"}
        )
