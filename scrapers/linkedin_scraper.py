from typing import Dict, Any, Iterable, List, Optional
from urllib.parse import urlencode

from scrapers.base_scraper import BaseScraper
from utils.utils import parse_salary, parse_posted_date, derive_is_remote
from configs.settings import settings
from utils.logger import get_logger

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = get_logger(__name__)


class LinkedInScraper(BaseScraper):
    """
    Public (no-login) LinkedIn Jobs scraper.

    - Uses only publicly accessible search pages.
    - Paginates with the `start` parameter: 0, 25, 50, ...
    - Respects rate limits via the base TokenBucket.
    - Does NOT attempt to bypass CAPTCHAs or other access controls.
    - Always review LinkedIn's Terms before running.

    Example search URL pattern:
      https://www.linkedin.com/jobs/search/?keywords=python&location=India&start=0
    """
    LI_SEARCH_BASE = "https://www.linkedin.com/jobs/search"

    def scrape(self, query: str, limit: int, location: Optional[str] = None) -> Iterable[Dict[str, Any]]:
        q = (query or "software engineer").strip()
        loc = location.strip() if location else "India"

        count = 0
        start = 0
        page_size = 25  # LinkedIn usually shows ~25 results per page

        try:
            while count < limit:
                params = {"keywords": q, "location": loc, "start": start}
                url = f"{self.LI_SEARCH_BASE}?{urlencode(params)}"

                # Navigate (rate-limited + retries handled in base)
                try:
                    self.get(url)
                except Exception as e:
                    logger.warning(f"Failed to navigate to LinkedIn page: {e}")
                    break

                # Wait for list container (best-effort; public pages can vary)
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.jobs-search__results-list li"))
                    )
                except TimeoutException:
                    logger.warning("Timeout waiting for LinkedIn job results")
                    break
                
                items = self.driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")
                if not items:
                    logger.info("No more LinkedIn job results found")
                    break  # no more public results

                for li in items:
                    try:
                        # Try multiple selectors for job URL
                        url_selectors = [
                            "a.base-card__full-link",
                            "a[data-control-name='job_card_click']",
                            "a[href*='/jobs/view/']",
                            "a[href*='linkedin.com/jobs']"
                        ]
                        job_url = ""
                        for selector in url_selectors:
                            a = li.find_elements(By.CSS_SELECTOR, selector)
                            if a:
                                job_url = a[0].get_attribute("href")
                                break

                        # Try multiple selectors for job title
                        title_selectors = [
                            "h3.base-search-card__title",
                            "h3[data-testid='job-search-card__title']",
                            "h3.job-search-card__title",
                            "a[data-control-name='job_card_click'] h3",
                            "h3",
                            "a[href*='/jobs/view/'] h3"
                        ]
                        title = ""
                        for selector in title_selectors:
                            title_el = li.find_elements(By.CSS_SELECTOR, selector)
                            if title_el and title_el[0].text.strip():
                                title = title_el[0].text.strip()
                                break

                        # Try multiple selectors for company name
                        company_selectors = [
                            "h4.base-search-card__subtitle a",
                            "h4.base-search-card__subtitle",
                            "span.job-search-card__company-name",
                            "a[data-control-name='job_card_company_click']",
                            "h4"
                        ]
                        company = ""
                        for selector in company_selectors:
                            company_el = li.find_elements(By.CSS_SELECTOR, selector)
                            if company_el and company_el[0].text.strip():
                                company = company_el[0].text.strip()
                                break

                        # Try multiple selectors for location
                        location_selectors = [
                            "span.job-search-card__location",
                            "span[data-testid='job-search-card__location']",
                            "span.location",
                            "li.job-search-card__location"
                        ]
                        location_text = ""
                        for selector in location_selectors:
                            loc_el = li.find_elements(By.CSS_SELECTOR, selector)
                            if loc_el and loc_el[0].text.strip():
                                location_text = loc_el[0].text.strip()
                                break

                        # Try multiple selectors for date
                        date_selectors = [
                            "time",
                            "time[datetime]",
                            "span.job-search-card__listdate",
                            "span[data-testid='job-search-card__listdate']"
                        ]
                        date_text = "today"
                        for selector in date_selectors:
                            time_el = li.find_elements(By.CSS_SELECTOR, selector)
                            if time_el:
                                date_text = time_el[0].get_attribute("datetime") or time_el[0].text.strip() or "today"
                                break

                        # Salary is rarely shown in public list results; keep None
                        salary_text = None
                        salary_min, salary_max, currency = parse_salary(salary_text)
                        
                        # Enhanced tags including search context and extracted data
                        enhanced_tags = []
                        if query:
                            enhanced_tags.extend([f"search:{query}", f"query:{query}"])
                        if location:
                            enhanced_tags.extend([f"location:{location}", f"search_location:{location}"])
                        if location_text:
                            enhanced_tags.extend([f"job_location:{location_text}"])
                        if company:
                            enhanced_tags.extend([f"company:{company}"])
                        enhanced_tags.extend(["source:linkedin", "mode:dynamic"])

                        posted_date = parse_posted_date(date_text, settings.timezone)
                        is_remote = derive_is_remote(title, location_text, enhanced_tags)
                        if is_remote:
                            enhanced_tags.append("remote")

                        yield {
                            "source": "linkedin",
                            "mode": "dynamic",
                            "title": title,
                            "company": company,
                            "location": location_text,
                            "salary": salary_text,
                            "salary_min": salary_min,
                            "salary_max": salary_max,
                            "currency": currency,
                            "tags": enhanced_tags,
                            "posted_date": posted_date,
                            "job_url": job_url,
                            "is_remote": is_remote,
                        }
                        count += 1
                        if count >= limit:
                            break
                    except Exception:
                        # Skip card parsing errors and continue
                        continue

                # If the page returned fewer than a full page, stop
                if len(items) < page_size:
                    break

                # Next public page
                start += page_size
        finally:
            self.close()