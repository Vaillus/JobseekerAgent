from datetime import date
from flask import Blueprint, jsonify, render_template, request
import markdown
import threading

from jobseeker_agent.utils.paths import (
    load_reviews,
    load_raw_jobs,
    load_job_statuses,
    save_job_statuses,
)
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.scraper.run_scraper import run_scraping
from jobseeker_agent.reviewer.review_batch import JobReviewer
from jobseeker_agent.interface import state

bp = Blueprint("reviewer", __name__)

# Data loaded at module level (will be loaded when blueprint is imported)
print("--- Loading reviewer data ---")
reviews = load_reviews()
raw_jobs = load_raw_jobs()
print(f"Loaded {len(reviews)} reviews and {len(raw_jobs)} raw jobs.")

reviews_map = {int(e["id"]): e for e in reviews}
raw_jobs_map = {int(j["id"]): j for j in raw_jobs}

base_jobs = []
job_ids = sorted(list(set(raw_jobs_map.keys()) & set(reviews_map.keys())))
print(f"Found {len(job_ids)} common job IDs.")

for job_id in job_ids:
    job_data = {
        "id": job_id,
        **raw_jobs_map.get(job_id, {}),
        **reviews_map.get(job_id, {}),
    }
    base_jobs.append(job_data)

# Sort by score descending
base_jobs.sort(key=lambda x: x.get("score", -float("inf")), reverse=True)
print("Jobs sorted by score.")


@bp.route("/")
def dashboard():
    """Renders the main dashboard HTML."""
    print("--- Request received for / route ---")
    job_statuses = load_job_statuses()
    job_statuses_map = {int(p["id"]): p for p in job_statuses}

    all_jobs = []
    for job in base_jobs:
        job_with_status = job.copy()
        job_with_status["status"] = job_statuses_map.get(job_with_status.get("id"))
        
        # Convert synthesis from Markdown to HTML
        if "synthesis_and_decision" in job_with_status and job_with_status["synthesis_and_decision"]:
            job_with_status["synthesis_and_decision"] = markdown.markdown(job_with_status["synthesis_and_decision"])

        all_jobs.append(job_with_status)

    unprocessed_jobs = [j for j in all_jobs if not j["status"]]
    print(f"Rendering dashboard with {len(unprocessed_jobs)} unprocessed jobs.")

    return render_template(
        "reviewer/dashboard.html",
        sidebar_jobs=unprocessed_jobs,
        all_jobs=all_jobs,
    )


@bp.route("/job/<int:job_id>")
def get_job_details(job_id: int):
    """Fetches live job details and returns as JSON."""
    print(f"--- Request received for /job/{job_id} ---")
    job_link = raw_jobs_map.get(job_id, {}).get("job_link")
    if not job_link:
        print(f"Job ID {job_id} not found in raw_jobs_map.")
        return jsonify({"error": "Job not found"}), 404
    
    print(f"Fetching live details for job link: {job_link}")
    live_details = extract_job_details(job_link)
    if not live_details:
        print("Could not fetch live details.")
        return jsonify({"description": None})

    # Convert description from Markdown to HTML
    if "description" in live_details and live_details["description"]:
        processed_markdown = live_details["description"].replace('**', '## ')
        live_details["description"] = markdown.markdown(processed_markdown)

    print("Successfully fetched live details.")
    return jsonify(live_details)


@bp.route("/status/<int:job_id>", methods=["POST"])
def update_status(job_id: int):
    """Marks a job's status as applied or not interested."""
    print(f"--- Request received for /status/{job_id} ---")
    data = request.get_json()
    has_applied = data.get("applied")
    print(f"Updating status for job {job_id} to applied={has_applied}")

    if has_applied is None:
        return jsonify({"success": False, "message": "Missing 'applied' field"}), 400

    today = date.today().isoformat()
    status = {"id": job_id, "date": today, "applied": has_applied}

    current_statuses = load_job_statuses()
    
    # Remove existing status for this job_id if it exists, then add the new one
    current_statuses = [s for s in current_statuses if s['id'] != job_id]
    current_statuses.append(status)
    
    save_job_statuses(current_statuses)
    print(f"Status for job {job_id} saved successfully.")

    return jsonify({"success": True, "status": status})


