"""Task parser for extracting quiz instructions from rendered HTML pages."""

import base64
import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.logging_config import get_logger
from src.models import AnswerFormat, TaskDefinition

logger = get_logger(__name__)


class TaskParser:
    """Parser for extracting task definitions from quiz HTML pages."""
    
    def __init__(self):
        """Initialize the task parser."""
        self.logger = logger
    
    def parse_quiz_page(self, html: str, base_url: str = "") -> TaskDefinition:
        """
        Parse rendered HTML to extract task details.
        
        Args:
            html: Rendered HTML content from quiz page
            base_url: Base URL for resolving relative URLs
        
        Returns:
            TaskDefinition with instructions, submit_url, and answer_format
        
        Raises:
            ValueError: If required elements cannot be extracted
        """
        self.logger.info("parsing_quiz_page", html_length=len(html))
        
        # Special handling for /project2 entry page (instruction page)
        if "/project2" in base_url and "How to play:" in html:
            self.logger.info("detected_project2_entry_page", base_url=base_url)
            return TaskDefinition(
                instructions="Project 2 entry page: Submit 'start' to begin the quiz sequence.",
                submit_url="https://tds-llm-analysis.s-anand.net/submit",
                answer_format=AnswerFormat.STRING,
                file_urls=[],
                additional_context={"is_entry_page": True, "suggested_answer": "start"}
            )
        
        # Special handling for /demo page (documentation page)
        if "/demo" in base_url and "POST this JSON" in html:
            self.logger.info("detected_demo_page", base_url=base_url)
            # Demo page just wants any answer to proceed to real quiz
            return TaskDefinition(
                instructions="Demo page: Submit any answer to proceed to the actual quiz.",
                submit_url="https://tds-llm-analysis.s-anand.net/submit",
                answer_format=AnswerFormat.STRING,
                file_urls=[],
                additional_context={"is_demo": True}
            )
        
        # Try to extract base64 content first
        try:
            base64_content = self._extract_base64_content(html)
            # Decode task instructions
            instructions = self._decode_base64(base64_content)
            self.logger.info("decoded_instructions", length=len(instructions))
        except ValueError as e:
            # No base64 found, try to parse plain HTML instructions
            self.logger.info("no_base64_found_parsing_plain_html", error=str(e))
            instructions = self._extract_plain_html_instructions(html)
            self.logger.info("extracted_plain_html_instructions", length=len(instructions))
        
        # Parse submit endpoint URL
        submit_url = self._parse_submit_url(instructions, base_url)
        
        # Detect answer format
        answer_format = self._detect_answer_format(instructions)
        
        # Extract file download URLs
        file_urls = self._extract_file_urls(instructions, base_url)
        
        task_definition = TaskDefinition(
            instructions=instructions,
            submit_url=submit_url,
            answer_format=answer_format,
            file_urls=file_urls,
            additional_context={}
        )
        
        self.logger.info(
            "task_parsed",
            submit_url=str(submit_url),
            answer_format=answer_format.value,
            file_count=len(file_urls)
        )
        
        return task_definition
    
    def _extract_base64_content(self, html: str) -> str:
        """
        Extract base64-encoded content from HTML.
        
        Args:
            html: HTML content to parse
        
        Returns:
            Base64-encoded string
        
        Raises:
            ValueError: If base64 content cannot be found
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for common patterns where base64 content might be stored
        # Pattern 1: In a <pre> or <code> tag with base64 content
        for tag in soup.find_all(['pre', 'code', 'div', 'span']):
            text = tag.get_text().strip()
            if self._is_base64(text):
                self.logger.info("found_base64_in_tag", tag_name=tag.name)
                return text
        
        # Pattern 2: In data attributes
        for tag in soup.find_all(attrs={'data-task': True}):
            content = tag.get('data-task', '')
            if self._is_base64(content):
                self.logger.info("found_base64_in_data_attribute")
                return content
        
        # Pattern 3: In script tags (JSON data)
        for script in soup.find_all('script'):
            script_text = script.get_text()
            # Look for base64 patterns in JavaScript
            base64_match = re.search(r'["\']([A-Za-z0-9+/]{20,}={0,2})["\']', script_text)
            if base64_match:
                potential_base64 = base64_match.group(1)
                if self._is_base64(potential_base64):
                    self.logger.info("found_base64_in_script")
                    return potential_base64
        
        # Pattern 4: Search entire HTML for base64-like strings
        base64_pattern = re.compile(r'\b([A-Za-z0-9+/]{40,}={0,2})\b')
        matches = base64_pattern.findall(html)
        for match in matches:
            if self._is_base64(match):
                self.logger.info("found_base64_in_html_text")
                return match
        
        raise ValueError("Could not find base64-encoded content in HTML")
    
    def _is_base64(self, s: str) -> bool:
        """
        Check if a string appears to be valid base64.
        
        Args:
            s: String to check
        
        Returns:
            True if string appears to be base64
        """
        if not s or len(s) < 20:
            return False
        
        # Base64 should only contain these characters
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', s):
            return False
        
        # Try to decode to verify
        try:
            decoded = base64.b64decode(s, validate=True)
            # Check if decoded content is printable text
            return len(decoded) > 0
        except Exception:
            return False
    
    def _decode_base64(self, base64_content: str) -> str:
        """
        Decode base64 content to human-readable text.
        
        Args:
            base64_content: Base64-encoded string
        
        Returns:
            Decoded text
        
        Raises:
            ValueError: If decoding fails
        """
        try:
            decoded_bytes = base64.b64decode(base64_content)
            decoded_text = decoded_bytes.decode('utf-8')
            return decoded_text
        except Exception as e:
            self.logger.error("base64_decode_failed", error=str(e))
            raise ValueError(f"Failed to decode base64 content: {e}")
    
    def _extract_plain_html_instructions(self, html: str) -> str:
        """
        Extract task instructions from plain HTML (when no base64 encoding is used).
        
        Args:
            html: HTML content to parse
        
        Returns:
            Extracted instruction text
        
        Raises:
            ValueError: If instructions cannot be extracted
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not text or len(text) < 10:
            raise ValueError("Could not extract meaningful instructions from HTML")
        
        self.logger.info("extracted_plain_text", length=len(text))
        return text
    
    def _parse_submit_url(self, instructions: str, base_url: str = "") -> str:
        """
        Parse submit endpoint URL from task instructions.
        
        Args:
            instructions: Decoded task instructions
            base_url: Base URL for resolving relative URLs
        
        Returns:
            Submit endpoint URL
        
        Raises:
            ValueError: If submit URL cannot be found
        """
        # Pattern 1: Look for any URL in the instructions first (most reliable)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, instructions)
        if urls:
            # Prefer URLs with "submit" in them
            for url in urls:
                if 'submit' in url.lower():
                    self.logger.info("found_submit_url_with_keyword", url=url)
                    return self._clean_url(url)
            # Otherwise return the first URL found
            self.logger.info("found_first_url", url=urls[0])
            return self._clean_url(urls[0])
        
        # Pattern 2: Look for explicit "submit" or "endpoint" keywords with URLs
        url_patterns = [
            r'submit\s+(?:to|at|endpoint)[:\s]+(https?://[^\s\n]+)',
            r'endpoint[:\s]+(https?://[^\s\n]+)',
            r'POST\s+(?:to|at)[:\s]+(https?://[^\s\n]+)',
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, instructions, re.IGNORECASE)
            if match:
                url = match.group(1).strip()
                url = self._clean_url(url)
                if base_url and not urlparse(url).scheme:
                    url = urljoin(base_url, url)
                self.logger.info("found_submit_url", url=url, pattern=pattern)
                return url
        
        raise ValueError("Could not find submit URL in instructions")
    
    def _clean_url(self, url: str) -> str:
        """
        Clean URL by removing trailing punctuation and whitespace.
        
        Args:
            url: URL to clean
        
        Returns:
            Cleaned URL
        """
        # Remove trailing punctuation that might be part of sentence
        url = url.rstrip('.,;:!?)')
        # Remove quotes
        url = url.strip('\'"')
        return url
    
    def _detect_answer_format(self, instructions: str) -> AnswerFormat:
        """
        Detect required answer format from task description.
        
        Args:
            instructions: Task instructions
        
        Returns:
            Detected AnswerFormat
        """
        instructions_lower = instructions.lower()
        
        # Check for explicit format mentions
        if 'base64' in instructions_lower or 'data:image' in instructions_lower or 'chart' in instructions_lower or 'visualization' in instructions_lower or 'image' in instructions_lower:
            self.logger.info("detected_format", format="base64")
            return AnswerFormat.BASE64
        
        if 'json' in instructions_lower or 'object' in instructions_lower or '{' in instructions:
            self.logger.info("detected_format", format="json")
            return AnswerFormat.JSON
        
        if 'true' in instructions_lower or 'false' in instructions_lower or 'boolean' in instructions_lower or 'yes/no' in instructions_lower:
            self.logger.info("detected_format", format="boolean")
            return AnswerFormat.BOOLEAN
        
        if 'number' in instructions_lower or 'count' in instructions_lower or 'sum' in instructions_lower or 'average' in instructions_lower or 'total' in instructions_lower:
            self.logger.info("detected_format", format="number")
            return AnswerFormat.NUMBER
        
        # Default to string if no specific format detected
        self.logger.info("detected_format", format="string")
        return AnswerFormat.STRING
    
    def _extract_file_urls(self, instructions: str, base_url: str = "") -> List[str]:
        """
        Extract file download URLs from instructions.
        
        Args:
            instructions: Task instructions
            base_url: Base URL for resolving relative URLs
        
        Returns:
            List of file URLs
        """
        file_urls = []
        
        # Pattern 1: Look for URLs with file extensions
        file_extensions = r'\.(pdf|csv|json|xlsx|xls|txt|png|jpg|jpeg|gif|mp3|wav|mp4)'
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+' + file_extensions
        matches = re.findall(url_pattern, instructions, re.IGNORECASE)
        
        for match in matches:
            # match is a tuple (url, extension), we need the full match
            pass
        
        # Better approach: find all URLs then filter by extension
        all_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', instructions)
        for url in all_urls:
            url = self._clean_url(url)
            # Check if URL has a file extension
            if re.search(file_extensions, url, re.IGNORECASE):
                if base_url and not urlparse(url).scheme:
                    url = urljoin(base_url, url)
                file_urls.append(url)
        
        # Pattern 2: Look for download links mentioned explicitly
        download_pattern = r'download[:\s]+([^\s\n]+)'
        download_matches = re.findall(download_pattern, instructions, re.IGNORECASE)
        for match in download_matches:
            url = self._clean_url(match)
            if url.startswith('http'):
                file_urls.append(url)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in file_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        self.logger.info("extracted_file_urls", count=len(unique_urls))
        return unique_urls
