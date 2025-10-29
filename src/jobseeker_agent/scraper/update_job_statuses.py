import json
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.scraper.job_manager import load_raw_jobs, save_raw_jobs
from tqdm import tqdm

def update_job_statuses(status_callback=None):
    """
    Parses all job offers from raw_jobs.json, checks their status, and updates
    the status to "Closed" if the job is no longer available.
    
    Args:
        status_callback: Optional callback function(current, total) for progress updates
    """
    raw_jobs = load_raw_jobs()
    
    # Filter out jobs already marked as Closed to avoid unnecessary checks
    jobs_to_check = [job for job in raw_jobs if job.get('status') != 'Closed']
    total_jobs = len(jobs_to_check)
    
    updated_jobs = []
    jobs_updated_count = 0

    print(f"Starting job status update for {total_jobs} jobs (skipping {len(raw_jobs) - total_jobs} already closed)...")
    
    # Add Closed jobs directly to updated_jobs without checking
    closed_jobs = [job for job in raw_jobs if job.get('status') == 'Closed']
    updated_jobs.extend(closed_jobs)

    for i, job in enumerate(tqdm(jobs_to_check, desc="Analyzing jobs"), 1):
        if status_callback:
            status_callback(i, total_jobs)
            
        job_link = job.get('job_link')
        original_status = job.get('status')

        if not job_link:
            updated_jobs.append(job)
            continue

        analysis_result = extract_job_details(job_link)

        is_closed = not analysis_result or analysis_result.get('status') == 'Closed'

        if is_closed and original_status != 'Closed':
            job['status'] = 'Closed'
            jobs_updated_count += 1
            if not analysis_result:
                print(f"Updating job {job.get('id')} to 'Closed' because its page could not be accessed: {job.get('title')}")
            else:
                print(f"Updating job {job.get('id')} to 'Closed': {job.get('title')}")

        updated_jobs.append(job)

    save_raw_jobs(updated_jobs)

    print("\nUpdate process finished.")
    print(f"Total jobs updated to 'Closed': {jobs_updated_count}")
    print(f"Total jobs processed: {len(updated_jobs)}")
    
    return jobs_updated_count

if __name__ == "__main__":
    update_job_statuses()