@bp.route("/scrape", methods=["POST"])
def start_scraping():
    """Launch scraping in a background thread."""
    print("--- Request received for /scrape ---")
    data = request.get_json()
    time_horizon = data.get("time_horizon", "day")
    
    if state.SCRAPING_THREAD and state.SCRAPING_THREAD.is_alive():
        return jsonify({"success": False, "message": "Scraping already in progress"}), 400
    
    # Reset status
    state.SCRAPING_STATUS = {"status": "running", "new_jobs_count": 0, "error": None}
    
    def scrape_task():
        try:
            print(f"Starting scraping with time_horizon={time_horizon}")
            new_jobs_count = run_scraping(max_time=time_horizon)
            state.SCRAPING_STATUS = {
                "status": "completed",
                "new_jobs_count": new_jobs_count,
                "error": None
            }
            print(f"Scraping completed. Added {new_jobs_count} new jobs.")
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            state.SCRAPING_STATUS = {
                "status": "error",
                "new_jobs_count": 0,
                "error": str(e)
            }
    
    state.SCRAPING_THREAD = threading.Thread(target=scrape_task)
    state.SCRAPING_THREAD.start()
    
    return jsonify({"success": True, "message": "Scraping started"})


@bp.route("/scrape/status", methods=["GET"])
def get_scraping_status():
    """Get current scraping status."""
    return jsonify(state.SCRAPING_STATUS)


@bp.route("/review", methods=["POST"])
def start_review():
    """Launch review in a background thread."""
    print("--- Request received for /review ---")
    data = request.get_json()
    count = data.get("count", 10)
    
    if state.REVIEW_THREAD and state.REVIEW_THREAD.is_alive():
        return jsonify({"success": False, "message": "Review already in progress"}), 400
    
    # Reset status
    state.REVIEW_STATUS = {"status": "running", "current": 0, "total": count, "error": None}
    
    def review_task():
        try:
            print(f"Starting review of {count} jobs")
            reviewer = JobReviewer()
            
            for i in range(count):
                job_review = reviewer.review_random_job("gpt-4.1", with_correction=True)
                if job_review is None:
                    # No more jobs to review
                    state.REVIEW_STATUS["total"] = i
                    break
                state.REVIEW_STATUS["current"] = i + 1
                print(f"Reviewed {i + 1}/{count} jobs")
            
            state.REVIEW_STATUS["status"] = "completed"
            print(f"Review completed. Reviewed {state.REVIEW_STATUS['current']} jobs.")
        except Exception as e:
            print(f"Error during review: {str(e)}")
            import traceback
            traceback.print_exc()
            state.REVIEW_STATUS = {
                "status": "error",
                "current": state.REVIEW_STATUS.get("current", 0),
                "total": count,
                "error": str(e)
            }
    
    state.REVIEW_THREAD = threading.Thread(target=review_task)
    state.REVIEW_THREAD.start()
    
    return jsonify({"success": True, "message": "Review started"})


@bp.route("/review/status", methods=["GET"])
def get_review_status():
    """Get current review status."""
    return jsonify(state.REVIEW_STATUS)


@bp.route("/refresh-jobs", methods=["GET"])
def refresh_jobs():
    """Reload job data and return updated lists."""
    print("--- Request received for /refresh-jobs ---")
    
    try:
        # Reload data
        reviews = load_reviews()
        raw_jobs = load_raw_jobs()
        job_statuses = load_job_statuses()
        
        print(f"Reloaded {len(reviews)} reviews and {len(raw_jobs)} raw jobs.")
        
        reviews_map = {int(e["id"]): e for e in reviews}
        raw_jobs_map = {int(j["id"]): j for j in raw_jobs}
        job_statuses_map = {int(p["id"]): p for p in job_statuses}
        
        base_jobs = []
        job_ids = sorted(list(set(raw_jobs_map.keys()) & set(reviews_map.keys())))
        
        for job_id in job_ids:
            job_data = {
                "id": job_id,
                **raw_jobs_map.get(job_id, {}),
                **reviews_map.get(job_id, {}),
            }
            base_jobs.append(job_data)
        
        # Sort by score descending
        base_jobs.sort(key=lambda x: x.get("score", -float("inf")), reverse=True)
        
        all_jobs = []
        for job in base_jobs:
            job_with_status = job.copy()
            job_with_status["status"] = job_statuses_map.get(job_with_status.get("id"))
            
            # Convert synthesis from Markdown to HTML
            if "synthesis_and_decision" in job_with_status and job_with_status["synthesis_and_decision"]:
                job_with_status["synthesis_and_decision"] = markdown.markdown(job_with_status["synthesis_and_decision"])
            
            all_jobs.append(job_with_status)
        
        unprocessed_jobs = [j for j in all_jobs if not j["status"]]
        
        print(f"Returning {len(unprocessed_jobs)} unprocessed jobs.")
        
        return jsonify({
            "success": True,
            "jobs": all_jobs,
            "sidebar_jobs": unprocessed_jobs
        })
    except Exception as e:
        print(f"Error refreshing jobs: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

