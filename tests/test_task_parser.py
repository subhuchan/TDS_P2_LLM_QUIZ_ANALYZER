"""Tests for TaskParser functionality."""

import base64
import pytest

from src.models import AnswerFormat
from src.task_parser import TaskParser


class TestTaskParser:
    """Tests for TaskParser class."""
    
    def test_parse_simple_quiz_page(self):
        """Test parsing a simple quiz page with base64 content."""
        # Create a simple task instruction
        instructions = """
        Task: Calculate the sum of numbers.
        Submit your answer to: https://example.com/submit
        Answer format: number
        """
        
        # Encode to base64
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        
        # Create HTML with base64 content
        html = f"""
        <html>
            <body>
                <pre>{base64_content}</pre>
            </body>
        </html>
        """
        
        parser = TaskParser()
        task = parser.parse_quiz_page(html)
        
        assert task.instructions == instructions
        assert str(task.submit_url) == "https://example.com/submit"
        assert task.answer_format == AnswerFormat.NUMBER
    
    def test_extract_base64_from_pre_tag(self):
        """Test extracting base64 content from pre tag."""
        instructions = "Test instructions"
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        html = f"<html><body><pre>{base64_content}</pre></body></html>"
        
        parser = TaskParser()
        extracted = parser._extract_base64_content(html)
        
        assert extracted == base64_content
    
    def test_decode_base64(self):
        """Test base64 decoding."""
        original_text = "Hello, World!"
        base64_text = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
        
        parser = TaskParser()
        decoded = parser._decode_base64(base64_text)
        
        assert decoded == original_text
    
    def test_parse_submit_url(self):
        """Test parsing submit URL from instructions."""
        instructions = "Submit your answer to: https://example.com/api/submit"
        
        parser = TaskParser()
        url = parser._parse_submit_url(instructions)
        
        assert url == "https://example.com/api/submit"
    
    def test_detect_answer_format_number(self):
        """Test detecting number answer format."""
        instructions = "Calculate the sum of all numbers"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.NUMBER
    
    def test_detect_answer_format_boolean(self):
        """Test detecting boolean answer format."""
        instructions = "Answer true or false"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.BOOLEAN
    
    def test_detect_answer_format_base64(self):
        """Test detecting base64 answer format."""
        instructions = "Generate a chart and return as base64"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.BASE64
    
    def test_detect_answer_format_json(self):
        """Test detecting JSON answer format."""
        instructions = "Return the result as a JSON object"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.JSON
    
    def test_extract_file_urls(self):
        """Test extracting file URLs from instructions."""
        instructions = """
        Download the data from https://example.com/data.csv
        and the PDF from https://example.com/report.pdf
        """
        
        parser = TaskParser()
        urls = parser._extract_file_urls(instructions)
        
        assert len(urls) == 2
        assert "https://example.com/data.csv" in urls
        assert "https://example.com/report.pdf" in urls
    
    def test_extract_no_file_urls(self):
        """Test when no file URLs are present."""
        instructions = "Just calculate the sum"
        
        parser = TaskParser()
        urls = parser._extract_file_urls(instructions)
        
        assert len(urls) == 0
    
    def test_clean_url_removes_punctuation(self):
        """Test URL cleaning removes trailing punctuation."""
        parser = TaskParser()
        
        assert parser._clean_url("https://example.com/api.") == "https://example.com/api"
        assert parser._clean_url("https://example.com/api,") == "https://example.com/api"
        assert parser._clean_url("https://example.com/api)") == "https://example.com/api"
    
    def test_is_base64_valid(self):
        """Test base64 validation with valid content."""
        parser = TaskParser()
        valid_base64 = base64.b64encode(b"test content that is long enough").decode('utf-8')
        
        assert parser._is_base64(valid_base64) is True
    
    def test_is_base64_invalid(self):
        """Test base64 validation with invalid content."""
        parser = TaskParser()
        
        assert parser._is_base64("not base64!@#$") is False
        assert parser._is_base64("short") is False
        assert parser._is_base64("") is False
    
    def test_extract_base64_from_code_tag(self):
        """Test extracting base64 content from code tag."""
        instructions = "Test instructions for code tag"
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        html = f"<html><body><code>{base64_content}</code></body></html>"
        
        parser = TaskParser()
        extracted = parser._extract_base64_content(html)
        
        assert extracted == base64_content
    
    def test_extract_base64_from_data_attribute(self):
        """Test extracting base64 content from data attribute."""
        instructions = "Test instructions from data attribute"
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        html = f'<html><body><div data-task="{base64_content}">Content</div></body></html>'
        
        parser = TaskParser()
        extracted = parser._extract_base64_content(html)
        
        assert extracted == base64_content
    
    def test_extract_base64_from_script_tag(self):
        """Test extracting base64 content from script tag."""
        instructions = "Test instructions from script tag with enough length"
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        html = f'<html><body><script>var task = "{base64_content}";</script></body></html>'
        
        parser = TaskParser()
        extracted = parser._extract_base64_content(html)
        
        assert extracted == base64_content
    
    def test_extract_base64_missing_raises_error(self):
        """Test that missing base64 content raises ValueError."""
        html = "<html><body><p>No base64 content here</p></body></html>"
        
        parser = TaskParser()
        
        with pytest.raises(ValueError, match="Could not find base64-encoded content"):
            parser._extract_base64_content(html)
    
    def test_decode_base64_invalid_raises_error(self):
        """Test that invalid base64 raises ValueError."""
        parser = TaskParser()
        
        with pytest.raises(ValueError, match="Failed to decode base64 content"):
            parser._decode_base64("not-valid-base64!@#$")
    
    def test_parse_submit_url_with_submit_keyword(self):
        """Test parsing submit URL when 'submit' keyword is present."""
        instructions = """
        Complete the task and submit to: https://api.example.com/submit
        Other URL: https://example.com/info
        """
        
        parser = TaskParser()
        url = parser._parse_submit_url(instructions)
        
        # Should prefer URL with 'submit' keyword
        assert url == "https://api.example.com/submit"
    
    def test_parse_submit_url_with_endpoint_keyword(self):
        """Test parsing submit URL with 'endpoint' keyword."""
        instructions = "POST endpoint: https://example.com/api/endpoint"
        
        parser = TaskParser()
        url = parser._parse_submit_url(instructions)
        
        assert url == "https://example.com/api/endpoint"
    
    def test_parse_submit_url_first_url_fallback(self):
        """Test that first URL is used when no submit keyword found."""
        instructions = "Visit https://example.com/first and then https://example.com/second"
        
        parser = TaskParser()
        url = parser._parse_submit_url(instructions)
        
        assert url == "https://example.com/first"
    
    def test_parse_submit_url_missing_raises_error(self):
        """Test that missing submit URL raises ValueError."""
        instructions = "No URL in these instructions"
        
        parser = TaskParser()
        
        with pytest.raises(ValueError, match="Could not find submit URL"):
            parser._parse_submit_url(instructions)
    
    def test_parse_submit_url_with_trailing_punctuation(self):
        """Test parsing submit URL with trailing punctuation."""
        instructions = "Submit to: https://example.com/submit."
        
        parser = TaskParser()
        url = parser._parse_submit_url(instructions)
        
        assert url == "https://example.com/submit"
    
    def test_detect_answer_format_string_default(self):
        """Test that string is the default answer format."""
        instructions = "Just provide your answer"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.STRING
    
    def test_detect_answer_format_chart(self):
        """Test detecting base64 format for chart requests."""
        instructions = "Create a chart showing the data"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.BASE64
    
    def test_detect_answer_format_visualization(self):
        """Test detecting base64 format for visualization requests."""
        instructions = "Generate a visualization of the results"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.BASE64
    
    def test_detect_answer_format_count(self):
        """Test detecting number format for count requests."""
        instructions = "Count the number of items"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.NUMBER
    
    def test_detect_answer_format_average(self):
        """Test detecting number format for average requests."""
        instructions = "Calculate the average value"
        
        parser = TaskParser()
        format = parser._detect_answer_format(instructions)
        
        assert format == AnswerFormat.NUMBER
    
    def test_extract_file_urls_multiple_formats(self):
        """Test extracting multiple file URLs with different formats."""
        instructions = """
        Download these files:
        - CSV: https://example.com/data.csv
        - PDF: https://example.com/report.pdf
        - JSON: https://example.com/config.json
        - Image: https://example.com/chart.png
        """
        
        parser = TaskParser()
        urls = parser._extract_file_urls(instructions)
        
        assert len(urls) == 4
        assert "https://example.com/data.csv" in urls
        assert "https://example.com/report.pdf" in urls
        assert "https://example.com/config.json" in urls
        assert "https://example.com/chart.png" in urls
    
    def test_extract_file_urls_removes_duplicates(self):
        """Test that duplicate file URLs are removed."""
        instructions = """
        Download https://example.com/data.csv
        Also get https://example.com/data.csv again
        """
        
        parser = TaskParser()
        urls = parser._extract_file_urls(instructions)
        
        assert len(urls) == 1
        assert urls[0] == "https://example.com/data.csv"
    
    def test_extract_file_urls_with_download_keyword(self):
        """Test extracting file URLs with 'download' keyword."""
        instructions = "download: https://example.com/file.xlsx"
        
        parser = TaskParser()
        urls = parser._extract_file_urls(instructions)
        
        assert len(urls) == 1
        assert "https://example.com/file.xlsx" in urls
    
    def test_extract_file_urls_cleans_punctuation(self):
        """Test that file URLs are cleaned of trailing punctuation."""
        instructions = "Get the file from https://example.com/data.csv."
        
        parser = TaskParser()
        urls = parser._extract_file_urls(instructions)
        
        assert len(urls) == 1
        assert urls[0] == "https://example.com/data.csv"
    
    def test_parse_quiz_page_with_file_urls(self):
        """Test parsing complete quiz page with file URLs."""
        instructions = """
        Task: Analyze the data from https://example.com/data.csv
        Submit to: https://example.com/submit
        Return the count as a number.
        """
        
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        html = f"<html><body><pre>{base64_content}</pre></body></html>"
        
        parser = TaskParser()
        task = parser.parse_quiz_page(html)
        
        assert task.instructions == instructions
        assert str(task.submit_url) == "https://example.com/submit"
        assert task.answer_format == AnswerFormat.NUMBER
        assert len(task.file_urls) == 1
        assert str(task.file_urls[0]) == "https://example.com/data.csv"
    
    def test_parse_quiz_page_complex_scenario(self):
        """Test parsing quiz page with multiple elements."""
        instructions = """
        Task: Download the PDF from https://example.com/report.pdf
        Extract data from page 3 and calculate the sum.
        Also get https://example.com/data.csv for additional info.
        Submit your answer to: https://api.example.com/submit
        """
        
        base64_content = base64.b64encode(instructions.encode('utf-8')).decode('utf-8')
        html = f"<html><body><div><code>{base64_content}</code></div></body></html>"
        
        parser = TaskParser()
        task = parser.parse_quiz_page(html)
        
        assert "Download the PDF" in task.instructions
        assert str(task.submit_url) == "https://api.example.com/submit"
        assert task.answer_format == AnswerFormat.NUMBER
        assert len(task.file_urls) == 2
        file_urls_str = [str(url) for url in task.file_urls]
        assert "https://example.com/report.pdf" in file_urls_str
        assert "https://example.com/data.csv" in file_urls_str
