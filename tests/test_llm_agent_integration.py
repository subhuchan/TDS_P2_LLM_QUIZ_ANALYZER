"""Integration tests for LLM agent."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.llm_agent import LLMAgent
from src.models import TaskDefinition, AnswerFormat


@pytest.mark.asyncio
class TestLLMAgentIntegration:
    """Integration test suite for LLM Agent."""
    
    @pytest.fixture
    def agent(self):
        """Create LLMAgent instance."""
        return LLMAgent()
    
    @pytest.fixture
    def simple_task(self):
        """Create simple task definition."""
        return TaskDefinition(
            instructions="Calculate the sum of 5 and 3",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.NUMBER,
            file_urls=[],
            additional_context={}
        )
    
    @pytest.fixture
    def data_task(self):
        """Create data analysis task."""
        return TaskDefinition(
            instructions="Download CSV from URL and calculate the average of the 'age' column",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.NUMBER,
            file_urls=["https://example.com/data.csv"],
            additional_context={}
        )
    
    @pytest.fixture
    def chart_task(self):
        """Create chart generation task."""
        return TaskDefinition(
            instructions="Create a bar chart showing sales by category",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.BASE64,
            file_urls=["https://example.com/sales.csv"],
            additional_context={}
        )
    
    async def test_solve_simple_number_task(self, agent, simple_task):
        """Test solving simple number task with mocked LLM."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "8"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            answer = await agent.solve_task(simple_task)
            
            assert isinstance(answer, (int, float))
            assert answer == 8
    
    async def test_solve_boolean_task(self, agent):
        """Test solving boolean task."""
        task = TaskDefinition(
            instructions="Is 10 greater than 5?",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.BOOLEAN,
            file_urls=[],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "true"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            answer = await agent.solve_task(task)
            
            assert isinstance(answer, bool)
            assert answer is True
    
    async def test_solve_string_task(self, agent):
        """Test solving string task."""
        task = TaskDefinition(
            instructions="What is the capital of France?",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.STRING,
            file_urls=[],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Paris"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            answer = await agent.solve_task(task)
            
            assert isinstance(answer, str)
            assert answer == "Paris"
    
    async def test_solve_json_task(self, agent):
        """Test solving JSON task."""
        task = TaskDefinition(
            instructions="Return a JSON object with name and age",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.JSON,
            file_urls=[],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"name": "John", "age": 30}'
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            answer = await agent.solve_task(task)
            
            assert isinstance(answer, dict)
            assert answer["name"] == "John"
            assert answer["age"] == 30
    
    async def test_task_with_file_download(self, agent, data_task):
        """Test task requiring file download."""
        # Mock file download
        csv_data = b"name,age\nJohn,30\nJane,25"
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "27.5"
        
        with patch('src.web_scraper.WebScraper.download_file', return_value=csv_data):
            with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
                answer = await agent.solve_task(data_task)
                
                assert isinstance(answer, (int, float))
    
    async def test_task_with_tool_calling(self, agent):
        """Test task that requires tool calling."""
        task = TaskDefinition(
            instructions="Download data from URL and calculate sum",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.NUMBER,
            file_urls=["https://example.com/data.csv"],
            additional_context={}
        )
        
        # Mock tool call response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.tool_calls = [Mock()]
        mock_response.choices[0].message.tool_calls[0].function.name = "download_file"
        mock_response.choices[0].message.tool_calls[0].function.arguments = '{"url": "https://example.com/data.csv"}'
        
        # Mock final response
        mock_final_response = Mock()
        mock_final_response.choices = [Mock()]
        mock_final_response.choices[0].message.content = "100"
        
        with patch.object(agent.client.chat.completions, 'create', side_effect=[mock_response, mock_final_response]):
            with patch('src.web_scraper.WebScraper.download_file', return_value=b"data"):
                answer = await agent.solve_task(task)
                
                assert isinstance(answer, (int, float))
    
    async def test_answer_format_conversion_number(self, agent):
        """Test converting answer to number format."""
        task = TaskDefinition(
            instructions="Calculate sum",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.NUMBER,
            file_urls=[],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "The answer is 42"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            answer = await agent.solve_task(task)
            
            # Should extract number from text
            assert isinstance(answer, (int, float))
    
    async def test_answer_format_conversion_boolean(self, agent):
        """Test converting answer to boolean format."""
        task = TaskDefinition(
            instructions="Is it true?",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.BOOLEAN,
            file_urls=[],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Yes, it is true"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            answer = await agent.solve_task(task)
            
            # Should extract boolean from text
            assert isinstance(answer, bool)
    
    async def test_handle_llm_error(self, agent, simple_task):
        """Test handling LLM API errors."""
        with patch.object(agent.client.chat.completions, 'create', side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await agent.solve_task(simple_task)
    
    async def test_handle_invalid_response_format(self, agent):
        """Test handling invalid response format."""
        task = TaskDefinition(
            instructions="Return a number",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.NUMBER,
            file_urls=[],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "not a number"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(Exception):
                await agent.solve_task(task)
    
    async def test_task_interpretation(self, agent):
        """Test LLM task interpretation."""
        task = TaskDefinition(
            instructions="Complex multi-step task: download data, filter rows where age > 25, calculate average salary",
            submit_url="https://example.com/submit",
            answer_format=AnswerFormat.NUMBER,
            file_urls=["https://example.com/data.csv"],
            additional_context={}
        )
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "55000"
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            with patch('src.web_scraper.WebScraper.download_file', return_value=b"data"):
                answer = await agent.solve_task(task)
                
                assert isinstance(answer, (int, float))
    
    async def test_retry_on_rate_limit(self, agent, simple_task):
        """Test retry logic on rate limit error."""
        from openai import RateLimitError
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "8"
        
        # First call raises rate limit, second succeeds
        with patch.object(
            agent.client.chat.completions,
            'create',
            side_effect=[RateLimitError("Rate limit"), mock_response]
        ):
            answer = await agent.solve_task(simple_task)
            
            assert answer == 8
    
    async def test_base64_chart_generation(self, agent, chart_task):
        """Test generating base64 encoded chart."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            with patch('src.web_scraper.WebScraper.download_file', return_value=b"data"):
                answer = await agent.solve_task(chart_task)
                
                assert isinstance(answer, str)
                assert answer.startswith('data:image/png;base64,')
