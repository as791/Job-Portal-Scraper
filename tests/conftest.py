"""
Pytest configuration and fixtures for scraper tests.
"""
import pytest
from unittest.mock import Mock, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime, timezone

from scrapers.base_scraper import BaseScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.naukri_scraper import NaukriScraper
from configs.settings import settings


@pytest.fixture
def mock_webdriver(mocker):
    """Mock Selenium WebDriver."""
    mock_driver = Mock(spec=webdriver.Chrome)
    mock_driver.get = Mock()
    mock_driver.quit = Mock()
    mock_driver.set_page_load_timeout = Mock()
    mock_driver.execute_script = Mock(return_value="complete")
    mock_driver.current_url = "https://example.com"
    
    # Mock find_elements to return empty list by default
    mock_driver.find_elements = Mock(return_value=[])
    mock_driver.find_element = Mock(side_effect=Exception("Element not found"))
    
    mocker.patch('selenium.webdriver.Chrome', return_value=mock_driver)
    return mock_driver


@pytest.fixture
def mock_token_bucket(mocker):
    """Mock TokenBucket for rate limiting."""
    mock_bucket = Mock()
    mock_bucket.consume = Mock()
    mocker.patch('rate_limiter.rate_limit.TokenBucket', return_value=mock_bucket)
    return mock_bucket


@pytest.fixture
def mock_webdriver_wait(mocker):
    """Mock WebDriverWait."""
    mock_wait = Mock()
    mock_wait.until = Mock()
    mocker.patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait)
    return mock_wait


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        "source": "linkedin",
        "mode": "dynamic",
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "New York, NY",
        "salary": "$100,000 - $150,000",
        "salary_min": 100000,
        "salary_max": 150000,
        "currency": "USD",
        "tags": ["python", "django", "senior"],
        "posted_date": datetime.now(timezone.utc),
        "job_url": "https://example.com/job/123",
        "is_remote": False,
    }


@pytest.fixture
def mock_linkedin_job_elements():
    """Mock LinkedIn job elements."""
    elements = []
    for i in range(3):
        mock_element = Mock(spec=WebElement)
        
        # Mock title element
        mock_title = Mock(spec=WebElement)
        mock_title.text = f"Software Engineer {i+1}"
        
        # Mock company element
        mock_company = Mock(spec=WebElement)
        mock_company.text = f"Company {i+1}"
        
        # Mock location element
        mock_location = Mock(spec=WebElement)
        mock_location.text = f"Location {i+1}"
        
        # Mock date element
        mock_date = Mock(spec=WebElement)
        mock_date.get_attribute.return_value = "2024-01-01"
        
        # Mock link element
        mock_link = Mock(spec=WebElement)
        mock_link.get_attribute.return_value = f"https://linkedin.com/job/{i+1}"
        
        # Setup find_elements for the job element
        mock_element.find_elements.side_effect = lambda selector, **kwargs: {
            "a.base-card__full-link": [mock_link],
            "h3.base-search-card__title": [mock_title],
            "h4.base-search-card__subtitle a, h4.base-search-card__subtitle": [mock_company],
            "span.job-search-card__location": [mock_location],
            "time": [mock_date],
        }.get(selector, [])
        
        elements.append(mock_element)
    
    return elements


@pytest.fixture
def mock_naukri_job_elements():
    """Mock Naukri job elements."""
    elements = []
    for i in range(3):
        mock_element = Mock(spec=WebElement)
        
        # Mock title element
        mock_title = Mock(spec=WebElement)
        mock_title.text = f"Python Developer {i+1}"
        mock_title.get_attribute.return_value = f"https://naukri.com/job/{i+1}"
        
        # Mock company element
        mock_company = Mock(spec=WebElement)
        mock_company.text = f"Naukri Company {i+1}"
        
        # Mock location element
        mock_location = Mock(spec=WebElement)
        mock_location.text = f"Bangalore {i+1}"
        
        # Mock salary element
        mock_salary = Mock(spec=WebElement)
        mock_salary.text = f"{10+i} LPA"
        
        # Mock date element
        mock_date = Mock(spec=WebElement)
        mock_date.text = "2 days ago"
        
        # Mock tag elements
        mock_tags = []
        for tag in ["python", "django", "sql"]:
            mock_tag = Mock(spec=WebElement)
            mock_tag.text = tag
            mock_tags.append(mock_tag)
        
        # Setup find_element and find_elements for the job element
        def find_element_side_effect(selector, **kwargs):
            if "a.title" in selector or "a" in selector:
                return mock_title
            elif "a.subTitle" in selector or "span.org" in selector:
                return mock_company
            else:
                raise Exception("Element not found")
        
        def find_elements_side_effect(selector, **kwargs):
            if "li.location span.location" in selector:
                return [mock_location]
            elif "li.salary span" in selector:
                return [mock_salary]
            elif "span.job-post-day" in selector:
                return [mock_date]
            elif "a.title" in selector:
                return [mock_title]
            elif "ul.tags li a" in selector:
                return mock_tags
            else:
                return []
        
        mock_element.find_element.side_effect = find_element_side_effect
        mock_element.find_elements.side_effect = find_elements_side_effect
        
        elements.append(mock_element)
    
    return elements


@pytest.fixture
def mock_settings(mocker):
    """Mock settings for testing."""
    mock_settings = Mock()
    mock_settings.requests_per_sec = 1.0
    mock_settings.headless = True
    mock_settings.timezone = "UTC"
    mock_settings.linkedin_email = None
    mock_settings.linkedin_password = None
    mocker.patch('configs.settings.settings', mock_settings)
    return mock_settings


@pytest.fixture
def mock_utils(mocker):
    """Mock utility functions."""
    mocker.patch('utils.utils.choose_user_agent', return_value="Mozilla/5.0 Test")
    mocker.patch('utils.utils.parse_salary', return_value=(50000, 100000, "USD"))
    mocker.patch('utils.utils.parse_posted_date', return_value=datetime.now(timezone.utc))
    mocker.patch('utils.utils.derive_is_remote', return_value=False)
    mocker.patch('utils.utils.to_tags', return_value=["python", "django"])


@pytest.fixture
def base_scraper(mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
    """Create a base scraper instance for testing."""
    class TestScraper(BaseScraper):
        def scrape(self, query: str, location: str | None, limit: int):
            return []
    
    return TestScraper()


@pytest.fixture
def linkedin_scraper(mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
    """Create a LinkedIn scraper instance for testing."""
    return LinkedInScraper()


@pytest.fixture
def naukri_scraper(mock_webdriver, mock_token_bucket, mock_settings, mock_utils):
    """Create a Naukri scraper instance for testing."""
    return NaukriScraper()
