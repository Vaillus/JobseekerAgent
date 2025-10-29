from datetime import date
from flask import Blueprint, jsonify, render_template, request
import markdown
import threading

from jobseeker_agent.utils.paths import (
    load_reviews,
    load_raw_jobs,
    load_job_statuses,
    save_job_statuses,
    load_scraping_destinations,
    save_scraping_destinations,
)
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.scraper.run_scraper import run_scraping
from jobseeker_agent.scraper.update_job_statuses import update_job_statuses
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
    # Skip jobs whose raw status is Closed
    if raw_jobs_map.get(job_id, {}).get("status") == "Closed":
        continue
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

    # Calculate review count info
    # Total: all open jobs (not Closed) in raw_jobs
    total_open_count = len([j for j in raw_jobs if j.get("status") != "Closed"])
    # Unreviewed: open jobs that are NOT in reviews.json
    unreviewed_count = len([
        j for j in raw_jobs 
        if j.get("status") != "Closed" and j["id"] not in reviews_map
    ])
    percentage = (unreviewed_count / total_open_count * 100) if total_open_count > 0 else 0
    review_count_info = {
        "unreviewed_count": unreviewed_count,
        "total_open_count": total_open_count,
        "percentage": round(percentage, 1)
    }

    return render_template(
        "reviewer/dashboard.html",
        sidebar_jobs=unprocessed_jobs,
        all_jobs=all_jobs,
        review_count_info=review_count_info,
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
    # Support either days (int) or legacy time_horizon (str)
    if "days" in data:
        try:
            time_horizon = int(data["days"])
        except Exception:
            return jsonify({"success": False, "message": "Invalid 'days' value"}), 400
    else:
        time_horizon = data.get("time_horizon", "day")

    # Optional destinations list; if not provided, load from server-side config
    destinations = data.get("destinations")
    if destinations is None:
        destinations = load_scraping_destinations()
    
    if state.SCRAPING_THREAD and state.SCRAPING_THREAD.is_alive():
        return jsonify({"success": False, "message": "Scraping already in progress"}), 400
    
    # Reset status
    state.SCRAPING_STATUS = {"status": "running", "new_jobs_count": 0, "error": None}
    
    def scrape_task():
        try:
            print(f"Starting scraping with time_horizon={time_horizon}")
            new_jobs_count = run_scraping(max_time=time_horizon, destinations_config=destinations)
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


@bp.route("/scrape/config", methods=["GET"])
def get_scraping_config():
    """Return scraping destinations configuration. If empty, generate defaults in-memory."""
    destinations = load_scraping_destinations()
    if not destinations:
        destinations = [
            {"id": 1, "location": "Sidney, Australia", "remote_type": "any", "enabled": True},
            {"id": 2, "location": "Australia", "remote_type": "remote", "enabled": True},
            {"id": 3, "location": "Paris, France", "remote_type": "any", "enabled": True},
            {"id": 4, "location": "France", "remote_type": "remote", "enabled": True},
            {"id": 5, "location": "Germany", "remote_type": "remote", "enabled": True},
            {"id": 6, "location": "Amsterdam, Netherlands", "remote_type": "any", "enabled": True},
            {"id": 7, "location": "Netherlands", "remote_type": "remote", "enabled": True},
        ]
    return jsonify({"destinations": destinations})


@bp.route("/scrape/config", methods=["POST"])
def save_scraping_config():
    """Persist scraping destinations configuration to JSON."""
    data = request.get_json()
    destinations = data.get("destinations")
    if not isinstance(destinations, list):
        return jsonify({"success": False, "message": "Field 'destinations' must be a list"}), 400
    try:
        save_scraping_destinations(destinations)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/scrape/status", methods=["GET"])
def get_scraping_status():
    """Get current scraping status."""
    return jsonify(state.SCRAPING_STATUS)


@bp.route("/update-status", methods=["POST"])
def start_update_status():
    """Launch job status update in a background thread."""
    print("--- Request received for /update-status ---")
    
    if state.UPDATE_STATUS_THREAD and state.UPDATE_STATUS_THREAD.is_alive():
        return jsonify({"success": False, "message": "Status update already in progress"}), 400
    
    # Reset status
    state.UPDATE_STATUS_STATUS = {"status": "running", "current": 0, "total": 0, "jobs_updated_count": 0, "error": None}
    
    def update_status_task():
        try:
            print("Starting job status update...")
            
            def progress_callback(current, total):
                state.UPDATE_STATUS_STATUS = {
                    "status": "running",
                    "current": current,
                    "total": total,
                    "jobs_updated_count": 0,
                    "error": None
                }
            
            jobs_updated_count = update_job_statuses(status_callback=progress_callback)
            final_total = state.UPDATE_STATUS_STATUS.get("total", 0)
            state.UPDATE_STATUS_STATUS = {
                "status": "completed",
                "current": final_total,
                "total": final_total,
                "jobs_updated_count": jobs_updated_count,
                "error": None
            }
            print(f"Status update completed. {jobs_updated_count} jobs updated to 'Closed'.")
        except Exception as e:
            print(f"Error during status update: {str(e)}")
            import traceback
            traceback.print_exc()
            state.UPDATE_STATUS_STATUS = {
                "status": "error",
                "current": state.UPDATE_STATUS_STATUS.get("current", 0),
                "total": state.UPDATE_STATUS_STATUS.get("total", 0),
                "jobs_updated_count": 0,
                "error": str(e)
            }
    
    state.UPDATE_STATUS_THREAD = threading.Thread(target=update_status_task)
    state.UPDATE_STATUS_THREAD.start()
    
    return jsonify({"success": True, "message": "Status update started"})


@bp.route("/update-status/status", methods=["GET"])
def get_update_status_status():
    """Get current update status status."""
    return jsonify(state.UPDATE_STATUS_STATUS)


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
            # Skip jobs whose raw status is Closed
            if raw_jobs_map.get(job_id, {}).get("status") == "Closed":
                continue
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
        
        # Calculate review count info
        # Total: all open jobs (not Closed) in raw_jobs
        total_open_count = len([j for j in raw_jobs if j.get("status") != "Closed"])
        # Unreviewed: open jobs that are NOT in reviews.json
        unreviewed_count = len([
            j for j in raw_jobs 
            if j.get("status") != "Closed" and j["id"] not in reviews_map
        ])
        percentage = (unreviewed_count / total_open_count * 100) if total_open_count > 0 else 0
        review_count_info = {
            "unreviewed_count": unreviewed_count,
            "total_open_count": total_open_count,
            "percentage": round(percentage, 1)
        }
        
        print(f"Returning {len(unprocessed_jobs)} unprocessed jobs.")
        
        return jsonify({
            "success": True,
            "jobs": all_jobs,
            "sidebar_jobs": unprocessed_jobs,
            "review_count_info": review_count_info
        })
    except Exception as e:
        print(f"Error refreshing jobs: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

