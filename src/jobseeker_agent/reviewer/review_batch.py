import random
from jobseeker_agent.utils.paths import (
    load_raw_jobs,
    load_reviews,
    save_reviews,
    load_processed_jobs,
    save_processed_jobs,
)
from jobseeker_agent.reviewer.agents.reviewer import review as review_agent
from jobseeker_agent.scraper.extract_job_details import extract_job_details


class JobReviewer:
    def __init__(self):
        self.raw_jobs = load_raw_jobs()
        self.processed_job_ids = set(load_processed_jobs())
        self.reviews = load_reviews()

    def _get_unprocessed_jobs(self):
        return [
            job
            for job in self.raw_jobs
            if job["id"] not in self.processed_job_ids and job.get("status") != "Closed"
        ]

    def review_random_job(self, model, with_correction=True, reasoning_level=None):
        unprocessed_jobs = self._get_unprocessed_jobs()
        if not unprocessed_jobs:
            print("All jobs have been reviewed.")
            return

        job_to_review = random.choice(unprocessed_jobs)
        job_id = job_to_review["id"]

        print(f"Reviewing job {job_id}...")
        job_details = extract_job_details(job_to_review["job_link"])
        if not job_details:
            print(f"Failed to retrieve details for job {job_id}. Skipping.")
            return

        review = review_agent(job_to_review, job_details, model, with_correction, reasoning_level)

        self.reviews.append(review)
        self.processed_job_ids.add(job_id)

        save_reviews(self.reviews)
        save_processed_jobs(list(self.processed_job_ids))

        print(f"Review for job {job_id} saved.")
        return review

    def review_next_latest(self, model, with_correction=True, reasoning_level=None):
        unprocessed_jobs = self._get_unprocessed_jobs()
        if not unprocessed_jobs:
            print("All jobs have been reviewed.")
            return

        # Pick most recent by highest id
        job_to_review = sorted(unprocessed_jobs, key=lambda j: j.get("id", 0), reverse=True)[0]
        job_id = job_to_review["id"]

        print(f"Reviewing job {job_id} (latest-first)...")
        job_details = extract_job_details(job_to_review["job_link"])
        if not job_details:
            print(f"Failed to retrieve details for job {job_id}. Skipping.")
            return

        review = review_agent(job_to_review, job_details, model, with_correction, reasoning_level)

        self.reviews.append(review)
        self.processed_job_ids.add(job_id)

        save_reviews(self.reviews)
        save_processed_jobs(list(self.processed_job_ids))

        print(f"Review for job {job_id} saved.")
        return review

    def review_n_jobs(self, n: int, model: str, with_correction=True, reasoning_level=None):
        for i in range(n):
            print(f"--- Reviewing job {i+1}/{n} ---")
            review = self.review_random_job(model, with_correction, reasoning_level)
            if review is None:
                break


if __name__ == "__main__":
    reviewer = JobReviewer()
    reviewer.review_n_jobs(300, "gpt-4.1")
