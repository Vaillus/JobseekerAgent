from dataclasses import dataclass
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from jobseeker_agent.scraper.linkedin_query import QueryBuilder
from jobseeker_agent.scraper.raw_jobs_manager import add_new_job


@dataclass
class JobData:
    title: str
    company: str
    location: str
    job_link: str
    posted_date: str


class ScraperConfig:
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOBS_PER_PAGE = 25
    MIN_DELAY = 2
    MAX_DELAY = 5
    RATE_LIMIT_DELAY = 30
    RATE_LIMIT_THRESHOLD = 10

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
        "Cache-Control": "no-cache",
    }


class LinkedInJobsScraper:
    def __init__(self):
        self.session = self._setup_session()

    def _setup_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def scrape_jobs(
        self,
        keywords: str,
        location: str,
        max_jobs: int = 100,
        remote_type: str = "any",
        max_time: str = "day",
    ) -> int:
        """Scrape jobs from LinkedIn based on the given parameters."""
        new_jobs_count = 0
        total_jobs_processed = 0
        start = 0

        while total_jobs_processed < max_jobs:
            try:
                url = self._build_search_url(
                    keywords, location, start, remote_type, max_time
                )
                print(url)
                soup = self._fetch_job_page(url)
                job_cards = soup.find_all("div", class_="base-card")

                if not job_cards:
                    break
                for card in job_cards:
                    if total_jobs_processed >= max_jobs:
                        break
                    job_data = self._extract_job_data(card)
                    if job_data:
                        job_dict = {
                            "title": job_data.title,
                            "company": job_data.company,
                            "location": job_data.location,
                            "job_link": job_data.job_link,
                            "posted_date": job_data.posted_date,
                        }
                        added_job = add_new_job(job_dict)
                        if added_job:
                            new_jobs_count += 1
                            print(f"Added new job: {job_data.title}")
                        else:
                            print(f"Job already exists: {job_data.title}")
                    total_jobs_processed += 1

                print(
                    f"Processed {total_jobs_processed} jobs, added {new_jobs_count} new jobs..."
                )
                start += ScraperConfig.JOBS_PER_PAGE
                time.sleep(
                    random.uniform(ScraperConfig.MIN_DELAY, ScraperConfig.MAX_DELAY)
                )
            except Exception as e:
                print(f"Scraping error: {str(e)}")
                break
        return new_jobs_count

    def _build_search_url(
        self,
        keywords: str,
        location: str,
        start: int = 0,
        remote_type: str = "any",
        max_time: str = "day"
    ) -> str:
        """Build the search URL based on the given parameters."""
        params = {
            "keywords": keywords,
            "location": location,
            "start": start,
        }
        if remote_type == "remote":
            params["f_WT"] = 2
        elif remote_type == "hybrid":
            params["f_WT"] = 3
        elif remote_type == "on_site":
            params["f_WT"] = 1
        elif remote_type == "any":
            pass
        else:
            raise ValueError(f"Invalid remote type: {remote_type}. Please choose from remote, hybrid, on_site, any.")
        if max_time == "day":
            params["f_TPR"] = 'r86400'
        elif max_time == "week":
            params["f_TPR"] = 'r604800'
        elif max_time == "month":
            params["f_TPR"] = 'r2592000'
        else:
            raise ValueError(f"Invalid max time: {max_time}. Please choose from day, week, month.")
        return f"{ScraperConfig.BASE_URL}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}"

    def _clean_job_url(self, url: str) -> str:
        return url.split("?")[0] if "?" in url else url

    def _extract_job_data(self, job_card: BeautifulSoup) -> Optional[JobData]:
        try:
            title = job_card.find("h3", class_="base-search-card__title").text.strip()
            company = job_card.find(
                "h4", class_="base-search-card__subtitle"
            ).text.strip()
            location = job_card.find(
                "span", class_="job-search-card__location"
            ).text.strip()
            job_link = self._clean_job_url(
                job_card.find("a", class_="base-card__full-link")["href"]
            )
            # print(job_card.prettify())
            posted_date = job_card.find("time", class_="job-search-card__listdate") or job_card.find("time", class_="job-search-card__listdate--new")
            # print(posted_date)
            posted_date = posted_date.text.strip() if posted_date else "N/A"
            # print(posted_date)
            return JobData(
                title=title,
                company=company,
                location=location,
                job_link=job_link,
                posted_date=posted_date,
            )
        except Exception as e:
            print(f"Failed to extract job data: {str(e)}")
            return None

    def _fetch_job_page(self, url: str) -> BeautifulSoup:
        """Fetch the job listing page and return the BeautifulSoup object."""
        try:
            response = self.session.get(url, headers=ScraperConfig.HEADERS)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Failed to fetch data: Status code {response.status_code}"
                )
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            raise RuntimeError(f"Request failed: {str(e)}")


def main():

    builder = QueryBuilder()
    query = builder.build_secondary_query()
    
    print(query)
    remote_type = "any" # remote, hybrid, on_site, any
    max_time = "month" # day, week, month
    params = {
        "keywords": query,
        "location": "Paris, France",
        "max_jobs": 100,
        "remote_type": remote_type,
        "max_time": max_time
    }

    scraper = LinkedInJobsScraper()
    new_jobs_added = scraper.scrape_jobs(**params)
    print(f"Finished scraping. Added {new_jobs_added} new jobs.")


if __name__ == "__main__":
    main()


# Doc:
# les paramètres )à