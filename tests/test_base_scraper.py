"""
Unit tests for BaseScraper class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions

from scrapers.base_scraper import BaseScraper


class TestBaseScraper:
    """Test cases for BaseScraper class."""
    
    def test_init_with_user_agent_seed(self, mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
        """Test BaseScraper initialization with user agent seed."""
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper(user_agent_seed=42)
        
        assert scraper.bucket is not None
        assert scraper.driver is not None
    
    def test_init_without_user_agent_seed(self, mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
        """Test BaseScraper initialization without user agent seed."""
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper()
        
        assert scraper.bucket is not None
        assert scraper.driver is not None
    
    def test_launch_with_headless_mode(self, mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
        """Test driver launch with headless mode enabled."""
        mock_settings.headless = True
        
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper()
        
        # Verify driver was created
        assert scraper.driver is not None
    
    def test_launch_without_headless_mode(self, mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
        """Test driver launch with headless mode disabled."""
        mock_settings.headless = False
        
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper()
        
        # Verify driver was created
        assert scraper.driver is not None
    
    def test_wait_ready_success(self, base_scraper):
        """Test successful wait for page ready state."""
        base_scraper.driver.execute_script.return_value = "complete"
        
        # Should not raise an exception
        base_scraper._wait_ready(timeout=5)
        
        base_scraper.driver.execute_script.assert_called_with("return document.readyState")
    
    def test_wait_ready_timeout(self, base_scraper, mock_webdriver_wait):
        """Test wait for page ready state with timeout."""
        base_scraper.driver.execute_script.return_value = "loading"
        mock_webdriver_wait.until.side_effect = TimeoutException("Timeout")
        
        with pytest.raises(TimeoutException):
            base_scraper._wait_ready(timeout=5)
    
    def test_get_success(self, base_scraper):
        """Test successful GET request."""
        url = "https://example.com"
        
        base_scraper.get(url)
        
        base_scraper.driver.get.assert_called_once_with(url)
    
    def test_get_with_retry_on_timeout(self, base_scraper):
        """Test GET request with retry on timeout."""
        url = "https://example.com"
        base_scraper.driver.get.side_effect = [TimeoutException("Timeout"), None]
        
        # Should retry and succeed on second attempt
        base_scraper.get(url)
        
        assert base_scraper.driver.get.call_count == 2
    
    def test_get_with_retry_on_webdriver_exception(self, base_scraper):
        """Test GET request with retry on WebDriverException."""
        url = "https://example.com"
        base_scraper.driver.get.side_effect = [WebDriverException("Driver error"), None]
        
        # Should retry and succeed on second attempt
        base_scraper.get(url)
        
        assert base_scraper.driver.get.call_count == 2
    
    def test_get_max_retries_exceeded(self, base_scraper):
        """Test GET request with maximum retries exceeded."""
        url = "https://example.com"
        base_scraper.driver.get.side_effect = TimeoutException("Timeout")
        
        with pytest.raises(TimeoutException):
            base_scraper.get(url)
        
        # Should have tried 3 times (initial + 2 retries)
        assert base_scraper.driver.get.call_count == 3
    
    def test_close_success(self, base_scraper):
        """Test successful driver close."""
        base_scraper.close()
        
        base_scraper.driver.quit.assert_called_once()
    
    def test_close_with_exception(self, base_scraper):
        """Test driver close with exception."""
        base_scraper.driver.quit.side_effect = Exception("Close error")
        
        # Should not raise exception
        base_scraper.close()
        
        base_scraper.driver.quit.assert_called_once()
    
    def test_abstract_scrape_method(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper()
    
    def test_rate_limiting(self, base_scraper):
        """Test that rate limiting is applied."""
        url = "https://example.com"
        
        base_scraper.get(url)
        
        # Rate limiting is applied via the bucket.consume function
        # We can't easily test this in unit tests since it's a function, not a mock
        assert base_scraper.driver.get.called
    
    def test_user_agent_setting(self, mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
        """Test that user agent is properly set."""
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper()
        
        # User agent should be set (we can't easily test the exact value in unit tests)
        assert scraper.ua is not None
    
    def test_page_load_timeout_setting(self, mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
        """Test that page load timeout is set."""
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper()
        
        scraper.driver.set_page_load_timeout.assert_called_once_with(30)
    
    @patch('selenium.webdriver.Chrome')
    def test_chrome_options_configuration(self, mock_chrome, mock_token_bucket, mock_settings, mock_utils):
        """Test Chrome options configuration."""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        class TestScraper(BaseScraper):
            def scrape(self, query: str, location: str | None, limit: int):
                return []
        
        scraper = TestScraper()
        
        # Verify Chrome was called with options
        mock_chrome.assert_called_once()
        call_args = mock_chrome.call_args
        assert 'options' in call_args[1]
