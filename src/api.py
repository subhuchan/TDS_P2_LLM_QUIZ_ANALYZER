"""FastAPI server with authentication for the LLM Analysis Quiz System."""

import asyncio
from fastapi import FastAPI, Request, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import structlog

from src.models import QuizRequest, QuizResponse
from src.config import settings
from src.logging_config import get_logger
from src.quiz_orchestrator import QuizOrchestrator
from src.error_handler import (
    error_handler,
    AuthenticationError,
    ValidationError as QuizValidationError
)

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="LLM Analysis Quiz System",
    description="Automated quiz solver using LLMs and web automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests."""
    logger.info(
        "incoming_request",
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )
    
    response = await call_next(request)
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    
    return response


def validate_secret(secret: str) -> bool:
    """
    Validate the provided secret against the stored secret.
    
    Args:
        secret: Secret string from request
    
    Returns:
        True if secret is valid, False otherwise
    """
    return secret == settings.student_secret


async def solve_quiz_background(email: str, secret: str, url: str):
    """
    Background task to solve quiz sequence.
    
    This function runs asynchronously in the background after the API
    returns a 200 response to the client.
    
    Args:
        email: Student email address
        secret: Authentication secret string
        url: Initial quiz URL
    """
    try:
        logger.info(
            "background_task_started",
            email=email,
            url=url
        )
        
        # Create orchestrator instance
        orchestrator = QuizOrchestrator(timeout=180)
        
        # Solve quiz sequence
        result = await orchestrator.solve_quiz_sequence(
            email=email,
            secret=secret,
            initial_url=url
        )
        
        # Log final result
        logger.info(
            "background_task_completed",
            email=email,
            success=result.success,
            total_time=result.total_time,
            quizzes_solved=result.quizzes_solved,
            final_status=result.final_status,
            error=result.error
        )
        
    except Exception as e:
        logger.error(
            "background_task_failed",
            email=email,
            url=url,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )


@app.post("/quiz", response_model=QuizResponse, status_code=status.HTTP_200_OK)
async def handle_quiz(request: Request, background_tasks: BackgroundTasks) -> QuizResponse:
    """
    Handle incoming quiz requests.
    
    Validates the request payload and authentication secret, then spawns
    an async background task to solve the quiz. Returns immediately with
    200 status after validation.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks manager
    
    Returns:
        QuizResponse with status and message
    
    Raises:
        HTTPException: 400 for invalid JSON, 403 for invalid secret
    """
    try:
        # Parse request body
        body = await request.json()
        
    except Exception as e:
        error_handler.handle_error(e, "json_parsing", {"path": request.url.path})
        logger.error("invalid_json", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    try:
        # Validate request using Pydantic model
        quiz_request = QuizRequest(**body)
        
    except ValidationError as e:
        error_handler.handle_error(
            QuizValidationError("Request validation failed", original_error=e),
            "request_validation",
            {"errors": e.errors()}
        )
        logger.error("validation_error", errors=e.errors())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Validate secret
    if not validate_secret(quiz_request.secret):
        auth_error = AuthenticationError(
            "Invalid secret provided",
            context={"email": quiz_request.email, "url": str(quiz_request.url)}
        )
        error_handler.handle_error(auth_error, "authentication", {"email": quiz_request.email})
        logger.warning(
            "authentication_failed",
            email=quiz_request.email,
            url=str(quiz_request.url)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret"
        )
    
    # Log successful authentication
    logger.info(
        "quiz_request_authenticated",
        email=quiz_request.email,
        url=str(quiz_request.url)
    )
    
    # Spawn background task to solve quiz
    background_tasks.add_task(
        solve_quiz_background,
        email=quiz_request.email,
        secret=quiz_request.secret,
        url=str(quiz_request.url)
    )
    
    logger.info(
        "background_task_spawned",
        email=quiz_request.email,
        url=str(quiz_request.url)
    )
    
    # Return immediate 200 response
    return QuizResponse(
        status="accepted",
        message="Quiz request received and is being processed"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/metrics")
async def get_metrics():
    """
    Get system metrics and statistics.
    
    Returns:
        Dict with system metrics including:
        - Total requests and success rate
        - Quiz solving times
        - LLM usage and costs
        - Recent quiz attempts
    """
    from src.monitoring import get_metrics_collector
    
    collector = get_metrics_collector()
    metrics = collector.get_metrics()
    
    logger.info("metrics_requested")
    
    return metrics


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for HTTP exceptions."""
    logger.error(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors."""
    logger.error(
        "unexpected_error",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"}
    )
