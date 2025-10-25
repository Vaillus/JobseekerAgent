from datetime import date
from flask import Blueprint, jsonify, render_template, request
import markdown

from jobseeker_agent.utils.paths import (
    load_reviews,
    load_raw_jobs,
    load_job_statuses,
    save_job_statuses,
)
from jobseeker_agent.scraper.extract_job_details import extract_job_details

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

