"""Integration tests for quiz orchestrator."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time

from src.quiz_orchestrator import QuizOrchestrator
from src.models import QuizResult, SubmitResponse


@pytest.mark.asyncio
class TestQuizOrchestratorIntegration:
    """Integration test suite for QuizOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create QuizOrchestrator instance."""
        return QuizOrchestrator(timeout=180, max_retries_per_quiz=2)
    
    async def test_complete_quiz_sequence_single_quiz(self, orchestrator):
        """Test complete quiz sequence with single quiz."""
        # Mock browser fetch
        html_content = '<html><body>Quiz content</body></html>'
        
        # Mock task definition
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # Mock LLM answer
        mock_answer = 42
        
        # Mock submit response (correct, no next URL)
        mock_submit_response = SubmitResponse(
            correct=True,
            reason="",
            url=None
        )
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=mock_answer):
                    with patch.object(orchestrator.answer_submitter, 'submit_answer', return_value=mock_submit_response):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz"
                        )
        
        assert result.success is True
        assert result.quizzes_solved == 1
        assert result.final_status == "completed"
        assert result.total_time < 180
    
    async def test_complete_quiz_sequence_multiple_quizzes(self, orchestrator):
        """Test complete quiz sequence with multiple quizzes."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # First quiz: correct, has next URL
        mock_submit_response1 = SubmitResponse(
            correct=True,
            reason="",
            url="https://example.com/quiz2"
        )
        
        # Second quiz: correct, no next URL
        mock_submit_response2 = SubmitResponse(
            correct=True,
            reason="",
            url=None
        )
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=42):
                    with patch.object(
                        orchestrator.answer_submitter,
                        'submit_answer',
                        side_effect=[mock_submit_response1, mock_submit_response2]
                    ):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz1"
                        )
        
        assert result.success is True
        assert result.quizzes_solved == 2
        assert result.final_status == "completed"
    
    async def test_timeout_enforcement(self, orchestrator):
        """Test that timeout is enforced."""
        # Create orchestrator with short timeout
        short_orchestrator = QuizOrchestrator(timeout=2, max_retries_per_quiz=0)
        
        html_content = '<html><body>Quiz content</body></html>'
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # Mock slow operations
        async def slow_solve(*args, **kwargs):
            await asyncio.sleep(3)  # Longer than timeout
            return 42
        
        with patch.object(short_orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(short_orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(short_orchestrator.llm_agent, 'solve_task', side_effect=slow_solve):
                    result = await short_orchestrator.solve_quiz_sequence(
                        email="test@example.com",
                        secret="secret123",
                        initial_url="https://example.com/quiz"
                    )
        
        assert result.success is False
        assert result.final_status == "timeout"
        assert "time limit" in result.error.lower()
    
    async def test_retry_logic_incorrect_answer(self, orchestrator):
        """Test retry logic when answer is incorrect."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # First attempt: incorrect
        mock_submit_response1 = SubmitResponse(
            correct=False,
            reason="Wrong answer",
            url=None
        )
        
        # Second attempt: correct
        mock_submit_response2 = SubmitResponse(
            correct=True,
            reason="",
            url=None
        )
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', side_effect=[41, 42]):
                    with patch.object(
                        orchestrator.answer_submitter,
                        'submit_answer',
                        side_effect=[mock_submit_response1, mock_submit_response2]
                    ):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz"
                        )
        
        assert result.success is True
        assert result.quizzes_solved == 1
    
    async def test_retry_logic_max_retries(self, orchestrator):
        """Test retry logic when max retries exceeded."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # All attempts incorrect, no next URL
        mock_submit_response = SubmitResponse(
            correct=False,
            reason="Wrong answer",
            url=None
        )
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=41):
                    with patch.object(
                        orchestrator.answer_submitter,
                        'submit_answer',
                        return_value=mock_submit_response
                    ):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz"
                        )
        
        assert result.success is False
        assert "retries" in result.error.lower()
    
    async def test_retry_with_next_url(self, orchestrator):
        """Test retry logic when incorrect answer has next URL."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # First quiz: incorrect but has next URL
        mock_submit_response1 = SubmitResponse(
            correct=False,
            reason="Wrong answer",
            url="https://example.com/quiz2"
        )
        
        # Second quiz: correct
        mock_submit_response2 = SubmitResponse(
            correct=True,
            reason="",
            url=None
        )
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=42):
                    with patch.object(
                        orchestrator.answer_submitter,
                        'submit_answer',
                        side_effect=[
                            mock_submit_response1,
                            mock_submit_response1,  # Retry still incorrect
                            mock_submit_response1,  # Max retries
                            mock_submit_response2   # Next quiz
                        ]
                    ):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz1"
                        )
        
        # Should skip to next URL after max retries
        assert result.quizzes_solved >= 1
    
    async def test_multi_quiz_sequence(self, orchestrator):
        """Test handling multi-quiz sequences."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # Create chain of 5 quizzes
        responses = [
            SubmitResponse(correct=True, reason="", url="https://example.com/quiz2"),
            SubmitResponse(correct=True, reason="", url="https://example.com/quiz3"),
            SubmitResponse(correct=True, reason="", url="https://example.com/quiz4"),
            SubmitResponse(correct=True, reason="", url="https://example.com/quiz5"),
            SubmitResponse(correct=True, reason="", url=None),  # Final quiz
        ]
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=42):
                    with patch.object(
                        orchestrator.answer_submitter,
                        'submit_answer',
                        side_effect=responses
                    ):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz1"
                        )
        
        assert result.success is True
        assert result.quizzes_solved == 5
        assert result.final_status == "completed"
    
    async def test_handle_browser_error(self, orchestrator):
        """Test handling browser errors."""
        with patch.object(
            orchestrator.browser_manager,
            'fetch_and_render',
            side_effect=Exception("Browser error")
        ):
            result = await orchestrator.solve_quiz_sequence(
                email="test@example.com",
                secret="secret123",
                initial_url="https://example.com/quiz"
            )
        
        assert result.success is False
        assert result.final_status == "error"
        assert "browser" in result.error.lower() or "error" in result.error.lower()
    
    async def test_handle_parsing_error(self, orchestrator):
        """Test handling parsing errors."""
        html_content = '<html><body>Invalid quiz</body></html>'
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(
                orchestrator.task_parser,
                'parse_quiz_page',
                side_effect=Exception("Parsing error")
            ):
                result = await orchestrator.solve_quiz_sequence(
                    email="test@example.com",
                    secret="secret123",
                    initial_url="https://example.com/quiz"
                )
        
        assert result.success is False
        assert result.final_status == "error"
    
    async def test_handle_llm_error(self, orchestrator):
        """Test handling LLM errors."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(
                    orchestrator.llm_agent,
                    'solve_task',
                    side_effect=Exception("LLM error")
                ):
                    result = await orchestrator.solve_quiz_sequence(
                        email="test@example.com",
                        secret="secret123",
                        initial_url="https://example.com/quiz"
                    )
        
        assert result.success is False
        assert result.final_status == "error"
    
    async def test_timing_tracking(self, orchestrator):
        """Test that timing is tracked correctly."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        mock_submit_response = SubmitResponse(correct=True, reason="", url=None)
        
        start_time = time.time()
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=42):
                    with patch.object(orchestrator.answer_submitter, 'submit_answer', return_value=mock_submit_response):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz"
                        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        assert result.total_time > 0
        assert result.total_time <= elapsed + 1  # Allow 1 second tolerance
    
    async def test_prevent_url_loops(self, orchestrator):
        """Test prevention of URL loops."""
        html_content = '<html><body>Quiz content</body></html>'
        
        mock_task = Mock()
        mock_task.submit_url = "https://example.com/submit"
        mock_task.answer_format = "number"
        mock_task.file_urls = []
        
        # Create loop: quiz1 -> quiz2 -> quiz1
        responses = [
            SubmitResponse(correct=True, reason="", url="https://example.com/quiz2"),
            SubmitResponse(correct=True, reason="", url="https://example.com/quiz1"),  # Loop back
        ]
        
        with patch.object(orchestrator.browser_manager, 'fetch_and_render', return_value=html_content):
            with patch.object(orchestrator.task_parser, 'parse_quiz_page', return_value=mock_task):
                with patch.object(orchestrator.llm_agent, 'solve_task', return_value=42):
                    with patch.object(
                        orchestrator.answer_submitter,
                        'submit_answer',
                        side_effect=responses
                    ):
                        result = await orchestrator.solve_quiz_sequence(
                            email="test@example.com",
                            secret="secret123",
                            initial_url="https://example.com/quiz1"
                        )
        
        # Should detect loop and stop
        assert result.quizzes_solved == 2
        assert result.success is True or result.final_status == "completed"
