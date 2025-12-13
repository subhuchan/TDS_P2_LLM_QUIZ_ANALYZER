"""Web scraper for downloading files from URLs."""

import asyncio
from typing import Dict, Optional

import aiohttp
from src.logging_config import get_logger

logger = get_logger(__name__)

# File size limit: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024

# Download timeout: 30 seconds
DOWNLOAD_TIMEOUT = 30

# Supported file formats
SUPPORTED_FORMATS = {
    'pdf', 'csv', 'json', 'txt',
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',
    'xlsx', 'xls', 'xml', 'html'
}


class WebScraper:
    """Web scraper for downloading files with authentication and validation."""
    
    def __init__(
        self,
        max_file_size: int = MAX_FILE_SIZE,
        timeout: int = DOWNLOAD_TIMEOUT
    ):
        """
        Initialize the web scraper.
        
        Args:
            max_file_size: Maximum file size in bytes (default 50MB)
            timeout: Download timeout in seconds (default 30)
        """
        self.max_file_size = max_file_size
        self.timeout = timeout
        logger.info(
            "web_scraper_initialized",
            max_file_size=max_file_size,
            timeout=timeout
        )
    
    async def download_file(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Download a file from the specified URL.
        
        Args:
            url: URL of the file to download
            headers: Optional authentication headers
        
        Returns:
            File content as bytes
        
        Raises:
            ValueError: If file format is not supported or size exceeds limit
            aiohttp.ClientError: If download fails
            asyncio.TimeoutError: If download times out
        """
        logger.info("downloading_file", url=url, has_headers=bool(headers))
        
        # Validate URL format
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {url}")
        
        # Extract file extension
        file_extension = self._extract_extension(url)
        if file_extension and file_extension not in SUPPORTED_FORMATS:
            logger.warning(
                "unsupported_file_format",
                url=url,
                extension=file_extension
            )
        
        # Set up timeout
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        # Prepare headers
        request_headers = headers or {}
        if 'User-Agent' not in request_headers:
            request_headers['User-Agent'] = (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=request_headers) as response:
                    # Check response status
                    response.raise_for_status()
                    
                    # Check content length if available
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        size = int(content_length)
                        if size > self.max_file_size:
                            raise ValueError(
                                f"File size ({size} bytes) exceeds maximum "
                                f"allowed size ({self.max_file_size} bytes)"
                            )
                    
                    # Download file with size validation
                    content = bytearray()
                    async for chunk in response.content.iter_chunked(8192):
                        content.extend(chunk)
                        if len(content) > self.max_file_size:
                            raise ValueError(
                                f"Downloaded content exceeds maximum "
                                f"allowed size ({self.max_file_size} bytes)"
                            )
                    
                    file_bytes = bytes(content)
                    logger.info(
                        "file_downloaded",
                        url=url,
                        size=len(file_bytes),
                        content_type=response.headers.get('Content-Type')
                    )
                    
                    return file_bytes
        
        except asyncio.TimeoutError:
            logger.error("download_timeout", url=url, timeout=self.timeout)
            raise
        except aiohttp.ClientError as e:
            logger.error("download_failed", url=url, error=str(e))
            raise
        except ValueError as e:
            logger.error("download_validation_failed", url=url, error=str(e))
            raise
        except Exception as e:
            logger.error("download_unexpected_error", url=url, error=str(e))
            raise
    
    def _extract_extension(self, url: str) -> Optional[str]:
        """
        Extract file extension from URL.
        
        Args:
            url: URL to extract extension from
        
        Returns:
            File extension without dot, or None if not found
        """
        # Remove query parameters and fragments
        url_path = url.split('?')[0].split('#')[0]
        
        # Get the last path component (filename)
        if '/' in url_path:
            filename = url_path.rsplit('/', 1)[-1]
        else:
            filename = url_path
        
        # Extract extension from filename
        if '.' in filename:
            extension = filename.rsplit('.', 1)[-1].lower()
            # Validate it looks like a file extension (no slashes, reasonable length)
            if '/' not in extension and len(extension) <= 10:
                return extension
        
        return None
    
    async def scrape_webpage(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        use_js: bool = False
    ) -> str:
        """
        Scrape webpage content.
        
        Args:
            url: URL of the webpage to scrape
            headers: Optional authentication headers
            use_js: Whether to use JavaScript rendering (requires browser)
        
        Returns:
            HTML content as string
        
        Raises:
            NotImplementedError: If use_js is True (requires BrowserManager)
            aiohttp.ClientError: If scraping fails
            asyncio.TimeoutError: If scraping times out
        """
        if use_js:
            raise NotImplementedError(
                "JavaScript rendering requires BrowserManager. "
                "Use BrowserManager.fetch_and_render() instead."
            )
        
        logger.info("scraping_webpage", url=url, has_headers=bool(headers))
        
        # Set up timeout
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        # Prepare headers
        request_headers = headers or {}
        if 'User-Agent' not in request_headers:
            request_headers['User-Agent'] = (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=request_headers) as response:
                    response.raise_for_status()
                    html = await response.text()
                    
                    logger.info(
                        "webpage_scraped",
                        url=url,
                        size=len(html)
                    )
                    
                    return html
        
        except asyncio.TimeoutError:
            logger.error("scrape_timeout", url=url, timeout=self.timeout)
            raise
        except aiohttp.ClientError as e:
            logger.error("scrape_failed", url=url, error=str(e))
            raise
        except Exception as e:
            logger.error("scrape_unexpected_error", url=url, error=str(e))
            raise
