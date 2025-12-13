"""Browser manager for rendering JavaScript-based quiz pages."""

import asyncio
import logging
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

from src.error_handler import error_handler, BrowserError, TimeoutError as QuizTimeoutError

# Use standard logging to avoid circular dependencies
logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages headless browser for rendering JavaScript-based pages."""
    
    def __init__(
        self,
        timeout: int = 30000,
        max_retries: int = 2,
        headless: bool = True
    ):
        """
        Initialize the browser manager.
        
        Args:
            timeout: Page load timeout in milliseconds (default 30 seconds)
            max_retries: Maximum number of retry attempts for failed operations
            headless: Whether to run browser in headless mode
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        
        logger.info(
            f"BrowserManager initialized: timeout={timeout}ms, max_retries={max_retries}, headless={headless}"
        )
    
    async def _launch_browser(self) -> None:
        """Launch the browser instance."""
        if self._browser is not None:
            logger.debug("Browser already running")
            return
        
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
            self._context = await self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            logger.info("Browser launched successfully")
            
        except Exception as e:
            browser_error = BrowserError(
                f"Failed to launch browser: {str(e)}",
                original_error=e
            )
            error_handler.handle_error(browser_error, "browser_launch")
            logger.error(f"Browser launch failed: {e}")
            await self.cleanup()
            raise browser_error
    
    async def fetch_and_render(self, url: str) -> str:
        """
        Fetch URL and return fully rendered HTML after JavaScript execution.
        
        Args:
            url: Quiz page URL to fetch and render
        
        Returns:
            Rendered HTML content as string
        
        Raises:
            Exception: If page fails to load after all retry attempts
        """
        logger.info(f"Fetching URL: {url}")
        
        for attempt in range(self.max_retries):
            try:
                # Ensure browser is launched
                await self._launch_browser()
                
                # Create new page
                page: Page = await self._context.new_page()
                
                try:
                    # Navigate to URL with timeout
                    logger.debug(
                        f"Navigating to URL (attempt {attempt + 1}/{self.max_retries}): {url}"
                    )
                    
                    await page.goto(
                        url,
                        wait_until="networkidle",
                        timeout=self.timeout
                    )
                    
                    # Wait for any dynamic content to load
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # Additional wait for JavaScript to inject content
                    # Wait for either base64 content or a reasonable timeout
                    try:
                        await page.wait_for_function(
                            "document.body.innerText.length > 500 || document.querySelectorAll('pre, code').length > 0",
                            timeout=5000
                        )
                    except PlaywrightTimeoutError:
                        # Content might be in a different format, continue anyway
                        logger.warning(f"Content wait timeout for {url}, proceeding with current content")
                    
                    # Get the rendered HTML
                    html_content = await page.content()
                    
                    logger.info(
                        f"Page rendered successfully: {url} (length: {len(html_content)} chars)"
                    )
                    
                    return html_content
                    
                finally:
                    # Always close the page to free resources
                    await page.close()
                    
            except PlaywrightTimeoutError as e:
                timeout_error = QuizTimeoutError(
                    f"Page load timeout for {url}",
                    original_error=e,
                    context={"url": url, "attempt": attempt + 1}
                )
                error_handler.handle_error(
                    timeout_error,
                    "page_load_timeout",
                    {"url": url, "attempt": attempt + 1, "max_retries": self.max_retries}
                )
                logger.warning(
                    f"Page load timeout (attempt {attempt + 1}/{self.max_retries}): {url} - {e}"
                )
                
                if attempt == self.max_retries - 1:
                    logger.error(f"Page load failed after all retries: {url}")
                    raise timeout_error
                
                # Wait before retry
                await asyncio.sleep(1)
                
            except Exception as e:
                browser_error = BrowserError(
                    f"Browser error while fetching {url}: {str(e)}",
                    original_error=e,
                    context={"url": url, "attempt": attempt + 1}
                )
                error_handler.handle_error(
                    browser_error,
                    "browser_fetch",
                    {"url": url, "attempt": attempt + 1, "max_retries": self.max_retries}
                )
                logger.error(
                    f"Browser error (attempt {attempt + 1}/{self.max_retries}): {url} - {type(e).__name__}: {e}"
                )
                
                if attempt == self.max_retries - 1:
                    logger.error(f"Fetch failed after all retries: {url}")
                    raise browser_error
                
                # Cleanup and retry with fresh browser
                await self.cleanup()
                await asyncio.sleep(1)
        
        # Should not reach here, but just in case
        raise Exception(f"Failed to fetch page: {url}")
    
    async def cleanup(self) -> None:
        """Close browser and release resources."""
        logger.info("Cleaning up browser")
        
        try:
            if self._context is not None:
                await self._context.close()
                self._context = None
                logger.debug("Browser context closed")
            
            if self._browser is not None:
                await self._browser.close()
                self._browser = None
                logger.debug("Browser closed")
            
            if self._playwright is not None:
                await self._playwright.stop()
                self._playwright = None
                logger.debug("Playwright stopped")
            
            logger.info("Browser cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            # Don't raise - cleanup should be best-effort
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._launch_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
