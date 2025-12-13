"""Unit tests for web scraper."""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import aiohttp

from src.web_scraper import WebScraper


@pytest.mark.asyncio
class TestWebScraper:
    """Test suite for WebScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create WebScraper instance."""
        return WebScraper()
    
    async def test_download_file_success(self, scraper):
        """Test successful file download."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.raise_for_status = Mock()
        
        async def mock_iter_chunked(size):
            yield b"test file content"
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.download_file("https://example.com/file.pdf")
            
            assert content == b"test file content"
    
    async def test_download_file_with_headers(self, scraper):
        """Test file download with authentication headers."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.raise_for_status = Mock()
        
        async def mock_iter_chunked(size):
            yield b"authenticated content"
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        headers = {"Authorization": "Bearer token123"}
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_get = mock_session.get
        mock_get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.download_file(
                "https://example.com/file.pdf",
                headers=headers
            )
            
            assert content == b"authenticated content"
            # Verify headers were passed
            call_args = mock_get.call_args
            assert 'Authorization' in call_args[1].get('headers', {})
    
    async def test_download_file_timeout(self, scraper):
        """Test file download timeout handling."""
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.side_effect = asyncio.TimeoutError("Timeout")
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(asyncio.TimeoutError):
                await scraper.download_file("https://example.com/file.pdf")
    
    async def test_download_file_404(self, scraper):
        """Test file download with 404 error."""
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.raise_for_status = Mock(side_effect=aiohttp.ClientResponseError(
            request_info=Mock(),
            history=(),
            status=404,
            message="Not Found"
        ))
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(aiohttp.ClientResponseError):
                await scraper.download_file("https://example.com/missing.pdf")
    
    async def test_download_csv_file(self, scraper):
        """Test downloading CSV file."""
        csv_content = b"name,age\nJohn,30\nJane,25"
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'text/csv'}
        mock_response.raise_for_status = Mock()
        
        async def mock_iter_chunked(size):
            yield csv_content
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.download_file("https://example.com/data.csv")
            
            assert content == csv_content
    
    async def test_download_json_file(self, scraper):
        """Test downloading JSON file."""
        json_content = b'{"key": "value"}'
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/json'}
        mock_response.raise_for_status = Mock()
        
        async def mock_iter_chunked(size):
            yield json_content
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.download_file("https://example.com/data.json")
            
            assert content == json_content
    
    async def test_download_image_file(self, scraper):
        """Test downloading image file."""
        image_content = b"\x89PNG\r\n\x1a\n"  # PNG header
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'image/png'}
        mock_response.raise_for_status = Mock()
        
        async def mock_iter_chunked(size):
            yield image_content
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.download_file("https://example.com/image.png")
            
            assert content == image_content
    
    async def test_download_large_file(self, scraper):
        """Test downloading large file."""
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Type': 'application/pdf'}
        mock_response.raise_for_status = Mock()
        
        async def mock_iter_chunked(size):
            yield large_content
        
        mock_response.content.iter_chunked = mock_iter_chunked
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.download_file("https://example.com/large.pdf")
            
            assert len(content) == 10 * 1024 * 1024
    
    async def test_scrape_webpage_without_js(self, scraper):
        """Test scraping webpage without JavaScript."""
        html_content = "<html><body>Test content</body></html>"
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = Mock()
        mock_response.text = AsyncMock(return_value=html_content)
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content = await scraper.scrape_webpage("https://example.com", use_js=False)
            
            assert content == html_content
    
    async def test_connection_error(self, scraper):
        """Test handling connection errors."""
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.side_effect = aiohttp.ClientConnectorError(
            connection_key=Mock(),
            os_error=OSError("Connection failed")
        )
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(aiohttp.ClientConnectorError):
                await scraper.download_file("https://example.com/file.pdf")
    
    async def test_multiple_downloads(self, scraper):
        """Test multiple file downloads."""
        mock_response1 = AsyncMock()
        mock_response1.status = 200
        mock_response1.headers = {'Content-Type': 'application/pdf'}
        mock_response1.raise_for_status = Mock()
        
        async def mock_iter_chunked1(size):
            yield b"file1"
        
        mock_response1.content.iter_chunked = mock_iter_chunked1
        
        mock_response2 = AsyncMock()
        mock_response2.status = 200
        mock_response2.headers = {'Content-Type': 'application/pdf'}
        mock_response2.raise_for_status = Mock()
        
        async def mock_iter_chunked2(size):
            yield b"file2"
        
        mock_response2.content.iter_chunked = mock_iter_chunked2
        
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.side_effect = [mock_response1, mock_response2]
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            content1 = await scraper.download_file("https://example.com/file1.pdf")
            content2 = await scraper.download_file("https://example.com/file2.pdf")
            
            assert content1 == b"file1"
            assert content2 == b"file2"
