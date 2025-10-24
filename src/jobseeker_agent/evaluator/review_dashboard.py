import sys
import webbrowser
import threading
from pathlib import Path
from datetime import date
from flask import Flask, jsonify, render_template, request
from jinja2 import ChoiceLoader, FileSystemLoader
import json
import markdown
import os

print("--- Script starting ---")

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
print(f"Project root added to sys.path: {project_root}")

from jobseeker_agent.utils.paths import (
    load_main_evals,
    load_raw_jobs,
    load_job_statuses,
    save_job_statuses,
)
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.corrector.interface.routes import bp as corrector_bp
from jobseeker_agent.corrector.interface import state as corrector_state

print("--- Data Loading (once at startup) ---")
evals = load_main_evals()
raw_jobs = load_raw_jobs()
print(f"Loaded {len(evals)} evaluations and {len(raw_jobs)} raw jobs.")

evals_map = {int(e["id"]): e for e in evals}
raw_jobs_map = {int(j["id"]): j for j in raw_jobs}

base_jobs = []
job_ids = sorted(list(set(raw_jobs_map.keys()) & set(evals_map.keys())))
print(f"Found {len(job_ids)} common job IDs.")

for job_id in job_ids:
    job_data = {
        "id": job_id,
        **raw_jobs_map.get(job_id, {}),
        **evals_map.get(job_id, {}),
    }
    base_jobs.append(job_data)

# Sort by score descending
base_jobs.sort(key=lambda x: x.get("score", -float("inf")), reverse=True)
print("Jobs sorted by score.")


# --- Flask App ---
print("--- Initializing Flask App ---")
# We build absolute paths to the template and static folders
# to ensure the app can be run from anywhere.
app = Flask(
    __name__,
    static_folder=(Path(__file__).resolve().parent / "interface" / "static"),
)

# Define paths to the two template folders
evaluator_templates_path = (
    Path(__file__).resolve().parent / "interface" / "templates"
)
corrector_templates_path = (
    project_root / "src" / "jobseeker_agent" / "corrector" / "interface" / "templates"
)

# Set up a loader that looks for templates in both directories
app.jinja_loader = ChoiceLoader(
    [
        FileSystemLoader(str(evaluator_templates_path)),
        FileSystemLoader(str(corrector_templates_path)),
    ]
)

# For the blueprint, we only need to specify its static folder, as templates are now handled globally
corrector_interface_path = (
    project_root / "src" / "jobseeker_agent" / "corrector" / "interface"
)
app.register_blueprint(
    corrector_bp,
    url_prefix="/corrector"
)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
print("Flask App initialized.")


@app.route("/")
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
        "dashboard.html",
        sidebar_jobs=unprocessed_jobs,
        all_jobs=all_jobs,
    )


@app.route("/job/<int:job_id>")
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


@app.route("/status/<int:job_id>", methods=["POST"])
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


def main():
    """Main function to run the Flask app."""
    print("--- main() function called ---")
    # We use a thread to open the browser after the server starts.
    # This should only happen in the main process, not in the reloader's child process.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000/")).start()
    print("Starting the dashboard server at http://127.0.0.1:5000/")
    print("Press CTRL+C to stop the server.")
    app.run(port=5000, debug=True)


if __name__ == "__main__":
    print("--- Script executed directly ---")
    main()
