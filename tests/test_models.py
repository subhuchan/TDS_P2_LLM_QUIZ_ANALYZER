"""Tests for data models and validation."""

import pytest
from pydantic import ValidationError

from src.models import (
    AnswerFormat,
    QuizRequest,
    QuizResponse,
    TaskDefinition,
    SubmitPayload,
    SubmitResponse,
    QuizResult,
)


class TestAnswerFormat:
    """Tests for AnswerFormat enum."""
    
    def test_answer_format_values(self):
        """Test that all expected answer formats are defined."""
        assert AnswerFormat.BOOLEAN == "boolean"
        assert AnswerFormat.NUMBER == "number"
        assert AnswerFormat.STRING == "string"
        assert AnswerFormat.BASE64 == "base64"
        assert AnswerFormat.JSON == "json"


class TestQuizRequest:
    """Tests for QuizRequest model."""
    
    def test_valid_quiz_request(self):
        """Test creating a valid quiz request."""
        request = QuizRequest(
            email="student@example.com",
            secret="my-secret-123",
            url="https://example.com/quiz"
        )
        assert request.email == "student@example.com"
        assert request.secret == "my-secret-123"
        assert str(request.url) == "https://example.com/quiz"
    
    def test_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError):
            QuizRequest(
                email="not-an-email",
                secret="my-secret",
                url="https://example.com/quiz"
            )
    
    def test_empty_secret(self):
        """Test that empty secret raises validation error."""
        with pytest.raises(ValidationError):
            QuizRequest(
                email="student@example.com",
                secret="",
                url="https://example.com/quiz"
            )
    
    def test_whitespace_secret(self):
        """Test that whitespace-only secret raises validation error."""
        with pytest.raises(ValidationError):
            QuizRequest(
                email="student@example.com",
                secret="   ",
                url="https://example.com/quiz"
            )
    
    def test_invalid_url(self):
        """Test that invalid URL raises validation error."""
        with pytest.raises(ValidationError):
            QuizRequest(
                email="student@example.com",
                secret="my-secret",
                url="not-a-url"
            )
    
    def test_secret_trimmed(self):
        """Test that secret is trimmed of whitespace."""
        request = QuizRequest(
            email="student@example.com",
            secret="  my-secret  ",
            url="https://example.com/quiz"
        )
        assert request.secret == "my-secret"


class TestQuizResponse:
    """Tests for QuizResponse model."""
    
    def test_quiz_response_with_message(self):
        """Test creating quiz response with message."""
        response = QuizResponse(status="success", message="Quiz accepted")
        assert response.status == "success"
        assert response.message == "Quiz accepted"
    
    def test_quiz_response_without_message(self):
        """Test creating quiz response without message."""
        response = QuizResponse(status="success")
        assert response.status == "success"
        assert response.message is None


class TestTaskDefinition:
    """Tests for TaskDefinition model."""
    
    def test_valid_task_definition(self):
        """Test creating a valid task definition."""
        task = TaskDefinition(
            instructions="Solve this task",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.STRING,
            file_urls=["https://example.com/file.csv"],
            additional_context={"key": "value"}
        )
        assert task.instructions == "Solve this task"
        assert str(task.submit_url) == "https://example.com/submit"
        assert task.answer_format == AnswerFormat.STRING
        assert len(task.file_urls) == 1
        assert task.additional_context == {"key": "value"}
    
    def test_task_definition_defaults(self):
        """Test task definition with default values."""
        task = TaskDefinition(
            instructions="Solve this task",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.BOOLEAN
        )
        assert task.file_urls == []
        assert task.additional_context == {}


class TestSubmitPayload:
    """Tests for SubmitPayload model."""
    
    def test_valid_submit_payload(self):
        """Test creating a valid submit payload."""
        payload = SubmitPayload(
            email="student@example.com",
            secret="my-secret",
            url="https://example.com/quiz",
            answer=42
        )
        assert payload.email == "student@example.com"
        assert payload.secret == "my-secret"
        assert str(payload.url) == "https://example.com/quiz"
        assert payload.answer == 42
    
    def test_submit_payload_with_different_answer_types(self):
        """Test submit payload with various answer types."""
        # Boolean answer
        payload1 = SubmitPayload(
            email="student@example.com",
            secret="secret",
            url="https://example.com/quiz",
            answer=True
        )
        assert payload1.answer is True
        
        # String answer
        payload2 = SubmitPayload(
            email="student@example.com",
            secret="secret",
            url="https://example.com/quiz",
            answer="text answer"
        )
        assert payload2.answer == "text answer"
        
        # JSON object answer
        payload3 = SubmitPayload(
            email="student@example.com",
            secret="secret",
            url="https://example.com/quiz",
            answer={"key": "value"}
        )
        assert payload3.answer == {"key": "value"}
    
    def test_empty_secret_validation(self):
        """Test that empty secret raises validation error."""
        with pytest.raises(ValidationError):
            SubmitPayload(
                email="student@example.com",
                secret="",
                url="https://example.com/quiz",
                answer=42
            )


class TestSubmitResponse:
    """Tests for SubmitResponse model."""
    
    def test_correct_answer_response(self):
        """Test response for correct answer."""
        response = SubmitResponse(correct=True)
        assert response.correct is True
        assert response.reason is None
        assert response.url is None
    
    def test_incorrect_answer_with_reason(self):
        """Test response for incorrect answer with reason."""
        response = SubmitResponse(
            correct=False,
            reason="Expected 42 but got 41"
        )
        assert response.correct is False
        assert response.reason == "Expected 42 but got 41"
    
    def test_correct_answer_with_next_url(self):
        """Test response with next quiz URL."""
        response = SubmitResponse(
            correct=True,
            url="https://example.com/next-quiz"
        )
        assert response.correct is True
        assert str(response.url) == "https://example.com/next-quiz"


class TestQuizResult:
    """Tests for QuizResult model."""
    
    def test_successful_quiz_result(self):
        """Test successful quiz result."""
        result = QuizResult(
            success=True,
            total_time=120.5,
            quizzes_solved=3,
            final_status="All quizzes completed"
        )
        assert result.success is True
        assert result.total_time == 120.5
        assert result.quizzes_solved == 3
        assert result.final_status == "All quizzes completed"
        assert result.error is None
    
    def test_failed_quiz_result(self):
        """Test failed quiz result with error."""
        result = QuizResult(
            success=False,
            total_time=180.0,
            quizzes_solved=1,
            final_status="Timeout",
            error="Exceeded 3-minute time limit"
        )
        assert result.success is False
        assert result.error == "Exceeded 3-minute time limit"
    
    def test_negative_time_validation(self):
        """Test that negative time raises validation error."""
        with pytest.raises(ValidationError):
            QuizResult(
                success=True,
                total_time=-10.0,
                quizzes_solved=1,
                final_status="Complete"
            )
    
    def test_negative_quizzes_validation(self):
        """Test that negative quizzes count raises validation error."""
        with pytest.raises(ValidationError):
            QuizResult(
                success=True,
                total_time=100.0,
                quizzes_solved=-1,
                final_status="Complete"
            )
