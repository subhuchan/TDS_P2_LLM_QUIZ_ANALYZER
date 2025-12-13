# Error Handling Documentation

## Overview

The LLM Analysis Quiz System implements comprehensive error handling with automatic retry logic, error classification, and detailed logging. The error handling system is designed to gracefully handle transient failures while failing fast on non-recoverable errors.

## Error Categories

The system classifies errors into the following categories:

### 1. Authentication Errors (403)
- **Category**: `ErrorCategory.AUTHENTICATION`
- **Retryable**: No
- **Examples**: Invalid secret, missing credentials
- **Handling**: Immediate failure with 403 HTTP status

### 2. Validation Errors (400)
- **Category**: `ErrorCategory.VALIDATION`
- **Retryable**: No
- **Examples**: Malformed JSON, missing required fields, invalid data types
- **Handling**: Immediate failure with 400 HTTP status

### 3. Timeout Errors
- **Category**: `ErrorCategory.TIMEOUT`
- **Retryable**: Yes
- **Examples**: Page load timeout, operation timeout, quiz sequence timeout
- **Handling**: Retry with exponential backoff

### 4. Browser Errors
- **Category**: `ErrorCategory.BROWSER`
- **Retryable**: Yes
- **Examples**: Browser launch failure, page rendering failure, JavaScript execution error
- **Handling**: Retry with browser cleanup and relaunch

### 5. Network Errors
- **Category**: `ErrorCategory.NETWORK`
- **Retryable**: Yes
- **Examples**: HTTP errors (5xx), connection failures, request timeouts
- **Handling**: Retry with exponential backoff

### 6. LLM API Errors
- **Category**: `ErrorCategory.LLM_API`
- **Retryable**: Yes
- **Examples**: Rate limit errors, API timeouts, temporary API failures
- **Handling**: Retry with exponential backoff

### 7. Data Processing Errors
- **Category**: `ErrorCategory.DATA_PROCESSING`
- **Retryable**: Yes
- **Examples**: PDF parsing failure, CSV parsing error, JSON decode error
- **Handling**: Retry with exponential backoff

### 8. Task Execution Errors
- **Category**: `ErrorCategory.TASK_EXECUTION`
- **Retryable**: Yes
- **Examples**: Task solving failure, tool execution error
- **Handling**: Retry with exponential backoff

## Error Classes

### Base Error Class

```python
class QuizSystemError(Exception):
    """Base exception for quiz system errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        original_error: Optional[Exception] = None,
        context: Optional[dict] = None
    ):
        # Stores error message, category, original exception, and context
```

### Specific Error Classes

- `AuthenticationError`: For authentication failures
- `ValidationError`: For validation failures
- `TimeoutError`: For timeout scenarios
- `BrowserError`: For browser-related failures
- `NetworkError`: For network-related failures
- `LLMAPIError`: For LLM API failures
- `DataProcessingError`: For data processing failures
- `TaskExecutionError`: For task execution failures

## ErrorHandler Class

The `ErrorHandler` class provides centralized error handling with retry logic.

### Configuration

```python
error_handler = ErrorHandler(
    max_retries=3,           # Maximum number of retry attempts
    base_delay=1.0,          # Base delay in seconds
    max_delay=30.0,          # Maximum delay between retries
    exponential_base=2.0     # Base for exponential backoff
)
```

### Retry Logic

The error handler uses exponential backoff for retries:

- Attempt 1: 1 second delay
- Attempt 2: 2 seconds delay
- Attempt 3: 4 seconds delay
- Attempt 4: 8 seconds delay
- And so on, capped at `max_delay`

### Usage Examples

#### Using with_retry Method

```python
from src.error_handler import error_handler

async def risky_operation():
    # Operation that might fail
    pass

# Automatically retry on retryable errors
result = await error_handler.with_retry(
    risky_operation,
    max_retries=3,
    context={"operation": "data_fetch"}
)
```

#### Using Decorator

```python
from src.error_handler import error_handler

@error_handler.wrap_with_error_handling(max_retries=3)
async def fetch_data(url: str):
    # Operation that might fail
    pass
```

#### Manual Error Handling

```python
from src.error_handler import error_handler, NetworkError

try:
    # Risky operation
    result = await fetch_data()
except Exception as e:
    error_handler.handle_error(
        e,
        context="data_fetching",
        additional_context={"url": url}
    )
    raise
```

## Integration Points

### API Layer (src/api.py)

- Validates JSON payloads and raises `ValidationError` on failure
- Validates authentication and raises `AuthenticationError` on failure
- Logs all errors with comprehensive context

### Browser Manager (src/browser_manager.py)

- Wraps browser operations with error handling
- Retries on `PlaywrightTimeoutError` and browser failures
- Cleans up browser resources on failure

### Quiz Orchestrator (src/quiz_orchestrator.py)

- Handles timeout errors for quiz sequences
- Wraps task execution with error handling
- Provides detailed error context for debugging

### Answer Submitter (src/answer_submitter.py)

- Retries on network errors (5xx status codes)
- Handles validation errors for response parsing
- Tracks submission timing even on failures

## Logging

All errors are logged with structured logging including:

- Error message and type
- Error category
- Whether the error is retryable
- Retry attempt number
- Additional context (URLs, parameters, etc.)
- Original exception details

### Log Format

```json
{
  "event": "error_handled",
  "context": "quiz_solving",
  "error": "Network timeout",
  "error_type": "NetworkError",
  "category": "network",
  "retryable": true,
  "attempt": 2,
  "max_retries": 3,
  "url": "https://example.com/quiz"
}
```

## Best Practices

### 1. Use Specific Error Types

```python
# Good
raise AuthenticationError("Invalid secret provided")

# Avoid
raise Exception("Auth failed")
```

### 2. Provide Context

```python
# Good
raise NetworkError(
    "Failed to fetch data",
    context={"url": url, "status_code": 500}
)

# Avoid
raise NetworkError("Failed to fetch data")
```

### 3. Wrap Original Exceptions

```python
# Good
try:
    result = parse_json(data)
except json.JSONDecodeError as e:
    raise DataProcessingError(
        "JSON parsing failed",
        original_error=e
    )

# Avoid
try:
    result = parse_json(data)
except json.JSONDecodeError:
    raise DataProcessingError("JSON parsing failed")
```

### 4. Let ErrorHandler Manage Retries

```python
# Good
result = await error_handler.with_retry(fetch_data, url=url)

# Avoid (manual retry logic)
for attempt in range(3):
    try:
        result = await fetch_data(url)
        break
    except Exception:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)
```

## Testing

The error handling system includes comprehensive tests:

- Error classification tests
- Retry logic tests
- Exponential backoff tests
- Integration tests with actual components

Run tests with:

```bash
pytest tests/test_error_handler.py -v
```

## Monitoring

All errors are logged with structured logging, making it easy to:

- Track error rates by category
- Monitor retry success rates
- Identify problematic operations
- Debug failures with full context

## Future Enhancements

Potential improvements to the error handling system:

1. **Circuit Breaker Pattern**: Temporarily disable failing operations
2. **Error Metrics**: Track error rates and patterns
3. **Alerting**: Send notifications for critical errors
4. **Custom Retry Strategies**: Per-operation retry configuration
5. **Error Recovery**: Automatic recovery strategies for specific errors
