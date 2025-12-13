"""Monitoring and metrics collection for the LLM Analysis Quiz System."""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class QuizMetrics:
    """Metrics for a single quiz solving attempt."""
    
    quiz_url: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None
    
    # Timing metrics
    browser_time: float = 0.0
    parsing_time: float = 0.0
    solving_time: float = 0.0
    submission_time: float = 0.0
    
    # LLM metrics
    llm_calls: int = 0
    llm_tokens_used: int = 0
    llm_cost: float = 0.0
    
    # Result metrics
    retries: int = 0
    quizzes_in_sequence: int = 1
    
    def total_time(self) -> float:
        """Calculate total time taken."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "quiz_url": self.quiz_url,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "total_time": self.total_time(),
            "success": self.success,
            "error": self.error,
            "timing": {
                "browser": self.browser_time,
                "parsing": self.parsing_time,
                "solving": self.solving_time,
                "submission": self.submission_time,
            },
            "llm": {
                "calls": self.llm_calls,
                "tokens": self.llm_tokens_used,
                "cost": self.llm_cost,
            },
            "retries": self.retries,
            "quizzes_in_sequence": self.quizzes_in_sequence,
        }


@dataclass
class SystemMetrics:
    """Aggregate system metrics."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    total_quizzes_solved: int = 0
    total_time: float = 0.0
    
    total_llm_calls: int = 0
    total_llm_tokens: int = 0
    total_llm_cost: float = 0.0
    
    quiz_metrics: list = field(default_factory=list)
    
    def add_quiz_metrics(self, metrics: QuizMetrics) -> None:
        """Add metrics from a quiz attempt."""
        self.total_requests += 1
        
        if metrics.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        self.total_quizzes_solved += metrics.quizzes_in_sequence
        self.total_time += metrics.total_time()
        
        self.total_llm_calls += metrics.llm_calls
        self.total_llm_tokens += metrics.llm_tokens_used
        self.total_llm_cost += metrics.llm_cost
        
        self.quiz_metrics.append(metrics.to_dict())
        
        # Log metrics
        logger.info(
            "quiz_metrics_recorded",
            quiz_url=metrics.quiz_url,
            success=metrics.success,
            total_time=metrics.total_time(),
            llm_calls=metrics.llm_calls,
            llm_tokens=metrics.llm_tokens_used,
            llm_cost=metrics.llm_cost,
        )
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    def get_average_time(self) -> float:
        """Calculate average quiz solving time."""
        if self.total_requests == 0:
            return 0.0
        return self.total_time / self.total_requests
    
    def get_average_llm_cost(self) -> float:
        """Calculate average LLM cost per request."""
        if self.total_requests == 0:
            return 0.0
        return self.total_llm_cost / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system metrics to dictionary."""
        return {
            "summary": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": self.get_success_rate(),
                "total_quizzes_solved": self.total_quizzes_solved,
                "total_time": self.total_time,
                "average_time": self.get_average_time(),
            },
            "llm_usage": {
                "total_calls": self.total_llm_calls,
                "total_tokens": self.total_llm_tokens,
                "total_cost": self.total_llm_cost,
                "average_cost_per_request": self.get_average_llm_cost(),
            },
            "recent_quizzes": self.quiz_metrics[-10:],  # Last 10 quizzes
        }
    
    def save_to_file(self, filepath: str = "metrics.json") -> None:
        """Save metrics to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info("metrics_saved", filepath=filepath)
        except Exception as e:
            logger.error("failed_to_save_metrics", error=str(e), filepath=filepath)


class MetricsCollector:
    """Singleton metrics collector for the application."""
    
    _instance = None
    _metrics: SystemMetrics = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._metrics = SystemMetrics()
        return cls._instance
    
    def start_quiz(self, quiz_url: str) -> QuizMetrics:
        """Start tracking a new quiz."""
        metrics = QuizMetrics(
            quiz_url=quiz_url,
            start_time=time.time()
        )
        logger.info("quiz_tracking_started", quiz_url=quiz_url)
        return metrics
    
    def end_quiz(self, metrics: QuizMetrics, success: bool, error: Optional[str] = None) -> None:
        """End tracking a quiz and record metrics."""
        metrics.end_time = time.time()
        metrics.success = success
        metrics.error = error
        
        self._metrics.add_quiz_metrics(metrics)
        
        logger.info(
            "quiz_tracking_ended",
            quiz_url=metrics.quiz_url,
            success=success,
            total_time=metrics.total_time(),
            error=error,
        )
    
    def record_llm_usage(
        self,
        metrics: QuizMetrics,
        tokens_used: int,
        cost: float
    ) -> None:
        """Record LLM API usage."""
        metrics.llm_calls += 1
        metrics.llm_tokens_used += tokens_used
        metrics.llm_cost += cost
        
        logger.info(
            "llm_usage_recorded",
            tokens=tokens_used,
            cost=cost,
            total_tokens=metrics.llm_tokens_used,
            total_cost=metrics.llm_cost,
        )
    
    def record_timing(
        self,
        metrics: QuizMetrics,
        component: str,
        duration: float
    ) -> None:
        """Record timing for a component."""
        if component == "browser":
            metrics.browser_time += duration
        elif component == "parsing":
            metrics.parsing_time += duration
        elif component == "solving":
            metrics.solving_time += duration
        elif component == "submission":
            metrics.submission_time += duration
        
        logger.debug(
            "component_timing_recorded",
            component=component,
            duration=duration,
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self._metrics.to_dict()
    
    def save_metrics(self, filepath: str = "metrics.json") -> None:
        """Save metrics to file."""
        self._metrics.save_to_file(filepath)
    
    def log_summary(self) -> None:
        """Log a summary of current metrics."""
        summary = self._metrics.to_dict()["summary"]
        llm_usage = self._metrics.to_dict()["llm_usage"]
        
        logger.info(
            "metrics_summary",
            **summary,
            **llm_usage,
        )


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector
