from jobseeker_agent.utils.paths import load_raw_job
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.reviewer.agents.reviewer import review
from jobseeker_agent.utils.paths import save_reviews, load_reviews


def review_single_job(job_id: int):
    """Review a single job."""
    job = load_raw_job(job_id)
    if not job:
        print(f"No job found for ID {job_id}")
        return
    job_details = extract_job_details(job["job_link"])
    result = review(job, job_details)
    reviews = load_reviews()
    reviews.append(result)
    save_reviews(reviews)
    return result

if __name__ == "__main__":
    job_id = 18
    review_single_job(job_id)
    # save the review to a file