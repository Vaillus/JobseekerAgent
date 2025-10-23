import sys
import webbrowser
import threading
from pathlib import Path
from datetime import date
from flask import Flask, jsonify, render_template, request

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from jobseeker_agent.utils.paths import (
    load_main_evals,
    load_raw_jobs,
    load_job_statuses,
    save_job_statuses,
)
from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job

# --- Data Loading (once at startup) ---
evals = load_main_evals()
raw_jobs = load_raw_jobs()

evals_map = {int(e["id"]): e for e in evals}
raw_jobs_map = {int(j["id"]): j for j in raw_jobs}

base_jobs = []
job_ids = sorted(list(set(raw_jobs_map.keys()) & set(evals_map.keys())))

for job_id in job_ids:
    job_data = {
        "id": job_id,
        **raw_jobs_map.get(job_id, {}),
        **evals_map.get(job_id, {}),
    }
    base_jobs.append(job_data)

# Sort by score descending
base_jobs.sort(key=lambda x: x.get("score", -float("inf")), reverse=True)


# --- Flask App ---
app = Flask(
    __name__,
    template_folder="interface/templates",
    static_folder="interface/static",
)


@app.route("/")
def dashboard():
    """Renders the main dashboard HTML."""
    job_statuses = load_job_statuses()
    job_statuses_map = {int(p["id"]): p for p in job_statuses}

    all_jobs = []
    for job in base_jobs:
        job_with_status = job.copy()
        job_with_status["status"] = job_statuses_map.get(job_with_status.get("id"))
        all_jobs.append(job_with_status)

    unprocessed_jobs = [j for j in all_jobs if not j["status"]]

    return render_template(
        "dashboard.html",
        sidebar_jobs=unprocessed_jobs,
        all_jobs=all_jobs,
    )


@app.route("/job/<int:job_id>")
def get_job_details(job_id: int):
    """Fetches live job details and returns as JSON."""
    job_link = raw_jobs_map.get(job_id, {}).get("job_link")
    if not job_link:
        return jsonify({"error": "Job not found"}), 404
    
    live_details = analyze_linkedin_job(job_link)
    if not live_details:
        return jsonify({"description": None})

    return jsonify(live_details)


@app.route("/status/<int:job_id>", methods=["POST"])
def update_status(job_id: int):
    """Marks a job's status as applied or not interested."""
    data = request.get_json()
    has_applied = data.get("applied")

    if has_applied is None:
        return jsonify({"success": False, "message": "Missing 'applied' field"}), 400

    today = date.today().isoformat()
    status = {"id": job_id, "date": today, "applied": has_applied}

    current_statuses = load_job_statuses()
    
    # Remove existing status for this job_id if it exists, then add the new one
    current_statuses = [s for s in current_statuses if s['id'] != job_id]
    current_statuses.append(status)
    
    save_job_statuses(current_statuses)

    return jsonify({"success": True, "status": status})


def main():
    """Main function to run the Flask app."""
    # We use a thread to open the browser after the server starts.
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000/")).start()
    print("Starting the dashboard server at http://127.0.0.1:5000/")
    print("Press CTRL+C to stop the server.")
    app.run(port=5000, debug=False)


if __name__ == "__main__":
    main()
