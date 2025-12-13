"""Comprehensive error handling module with retry logic and logging."""

import asyncio
import functools
from typing import Any, Callable, Optional, Type, TypeVar, Union
from enum import Enum

from src.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class ErrorCategory(str, Enum):
    """Categories of errors for classification and handling."""
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    BROWSER = "browser"
    NETWORK = "network"
    LLM_API = "llm_api"
    DATA_PROCESSING = "data_processing"
    TASK_EXECUTION = "task_execution"
    UNKNOWN = "unknown"


class QuizSystemError(Exception):
    """Base exception for quiz system errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        original_error: Optional[Exception] = None,
        context: Optional[dict] = None
    ):
        """
        Initialize quiz system error.
        
        Args:
            message: Error message
            category: Error category for classification
            original_error: Original exception that caused this error
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.original_error = original_error
        self.context = context or {}


class AuthenticationError(QuizSystemError):
    """Error for authentication failures (403)."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, category=ErrorCategory.AUTHENTICATION, **kwargs)


class ValidationError(QuizSystemError):
    """Error for validation failures (400)."""
    
    def __init__(self, message: str = "Validation failed", **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)


class TimeoutError(QuizSystemError):
    """Error for timeout scenarios."""
    
    def __init__(self, message: str = "Operation timed out", **kwargs):
        super().__init__(message, category=ErrorCategory.TIMEOUT, **kwargs)


class BrowserError(QuizSystemError):
    """Error for browser-related failures."""
    
    def __init__(self, message: str = "Browser operation failed", **kwargs):
        super().__init__(message, category=ErrorCategory.BROWSER, **kwargs)


class NetworkError(QuizSystemError):
    """Error for network-related failures."""
    
    def __init__(self, message: str = "Network operation failed", **kwargs):
        super().__init__(message, category=ErrorCategory.NETWORK, **kwargs)


class LLMAPIError(QuizSystemError):
    """Error for LLM API failures."""
    
    def __init__(self, message: str = "LLM API operation failed", **kwargs):
        super().__init__(message, category=ErrorCategory.LLM_API, **kwargs)


class DataProcessingError(QuizSystemError):
    """Error for data processing failures."""
    
    def __init__(self, message: str = "Data processing failed", **kwargs):
        super().__init__(message, category=ErrorCategory.DATA_PROCESSING, **kwargs)


class TaskExecutionError(QuizSystemError):
    """Error for task execution failures."""
    
    def __init__(self, message: str = "Task execution failed", **kwargs):
        super().__init__(message, category=ErrorCategory.TASK_EXECUTION, **kwargs)


class ErrorHandler:
    """
    Comprehensive error handler with retry logic and logging.
    
    Provides utilities for handling different error categories with
    appropriate retry strategies and logging.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0
    ):
        """
        Initialize error handler.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for retries
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt using exponential backoff.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)
    
    def classify_error(self, error: Exception) -> ErrorCategory:
        """
        Classify an error into a category.
        
        Args:
            error: Exception to classify
        
        Returns:
            ErrorCategory for the error
        """
        # Check if it's already a QuizSystemError
        if isinstance(error, QuizSystemError):
            return error.category
        
        # Classify based on error type and message
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # Authentication errors
        if "403" in error_msg or "forbidden" in error_msg or "unauthorized" in error_msg:
            return ErrorCategory.AUTHENTICATION
        
        # Validation errors
        if "400" in error_msg or "validation" in error_msg or "invalid" in error_msg:
            return ErrorCategory.VALIDATION
        
        # Timeout errors
        if "timeout" in error_type.lower() or "timeout" in error_msg:
            return ErrorCategory.TIMEOUT
        
        # Browser errors
        if "playwright" in error_type.lower() or "browser" in error_msg:
            return ErrorCategory.BROWSER
        
        # Network errors
        if any(keyword in error_type.lower() for keyword in ["http", "connection", "network"]):
            return ErrorCategory.NETWORK
        
        # LLM API errors
        if any(keyword in error_type.lower() for keyword in ["openai", "ratelimit", "api"]):
            return ErrorCategory.LLM_API
        
        # Data processing errors
        if any(keyword in error_type.lower() for keyword in ["parse", "decode", "json", "csv", "pdf"]):
            return ErrorCategory.DATA_PROCESSING
        
        return ErrorCategory.UNKNOWN
    
    def is_retryable(self, error: Exception, category: Optional[ErrorCategory] = None) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: Exception to check
            category: Optional error category (will be classified if not provided)
        
        Returns:
            True if error should be retried, False otherwise
        """
        if category is None:
            category = self.classify_error(error)
        
        # Non-retryable categories
        non_retryable = {
            ErrorCategory.AUTHENTICATION,  # Auth failures won't fix themselves
            ErrorCategory.VALIDATION,      # Validation errors need code fixes
        }
        
        if category in non_retryable:
            return False
        
        # Retryable categories
        retryable = {
            ErrorCategory.TIMEOUT,
            ErrorCategory.BROWSER,
            ErrorCategory.NETWORK,
            ErrorCategory.LLM_API,
            ErrorCategory.DATA_PROCESSING,
            ErrorCategory.TASK_EXECUTION,
        }
        
        return category in retryable
    
    async def with_retry(
        self,
        func: Callable[..., T],
        *args,
        max_retries: Optional[int] = None,
        retry_on: Optional[tuple] = None,
        context: Optional[dict] = None,
        **kwargs
    ) -> T:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute (can be sync or async)
            *args: Positional arguments for the function
            max_retries: Maximum retry attempts (defaults to self.max_retries)
            retry_on: Tuple of exception types to retry on (defaults to all retryable)
            context: Additional context for logging
            **kwargs: Keyword arguments for the function
        
        Returns:
            Result from successful function execution
        
        Raises:
            Exception: Last exception if all retries fail
        """
        max_retries = max_retries if max_retries is not None else self.max_retries
        context = context or {}
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Execute function (handle both sync and async)
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success
                if attempt > 0:
                    logger.info(
                        "retry_succeeded",
                        function=func.__name__,
                        attempt=attempt + 1,
                        **context
                    )
                
                return result
            
            except Exception as e:
                last_error = e
                category = self.classify_error(e)
                
                # Check if we should retry
                if retry_on and not isinstance(e, retry_on):
                    # Not in retry_on list, don't retry
                    logger.error(
                        "error_not_retryable_type",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                        category=category.value,
                        **context
                    )
                    raise
                
                if not self.is_retryable(e, category):
                    # Error category is not retryable
                    logger.error(
                        "error_not_retryable_category",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                        category=category.value,
                        **context
                    )
                    raise
                
                # Check if we have retries left
                if attempt >= max_retries:
                    logger.error(
                        "max_retries_exceeded",
                        function=func.__name__,
                        error=str(e),
                        error_type=type(e).__name__,
                        category=category.value,
                        attempts=attempt + 1,
                        **context
                    )
                    raise
                
                # Calculate delay and retry
                delay = self.calculate_delay(attempt)
                
                logger.warning(
                    "retrying_after_error",
                    function=func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                    category=category.value,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=delay,
                    **context
                )
                
                await asyncio.sleep(delay)
        
        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in retry logic")
    
    def handle_error(
        self,
        error: Exception,
        context: str,
        additional_context: Optional[dict] = None
    ) -> None:
        """
        Log error with comprehensive context.
        
        Args:
            error: Exception to log
            context: Context description (e.g., "quiz_solving", "file_download")
            additional_context: Additional context information
        """
        category = self.classify_error(error)
        additional_context = additional_context or {}
        
        logger.error(
            "error_handled",
            context=context,
            error=str(error),
            error_type=type(error).__name__,
            category=category.value,
            retryable=self.is_retryable(error, category),
            **additional_context
        )
    
    def wrap_with_error_handling(
        self,
        max_retries: Optional[int] = None,
        retry_on: Optional[tuple] = None,
        context: Optional[dict] = None
    ):
        """
        Decorator to wrap functions with error handling and retry logic.
        
        Args:
            max_retries: Maximum retry attempts
            retry_on: Tuple of exception types to retry on
            context: Additional context for logging
        
        Returns:
            Decorator function
        
        Example:
            @error_handler.wrap_with_error_handling(max_retries=3)
            async def my_function():
                # function code
                pass
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await self.with_retry(
                    func,
                    *args,
                    max_retries=max_retries,
                    retry_on=retry_on,
                    context=context or {"function": func.__name__},
                    **kwargs
                )
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we need to run in event loop
                return asyncio.run(
                    self.with_retry(
                        func,
                        *args,
                        max_retries=max_retries,
                        retry_on=retry_on,
                        context=context or {"function": func.__name__},
                        **kwargs
                    )
                )
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Global error handler instance
error_handler = ErrorHandler()
