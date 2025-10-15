
import requests
import html2text
from bs4 import BeautifulSoup




def fetch_job_page(url):
    """Fetches the content of the job posting URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def analyze_linkedin_job(url):
    """Analyzes a LinkedIn job posting and returns its details:
    - description
    - status (Open/Closed/Potentially Closed (No Apply Button Found))
    - workplace_type (Remote/Hybrid/On-site)
    """
    page_content = fetch_job_page(url)
    if not page_content:
        print("Failed to fetch page content.")
        return None

    soup = BeautifulSoup(page_content, 'html.parser')

    # --- Job Description ---
    description_tag = soup.find('div', class_='description__text description__text--rich')
    if description_tag:
        html_description = str(description_tag)
        h = html2text.HTML2Text()
        h.ignore_links = True
        job_description = h.handle(html_description)
    else:
        job_description = 'Description not found.'

    # --- Job Status ---
    job_status = "Unknown"

    # 1. Primary check: Use a hidden flag in the HTML
    closed_flag_tag = soup.find('code', id='is-job-closed-flag')
    if closed_flag_tag and closed_flag_tag.string:
        if 'true' in closed_flag_tag.string:
            job_status = "Closed"
        elif 'false' in closed_flag_tag.string:
            job_status = "Open"
    
    # 2. Secondary check: if flag not present, look for explicit text
    if job_status == "Unknown":
        closed_indicators = [
            "not currently accepting applications",
            "no longer accepting applications",
            "job is no longer active"
        ]
        page_text_lower = soup.get_text().lower()
        for indicator in closed_indicators:
            if indicator in page_text_lower:
                job_status = "Closed"
                break
    
    # 3. Tertiary check: If still unknown, assume open but verify with apply button
    if job_status == "Unknown":
        job_status = "Open"  # Assume open if no closed signals
        # Look for a prominent apply button
        apply_button = soup.select_one('button.jobs-apply-button, .top-card-layout__cta')
        if not apply_button:
            job_status = "Potentially Closed (No Apply Button Found)"

    # --- Workplace Type (Remote/Hybrid/On-site) ---
    workplace_type = "Not found"
    
    description_body = soup.find('div', class_='description__text')
    if description_body:
        search_terms = ['remote', 'hybrid', 'on-site', 'à distance']
        list_items = description_body.find_all('li')
        for item in list_items:
            item_text = item.get_text().lower()
            for term in search_terms:
                if term in item_text:
                    if "remote" in item_text or "à distance" in item_text:
                        workplace_type = "Remote"
                    elif "hybrid" in item_text:
                        workplace_type = "Hybrid"
                    elif "on-site" in item_text:
                        workplace_type = "On-site"
                    break
                if workplace_type != "Not found":
                    break


    return {
        "description": job_description,
        "status": job_status,
        "workplace_type": workplace_type
    }

if __name__ == "__main__":
    job_url = "https://www.linkedin.com/jobs/view/ai-research-scientist-phd-at-mercor-4308167189/?originalSubdomain=au" # position open
    # job_url = "https://www.linkedin.com/jobs/view/machine-learning-engineer-data-ai-training-at-canva-4313971909/?originalSubdomain=au" # position closed
    
    job_details = analyze_linkedin_job(job_url)
    if job_details:
        print("\n--- Job Details ---")
        print(f"Status: {job_details['status']}")
        print(f"Workplace: {job_details['workplace_type']}")
        print(f"Description: {job_details['description'][:500]}...")
        print("-------------------\n")
