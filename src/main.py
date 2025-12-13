"""Main entry point for the LLM Analysis Quiz System API server."""

import uvicorn
from src.api import app
from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)


def main():
    """Start the FastAPI server."""
    logger.info(
        "starting_server",
        host=settings.api_host,
        port=settings.api_port
    )
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_config=None  # Use our custom logging configuration
    )


if __name__ == "__main__":
    main()
