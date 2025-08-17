from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException
from rate_limiter.rate_limit import TokenBucket
from utils.utils import choose_user_agent
from configs.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class BaseScraper(ABC):
    """
    Base Selenium scraper with:
      - Headless Chrome
      - Random User-Agent per run
      - Token-bucket throttle (≤ requests_per_sec)
      - Retries with exponential backoff
      - 'network idle' approximation via document.readyState
    """
    def __init__(self, user_agent_seed: int | None = None):
        self.bucket = TokenBucket(rate_per_sec=settings.requests_per_sec, capacity=1)
        self.ua = choose_user_agent(user_agent_seed)
        self.driver = self._launch()

    def _launch(self):
        opts = webdriver.ChromeOptions()
        if settings.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-plugins")
        opts.add_argument("--disable-images")
        opts.add_argument("--window-size=1366,900")
        opts.add_argument(f"--user-agent={self.ua}")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-web-security")
        opts.add_argument("--allow-running-insecure-content")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        
        # Use explicit ChromeDriver path in Docker container
        max_retries = 3
        for attempt in range(max_retries):
            try:
                from selenium.webdriver.chrome.service import Service
                # Try explicit ChromeDriver path first (for Docker)
                service = Service(executable_path="/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=opts)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                driver.set_page_load_timeout(30)
                return driver
            except Exception as e:
                logger.warning(f"Chrome driver launch attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Last attempt, try with Selenium Manager
                    try:
                        driver = webdriver.Chrome(options=opts)
                        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                        driver.set_page_load_timeout(30)
                        return driver
                    except Exception as manager_error:
                        logger.error(f"All Chrome driver launch attempts failed: {manager_error}")
                        raise
                time.sleep(2)  # Wait before retry

    def _wait_ready(self, timeout: int = 30):
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((TimeoutException, WebDriverException)),
        reraise=True,
    )
    def get(self, url: str):
        """Rate-limited navigation with retries and DOM readiness wait."""
        self.bucket.consume(1)
        self.driver.get(url)
        self._wait_ready()

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    @abstractmethod
    def scrape(self, query: str, limit: int, location: str | None = None) -> Iterable[Dict[str, Any]]:
        ...