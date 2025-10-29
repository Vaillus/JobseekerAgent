
import requests
import html2text
import time
from bs4 import BeautifulSoup




def fetch_job_page(url, retries=5, backoff_factor=0.5):
    """Fetches the content of the job posting URL with retries on failure."""
    for i in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.exceptions.RequestException as e:
            # Check if the exception has a response and if the status code is 429
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                wait_time = backoff_factor * (2 ** i)
                print(f"Rate limited. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Error fetching URL {url}: {e}")
                return None
    print(f"Failed to fetch URL {url} after {retries} retries.")
    return None

def _get_description(soup: BeautifulSoup) -> str:
    """Extracts the job description from the soup object."""
    description_tag = soup.find('div', class_='description__text description__text--rich')
    if description_tag:
        html_description = str(description_tag)
        h = html2text.HTML2Text()
        h.ignore_links = True
        return h.handle(html_description)
    return 'Description not found.'

def _get_job_status(soup: BeautifulSoup) -> str:
    """Determines the job status (Open/Closed) from the soup object."""
    # 1. Primary check: Use a hidden flag in the HTML
    closed_flag_tag = soup.find('code', id='is-job-closed-flag')
    if closed_flag_tag and closed_flag_tag.string:
        if 'true' in closed_flag_tag.string:
            return "Closed"
        elif 'false' in closed_flag_tag.string:
            return "Open"

    # 2. Secondary check: if flag not present, look for explicit text
    closed_indicators = [
        "not currently accepting applications",
        "no longer accepting applications",
        "job is no longer active"
    ]
    page_text_lower = soup.get_text().lower()
    if any(indicator in page_text_lower for indicator in closed_indicators):
        return "Closed"

    # 3. Tertiary check: If still unknown, assume open but verify with apply button
    apply_button = soup.select_one('button.jobs-apply-button, .top-card-layout__cta')
    if not apply_button:
        return "Potentially Closed (No Apply Button Found)"
    
    return "Open"

def _get_workplace_type(soup: BeautifulSoup) -> str:
    """Extracts the workplace type (Remote/Hybrid/On-site) from the soup object."""
    description_body = soup.find('div', class_='description__text')
    if description_body:
        list_items = description_body.find_all('li')
        for item in list_items:
            item_text = item.get_text().lower()
            if "remote" in item_text or "à distance" in item_text:
                return "Remote"
            if "hybrid" in item_text:
                return "Hybrid"
            if "on-site" in item_text:
                return "On-site"
    return "Not found"

def extract_job_details(url: str) -> dict | None:
    """
    Analyzes a LinkedIn job posting and returns its details:
    - description
    - status (Open/Closed/Potentially Closed (No Apply Button Found))
    - workplace_type (Remote/Hybrid/On-site)
    
    Returns None if the page is not a valid LinkedIn job posting (e.g., redirected
    to an error page) - detected by absence of job description.
    """
    page_content = fetch_job_page(url)
    if not page_content:
        print("Failed to fetch page content.")
        return None

    soup = BeautifulSoup(page_content, 'html.parser')
    
    description = _get_description(soup)
    
    # If we can't find the description, the page is likely invalid (redirected, error page, etc.)
    if description == 'Description not found.':
        print("Page does not appear to be a valid LinkedIn job posting (no description found).")
        return None

    return {
        "description": description,
        "status": _get_job_status(soup),
        "workplace_type": _get_workplace_type(soup),
    }

if __name__ == "__main__":
    job_url = "https://www.linkedin.com/jobs/view/ai-research-scientist-phd-at-mercor-4308167189/?originalSubdomain=au" # position open
    # job_url = "https://www.linkedin.com/jobs/view/machine-learning-engineer-data-ai-training-at-canva-4313971909/?originalSubdomain=au" # position closed
    
    job_details = extract_job_details(job_url)
    if job_details:
        print("\n--- Job Details ---")
        print(f"Status: {job_details['status']}")
        print(f"Workplace: {job_details['workplace_type']}")
        print(f"Description: {job_details['description'][:500]}...")
        print("-------------------\n")
