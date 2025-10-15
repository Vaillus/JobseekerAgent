import random
from jobseeker_agent.utils.paths import (
    load_raw_jobs,
    load_main_evals,
    save_main_evals,
    load_processed_jobs,
    save_processed_jobs,
)
from jobseeker_agent.evaluator.evaluator import evaluate_job
from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job


class JobEvaluator:
    def __init__(self):
        self.raw_jobs = load_raw_jobs()
        self.processed_job_ids = set(load_processed_jobs())
        self.evaluations = load_main_evals()

    def _get_unprocessed_jobs(self):
        return [
            job for job in self.raw_jobs if job["id"] not in self.processed_job_ids
        ]

    def evaluate_random_job(self):
        unprocessed_jobs = self._get_unprocessed_jobs()
        if not unprocessed_jobs:
            print("All jobs have been evaluated.")
            return

        job_to_evaluate = random.choice(unprocessed_jobs)
        job_id = job_to_evaluate["id"]

        print(f"Evaluating job {job_id}...")
        job_details = analyze_linkedin_job(job_to_evaluate["job_link"])
        if not job_details:
            print(f"Failed to retrieve details for job {job_id}. Skipping.")
            return

        evaluation = evaluate_job(job_to_evaluate, job_details)

        self.evaluations.append(evaluation)
        self.processed_job_ids.add(job_id)

        save_main_evals(self.evaluations)
        save_processed_jobs(list(self.processed_job_ids))

        print(f"Evaluation for job {job_id} saved.")
        return evaluation

    def evaluate_n_jobs(self, n: int):
        for i in range(n):
            print(f"--- Evaluating job {i+1}/{n} ---")
            evaluation = self.evaluate_random_job()
            if evaluation is None:
                break


if __name__ == "__main__":
    evaluator = JobEvaluator()
    evaluator.evaluate_n_jobs(50)
