"""Quiz orchestrator for managing quiz solving sequences with timing control."""

import asyncio
import time
from typing import Any, Dict, List, Optional

from src.browser_manager import BrowserManager
from src.task_parser import TaskParser
from src.llm_agent import LLMAgent
from src.answer_submitter import AnswerSubmitter
from src.models import QuizResult
from src.logging_config import get_logger
from src.monitoring import get_metrics_collector
from src.error_handler import (
    error_handler,
    TimeoutError as QuizTimeoutError,
    TaskExecutionError,
    BrowserError
)

logger = get_logger(__name__)
metrics_collector = get_metrics_collector()


class QuizOrchestrator:
    """
    Orchestrates the complete quiz solving sequence with timing control.
    
    Manages the 3-minute timeout, coordinates the solve-submit-retry loop,
    and handles quiz sequences with multiple URLs.
    """
    
    def __init__(
        self,
        timeout: int = 180,
        max_retries_per_quiz: int = 2
    ):
        """
        Initialize the quiz orchestrator.
        
        Args:
            timeout: Maximum time in seconds for entire quiz sequence (default 180)
            max_retries_per_quiz: Maximum retry attempts per quiz (default 2)
        """
        self.timeout = timeout
        self.max_retries_per_quiz = max_retries_per_quiz
        
        # Initialize components
        self.browser_manager = BrowserManager()
        self.task_parser = TaskParser()
        self.llm_agent = LLMAgent()
        self.answer_submitter = AnswerSubmitter()
        
        logger.info(
            "QuizOrchestrator initialized",
            extra={
                "timeout": timeout,
                "max_retries_per_quiz": max_retries_per_quiz
            }
        )
    
    async def solve_quiz_sequence(
        self,
        email: str,
        secret: str,
        initial_url: str,
        timeout: Optional[int] = None
    ) -> QuizResult:
        """
        Orchestrate the complete quiz solving sequence.
        
        Manages the entire workflow:
        1. Fetch and render quiz page
        2. Parse task instructions
        3. Solve task using LLM agent
        4. Submit answer
        5. Handle retry or proceed to next URL
        6. Repeat until sequence complete or timeout
        
        Args:
            email: Student email address
            secret: Authentication secret string
            initial_url: Starting quiz URL
            timeout: Maximum time in seconds (defaults to self.timeout)
        
        Returns:
            QuizResult with completion status, timing, and results
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        
        # Start metrics tracking
        quiz_metrics = metrics_collector.start_quiz(initial_url)
        
        logger.info(
            "Starting quiz sequence",
            extra={
                "email": email,
                "initial_url": initial_url,
                "timeout": timeout
            }
        )
        
        # Track progress
        quizzes_solved = 0
        current_url = initial_url
        visited_urls: List[str] = []
        
        try:
            # Create timeout task
            async with asyncio.timeout(timeout):
                while current_url:
                    # Check if we've already visited this URL (prevent loops)
                    if current_url in visited_urls:
                        logger.warning(
                            "Detected URL loop, stopping",
                            extra={"url": current_url}
                        )
                        break
                    
                    visited_urls.append(current_url)
                    elapsed = time.time() - start_time
                    remaining = timeout - elapsed
                    
                    logger.info(
                        "Processing quiz",
                        extra={
                            "url": current_url,
                            "quiz_number": len(visited_urls),
                            "elapsed_time": elapsed,
                            "remaining_time": remaining
                        }
                    )
                    
                    # Solve single quiz
                    next_url = await self._solve_single_quiz(
                        email=email,
                        secret=secret,
                        quiz_url=current_url,
                        remaining_time=remaining
                    )
                    
                    quizzes_solved += 1
                    
                    # Move to next URL or complete
                    current_url = next_url
                    
                    if not current_url:
                        logger.info("Quiz sequence completed successfully")
                        break
            
            # Success
            total_time = time.time() - start_time
            quiz_metrics.quizzes_in_sequence = quizzes_solved
            metrics_collector.end_quiz(quiz_metrics, success=True)
            
            return QuizResult(
                success=True,
                total_time=total_time,
                quizzes_solved=quizzes_solved,
                final_status="completed",
                error=None
            )
        
        except asyncio.TimeoutError as e:
            # Timeout reached
            total_time = time.time() - start_time
            timeout_error = QuizTimeoutError(
                f"Quiz sequence exceeded {timeout} second time limit",
                original_error=e,
                context={
                    "total_time": total_time,
                    "quizzes_solved": quizzes_solved,
                    "timeout": timeout
                }
            )
            error_handler.handle_error(
                timeout_error,
                "quiz_sequence_timeout",
                {
                    "total_time": total_time,
                    "quizzes_solved": quizzes_solved,
                    "timeout": timeout
                }
            )
            logger.warning(
                "Quiz sequence timed out",
                extra={
                    "total_time": total_time,
                    "quizzes_solved": quizzes_solved
                }
            )
            
            quiz_metrics.quizzes_in_sequence = quizzes_solved
            metrics_collector.end_quiz(
                quiz_metrics,
                success=False,
                error=f"Exceeded {timeout} second time limit"
            )
            
            return QuizResult(
                success=False,
                total_time=total_time,
                quizzes_solved=quizzes_solved,
                final_status="timeout",
                error=f"Exceeded {timeout} second time limit"
            )
        
        except Exception as e:
            # Error occurred
            total_time = time.time() - start_time
            task_error = TaskExecutionError(
                f"Quiz sequence failed: {str(e)}",
                original_error=e,
                context={
                    "total_time": total_time,
                    "quizzes_solved": quizzes_solved,
                    "current_url": current_url
                }
            )
            error_handler.handle_error(
                task_error,
                "quiz_sequence_error",
                {
                    "original_error": str(e),
                    "original_error_type": type(e).__name__,
                    "total_time": total_time,
                    "quizzes_solved": quizzes_solved
                }
            )
            logger.error(
                "Quiz sequence failed",
                extra={
                    "exception_message": str(e),
                    "exception_type": type(e).__name__,
                    "total_time": total_time,
                    "quizzes_solved": quizzes_solved
                }
            )
            
            quiz_metrics.quizzes_in_sequence = quizzes_solved
            metrics_collector.end_quiz(quiz_metrics, success=False, error=str(e))
            
            return QuizResult(
                success=False,
                total_time=total_time,
                quizzes_solved=quizzes_solved,
                final_status="error",
                error=str(e)
            )
        
        finally:
            # Cleanup browser resources
            await self.browser_manager.cleanup()
            logger.info("Quiz orchestrator cleanup completed")
    
    async def _solve_single_quiz(
        self,
        email: str,
        secret: str,
        quiz_url: str,
        remaining_time: float
    ) -> Optional[str]:
        """
        Solve a single quiz with retry logic.
        
        Args:
            email: Student email address
            secret: Authentication secret string
            quiz_url: Quiz URL to solve
            remaining_time: Remaining time in seconds
        
        Returns:
            Next quiz URL if available, None if sequence complete
        
        Raises:
            Exception: If quiz solving fails after all retries
        """
        logger.info(
            "Solving single quiz",
            extra={
                "quiz_url": quiz_url,
                "remaining_time": remaining_time
            }
        )
        
        # Step 1: Fetch and render quiz page with error handling
        try:
            html_content = await self.browser_manager.fetch_and_render(quiz_url)
        except Exception as e:
            browser_error = BrowserError(
                f"Failed to fetch quiz page: {str(e)}",
                original_error=e,
                context={"quiz_url": quiz_url}
            )
            error_handler.handle_error(browser_error, "quiz_page_fetch", {"quiz_url": quiz_url})
            raise browser_error
        
        # Step 2: Parse task definition with error handling
        try:
            task_definition = self.task_parser.parse_quiz_page(html_content, str(quiz_url))
        except Exception as e:
            parse_error = TaskExecutionError(
                f"Failed to parse quiz page: {str(e)}",
                original_error=e,
                context={"quiz_url": quiz_url}
            )
            error_handler.handle_error(parse_error, "task_parsing", {"quiz_url": quiz_url})
            raise parse_error
        
        logger.info(
            "Task parsed",
            extra={
                "submit_url": str(task_definition.submit_url),
                "answer_format": task_definition.answer_format.value,
                "file_count": len(task_definition.file_urls)
            }
        )
        
        # Step 3: Solve task and submit with retry logic
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries_per_quiz:
            try:
                # Solve the task
                logger.info(
                    "Solving task",
                    extra={"attempt": retry_count + 1}
                )
                
                # Special handling for demo page
                if task_definition.additional_context.get("is_demo"):
                    logger.info("Using simple answer for demo page")
                    answer = "Demo submission to proceed to actual quiz"
                else:
                    answer = await self.llm_agent.solve_task(task_definition)
                
                logger.info(
                    "Task solved",
                    extra={
                        "answer_type": type(answer).__name__,
                        "attempt": retry_count + 1
                    }
                )
                
                # Submit the answer
                submit_response = await self.answer_submitter.submit_answer(
                    submit_url=str(task_definition.submit_url),
                    email=email,
                    secret=secret,
                    quiz_url=quiz_url,
                    answer=answer
                )
                
                # Check if answer was correct
                if submit_response.correct:
                    logger.info(
                        "Answer correct",
                        extra={
                            "has_next_url": submit_response.url is not None
                        }
                    )
                    
                    # Return next URL or None if sequence complete
                    return str(submit_response.url) if submit_response.url else None
                
                else:
                    # Answer was incorrect
                    logger.warning(
                        "Answer incorrect",
                        extra={
                            "reason": submit_response.reason,
                            "has_next_url": submit_response.url is not None,
                            "retry_count": retry_count
                        }
                    )
                    
                    # Decide: retry current quiz or skip to next URL
                    if submit_response.url and retry_count >= self.max_retries_per_quiz:
                        # Skip to next URL after max retries
                        logger.info(
                            "Max retries reached, skipping to next URL",
                            extra={"next_url": str(submit_response.url)}
                        )
                        return str(submit_response.url)
                    
                    elif submit_response.url and self._should_skip_to_next(
                        retry_count, remaining_time
                    ):
                        # Strategic decision to skip to next URL
                        logger.info(
                            "Skipping to next URL based on time constraints",
                            extra={"next_url": str(submit_response.url)}
                        )
                        return str(submit_response.url)
                    
                    else:
                        # Retry current quiz
                        retry_count += 1
                        last_error = submit_response.reason
                        
                        if retry_count <= self.max_retries_per_quiz:
                            logger.info(
                                "Retrying quiz",
                                extra={
                                    "retry_count": retry_count,
                                    "reason": submit_response.reason
                                }
                            )
                            # Continue to next iteration
                        else:
                            # Max retries reached, no next URL
                            logger.error(
                                "Max retries reached, no next URL available",
                                extra={"last_reason": submit_response.reason}
                            )
                            raise Exception(
                                f"Failed to solve quiz after {self.max_retries_per_quiz} retries: {submit_response.reason}"
                            )
            
            except Exception as e:
                # Error during solve or submit
                task_error = TaskExecutionError(
                    f"Error during quiz solving: {str(e)}",
                    original_error=e,
                    context={
                        "quiz_url": quiz_url,
                        "retry_count": retry_count,
                        "max_retries": self.max_retries_per_quiz
                    }
                )
                error_handler.handle_error(
                    task_error,
                    "quiz_solving_error",
                    {
                        "exception_message": str(e),
                        "exception_type": type(e).__name__,
                        "retry_count": retry_count,
                        "quiz_url": quiz_url
                    }
                )
                logger.error(
                    "Error during quiz solving",
                    extra={
                        "exception_message": str(e),
                        "exception_type": type(e).__name__,
                        "retry_count": retry_count
                    }
                )
                
                retry_count += 1
                last_error = str(e)
                
                if retry_count > self.max_retries_per_quiz:
                    final_error = TaskExecutionError(
                        f"Failed to solve quiz after {self.max_retries_per_quiz} retries: {last_error}",
                        original_error=e,
                        context={"quiz_url": quiz_url, "attempts": retry_count}
                    )
                    raise final_error
                
                # Wait before retry
                await asyncio.sleep(1)
        
        # Should not reach here
        raise Exception(f"Failed to solve quiz: {last_error}")
    
    def _should_skip_to_next(
        self,
        retry_count: int,
        remaining_time: float
    ) -> bool:
        """
        Decide whether to skip to next URL or retry current quiz.
        
        Strategy: Skip if we're running low on time and have already tried once.
        
        Args:
            retry_count: Current retry count
            remaining_time: Remaining time in seconds
        
        Returns:
            True if should skip to next URL, False if should retry
        """
        # If less than 30 seconds remaining and we've tried once, skip
        if remaining_time < 30 and retry_count >= 1:
            return True
        
        # If less than 60 seconds remaining and we've tried twice, skip
        if remaining_time < 60 and retry_count >= 2:
            return True
        
        # Otherwise, retry
        return False
