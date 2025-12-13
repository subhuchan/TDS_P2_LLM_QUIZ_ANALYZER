"""Unit tests for answer submitter."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from src.answer_submitter import AnswerSubmitter
from src.models import SubmitResponse


@pytest.mark.asyncio
class TestAnswerSubmitter:
    """Test suite for AnswerSubmitter class."""
    
    @pytest.fixture
    def submitter(self):
        """Create AnswerSubmitter instance."""
        return AnswerSubmitter()
    
    async def test_submit_answer_success(self, submitter):
        """Test successful answer submission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "correct": True,
            "reason": "",
            "url": None
        }
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=42
            )
            
            assert result.correct is True
            assert result.reason == ""
            assert result.url is None
    
    async def test_submit_answer_incorrect(self, submitter):
        """Test incorrect answer submission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "correct": False,
            "reason": "Wrong answer",
            "url": "https://example.com/retry"
        }
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=41
            )
            
            assert result.correct is False
            assert result.reason == "Wrong answer"
            assert result.url == "https://example.com/retry"
    
    async def test_submit_answer_with_next_url(self, submitter):
        """Test submission with next quiz URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "correct": True,
            "reason": "",
            "url": "https://example.com/next-quiz"
        }
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer="answer"
            )
            
            assert result.correct is True
            assert result.url == "https://example.com/next-quiz"
    
    async def test_payload_construction_number(self, submitter):
        """Test payload construction with number answer."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response) as mock_post:
            await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=42
            )
            
            # Verify payload structure
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            
            assert payload['email'] == "test@example.com"
            assert payload['secret'] == "secret123"
            assert payload['url'] == "https://example.com/quiz"
            assert payload['answer'] == 42
    
    async def test_payload_construction_string(self, submitter):
        """Test payload construction with string answer."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response) as mock_post:
            await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer="text answer"
            )
            
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            
            assert payload['answer'] == "text answer"
    
    async def test_payload_construction_boolean(self, submitter):
        """Test payload construction with boolean answer."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response) as mock_post:
            await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=True
            )
            
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            
            assert payload['answer'] is True
    
    async def test_payload_construction_json(self, submitter):
        """Test payload construction with JSON object answer."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        answer_obj = {"key": "value", "number": 123}
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response) as mock_post:
            await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=answer_obj
            )
            
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            
            assert payload['answer'] == answer_obj
    
    async def test_response_parsing_all_fields(self, submitter):
        """Test parsing response with all fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "correct": False,
            "reason": "Calculation error",
            "url": "https://example.com/retry",
            "delay": 5
        }
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=42
            )
            
            assert result.correct is False
            assert result.reason == "Calculation error"
            assert result.url == "https://example.com/retry"
    
    async def test_response_parsing_minimal_fields(self, submitter):
        """Test parsing response with minimal fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "correct": True
        }
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=42
            )
            
            assert result.correct is True
            assert result.reason is None or result.reason == ""
            assert result.url is None
    
    async def test_retry_on_timeout(self, submitter):
        """Test retry logic on timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        # First call times out, second succeeds
        with patch.object(
            httpx.AsyncClient,
            'post',
            side_effect=[httpx.TimeoutException("Timeout"), mock_response]
        ):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=42,
                max_retries=2
            )
            
            assert result.correct is True
    
    async def test_retry_on_500_error(self, submitter):
        """Test retry logic on server error."""
        mock_error_response = Mock()
        mock_error_response.status_code = 500
        mock_error_response.raise_for_status = Mock(side_effect=httpx.HTTPStatusError(
            "500 Server Error",
            request=Mock(),
            response=mock_error_response
        ))
        
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        with patch.object(
            httpx.AsyncClient,
            'post',
            side_effect=[mock_error_response, mock_success_response]
        ):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=42,
                max_retries=2
            )
            
            assert result.correct is True
    
    async def test_max_retries_exceeded(self, submitter):
        """Test behavior when max retries exceeded."""
        with patch.object(
            httpx.AsyncClient,
            'post',
            side_effect=httpx.TimeoutException("Timeout")
        ):
            with pytest.raises(httpx.TimeoutException):
                await submitter.submit_answer(
                    submit_url="https://example.com/submit",
                    email="test@example.com",
                    secret="secret123",
                    quiz_url="https://example.com/quiz",
                    answer=42,
                    max_retries=2
                )
    
    async def test_handle_invalid_json_response(self, submitter):
        """Test handling invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            with pytest.raises(ValueError):
                await submitter.submit_answer(
                    submit_url="https://example.com/submit",
                    email="test@example.com",
                    secret="secret123",
                    quiz_url="https://example.com/quiz",
                    answer=42
                )
    
    async def test_handle_connection_error(self, submitter):
        """Test handling connection errors."""
        with patch.object(
            httpx.AsyncClient,
            'post',
            side_effect=httpx.ConnectError("Connection failed")
        ):
            with pytest.raises(httpx.ConnectError):
                await submitter.submit_answer(
                    submit_url="https://example.com/submit",
                    email="test@example.com",
                    secret="secret123",
                    quiz_url="https://example.com/quiz",
                    answer=42,
                    max_retries=1
                )
    
    async def test_submit_large_payload(self, submitter):
        """Test submitting large payload."""
        large_answer = "x" * (500 * 1024)  # 500KB string
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=large_answer
            )
            
            assert result.correct is True
    
    async def test_submit_base64_image(self, submitter):
        """Test submitting base64 encoded image."""
        base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"correct": True, "reason": "", "url": None}
        
        with patch.object(httpx.AsyncClient, 'post', return_value=mock_response):
            result = await submitter.submit_answer(
                submit_url="https://example.com/submit",
                email="test@example.com",
                secret="secret123",
                quiz_url="https://example.com/quiz",
                answer=base64_image
            )
            
            assert result.correct is True
