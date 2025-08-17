from typing import Dict, Any, Iterable, Optional
from scrapers.base_scraper import BaseScraper
from utils.utils import parse_salary, parse_posted_date, to_tags, derive_is_remote
from configs.settings import settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.logger import get_logger

logger = get_logger(__name__)

NAUKRI_SEARCH_WITH_LOCATION_URL = "https://www.naukri.com/{query}-jobs-in-{location}-{page}?k={query}&l={location}"
NAUKRI_SEARCH_WITHOUT_LOCATION_URL = "https://www.naukri.com/{query}-jobs-{page}?k={query}"


class NaukriScraper(BaseScraper):
    """
    Scrapes Naukri search results. Adjust selectors if the site updates its markup.
    Yields dicts with required fields for downstream cleaning/storage.
    """
    def scrape(self, query: str, limit: int, location: Optional[str] = None) -> Iterable[Dict[str, Any]]:
        q = query.strip()
        q_formatted = q.replace(" ", "-")
        count = 0
        page = 1
        max_pages = 20  # Naukri typically has max 20 pages
        
        try:
            while count < limit and page <= max_pages:
                # Construct URL for current page
                if location:
                    url = NAUKRI_SEARCH_WITH_LOCATION_URL.format(
                        query=q_formatted, 
                        page=page, 
                        location=location.strip().replace(' ', '-').lower()
                    )
                else:
                    url = NAUKRI_SEARCH_WITHOUT_LOCATION_URL.format(
                        query=q_formatted, 
                        page=page
                    )
                
                try:
                    self.get(url)
                except Exception as e:
                    logger.warning(f"Failed to navigate to Naukri page {page}: {e}")
                    break
                
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".srp-jobtuple-wrapper"))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for Naukri job results on page {page}")
                    break
                
                cards = self.driver.find_elements(By.CSS_SELECTOR, ".srp-jobtuple-wrapper")
                if not cards:
                    logger.info(f"No Naukri job results found on page {page}")
                    break

                # Use all job cards from current page
                job_cards = cards
                
                for i, card in enumerate(job_cards):
                    try:
                        # Extract title using h2 > a.title selector
                        title_elements = card.find_elements(By.CSS_SELECTOR, "h2 a.title")
                        title = ""
                        if title_elements:
                            title = title_elements[0].text.strip()

                        # Extract job URL from title link
                        job_url = ""
                        if title_elements:
                            job_url = title_elements[0].get_attribute("href")

                        # Extract company from the job URL structure
                        company = ""
                        if job_url:
                            # URL format: .../job-listings-{title}-{company}-{location}-{years}-{id}
                            url_parts = job_url.split('/')[-1].split('-')
                            if len(url_parts) > 3:
                                # Try to extract company name from URL - look for company name before location
                                # Find the company name by looking for patterns
                                company_candidates = []
                                for i, part in enumerate(url_parts):
                                    # Skip the first part (job-listings) and title parts
                                    if i < 2:
                                        continue
                                    # Stop when we hit location indicators
                                    if part.lower() in ['bengaluru', 'mumbai', 'delhi', 'pune', 'chennai', 'hyderabad', 'kolkata', 'noida', 'gurgaon', 'remote']:
                                        break
                                    # Stop when we hit year patterns
                                    if 'to' in part.lower() and any(char.isdigit() for char in part):
                                        break
                                    company_candidates.append(part)
                                
                                if company_candidates:
                                    company = ' '.join(company_candidates).replace('-', ' ').title()

                        # Extract location from the job URL structure
                        location_text = ""
                        if job_url:
                            # Look for location in URL or try to find location elements
                            location_elements = card.find_elements(By.CSS_SELECTOR, "span[class*='location'], .location, [class*='location']")
                            if location_elements:
                                location_text = location_elements[0].text.strip()
                            else:
                                # Try to extract from URL if not found in elements
                                url_parts = job_url.split('/')[-1].split('-')
                                if len(url_parts) > 2:
                                    # Find location in URL parts
                                    location_candidates = []
                                    for part in url_parts:
                                        # Look for known location names
                                        if part.lower() in ['bengaluru', 'mumbai', 'delhi', 'pune', 'chennai', 'hyderabad', 'kolkata', 'noida', 'gurgaon', 'remote', 'ajmer', 'jaipur']:
                                            location_candidates.append(part.title())
                                    if location_candidates:
                                        location_text = ', '.join(location_candidates)

                        # Try multiple selectors for salary
                        salary_selectors = [
                            "span[class*='salary']",
                            "div[class*='salary']",
                            "span[class*='compensation']",
                            "div[class*='compensation']"
                        ]
                        salary_text = ""
                        for selector in salary_selectors:
                            salary_el = card.find_elements(By.CSS_SELECTOR, selector)
                            if salary_el and salary_el[0].text.strip():
                                salary_text = salary_el[0].text.strip()
                                break

                        # Try multiple selectors for date
                        date_selectors = [
                            "span[class*='date']",
                            "div[class*='date']",
                            "span[class*='posted']",
                            "div[class*='posted']",
                            "time"
                        ]
                        date_text = "today"
                        for selector in date_selectors:
                            date_el = card.find_elements(By.CSS_SELECTOR, selector)
                            if date_el and date_el[0].text.strip():
                                date_text = date_el[0].text.strip()
                                break

                        # job_url is already extracted above from title_elements

                        salary_min, salary_max, currency = parse_salary(salary_text)
                        tag_els = card.find_elements(By.CSS_SELECTOR, "ul.tags li a")
                        page_tags = to_tags([e.text for e in tag_els])
                        posted_date = parse_posted_date(date_text, settings.timezone)
                        is_remote = derive_is_remote(title, location_text, page_tags)
                        
                        # Enhanced tags including search context and extracted data
                        enhanced_tags = page_tags.copy()
                        if query:
                            enhanced_tags.extend([f"search:{query}", f"query:{query}"])
                        if location:
                            enhanced_tags.extend([f"location:{location}", f"search_location:{location}"])
                        if location_text:
                            enhanced_tags.extend([f"job_location:{location_text}"])
                        if company:
                            enhanced_tags.extend([f"company:{company}"])
                        if is_remote:
                            enhanced_tags.append("remote")
                        enhanced_tags.extend(["source:naukri", "mode:dynamic"])

                        job_data = {
                            "source": "naukri",
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
                        yield job_data
                        count += 1
                        if count >= limit:
                            break
                    except Exception:
                        # Skip bad cards but keep going
                        continue

                # Move to next page if we haven't reached the limit
                if count < limit:
                    page += 1
                    pass  # Continue to next page
                else:
                    break  # Reached limit
        finally:
            self.close()