"""
This script contains functions that relate to the testing of reviews.
in data/reviewer/tests/, there are several 'generations' of reviews.
each generation is associated with a different llm model, prompt, and eventually jobs that are being reviewed.
"""

from jobseeker_agent.utils.paths import load_raw_jobs, save_test_reviews, load_reviews, load_labels
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.reviewer.agents.reviewer import review

def print_review(job_id, generation_id: int):
    """Print the review for a given job ID with a given generation ID."""
    reviews = load_reviews(generation_id)
    for review in reviews:
        if review["id"] == job_id:
            from rich.console import Console
            from rich.markdown import Markdown
            
            console = Console()
            console.print(Markdown(review["evaluation_grid"]))
            return
    print(f"No review found for job ID {job_id}")

def review_from_id(job_id, generation_id: int):
    """Review a job from a given job ID with a given generation ID."""
    job = load_raw_jobs()
    job = next((j for j in job if j["id"] == job_id), None)
    if not job:
        print(f"No job found for ID {job_id}")
        return
    
    job_details = extract_job_details(job["job_link"])
    result = review(job, job_details)

    reviews = load_reviews(generation_id)
    reviews.append(result)
    save_test_reviews(reviews, generation_id)
    print(f"Saved review for job {job['id']}")
    return result


def main(generation_id: int, model=str):
    """
    Evaluate all jobs for a given generation ID.
    Jobs are labeled in data/reviewer/tests/generation_id/labels.json.
    Reviews are stored in data/reviewer/tests/generation_id/reviews.json.
    """
    labels = load_labels(generation_id)
    if not labels:
        print(f"No labels found for generation {generation_id}. Nothing to review.")
        return
    
    labeled_job_ids = {label["id"] for label in labels}
    
    raw_jobs = load_raw_jobs()
    jobs_to_review = [job for job in raw_jobs if job["id"] in labeled_job_ids]

    reviews = load_reviews(generation_id)
    reviewed_job_ids = {e["id"] for e in reviews}

    for job in jobs_to_review:
        if job["id"] in reviewed_job_ids:
            print(f"Job {job['id']} already reviewed. Skipping.")
            continue

        job_details = extract_job_details(job["job_link"])
        result = review(job, job_details, model=model)

        reviews.append(result)
        save_test_reviews(reviews, generation_id)
        print(f"Saved review for job {job['id']}")

if __name__ == "__main__":
    generation_id = 5
    main(generation_id, "gpt-5-mini")
