import sys
import webbrowser
import threading
from pathlib import Path
from datetime import date
from flask import Flask, jsonify, render_template_string, request

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
app = Flask(__name__)


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

    return render_template_string(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Job Review Dashboard</title>
        <style>
            body { font-family: sans-serif; display: flex; height: 100vh; margin: 0; }
            #sidebar { width: 350px; background-color: #f8f8f8; border-right: 1px solid #ddd; overflow-y: auto; padding: 1em; }
            #content { flex: 1; padding: 2em; overflow-y: auto; }
            .job-item { padding: 1em; border-bottom: 1px solid #eee; cursor: pointer; border-radius: 5px; margin-bottom: 5px;}
            .job-item:hover { background-color: #eaf2f8; }
            .job-item.selected { background-color: #d4e6f1; }
            .job-item h4 { margin: 0 0 5px 0; color: #2c3e50; }
            .job-item p { margin: 0; font-size: 0.9em; color: #555; }
            h1 { color: #2c3e50; }
            h2 { color: #34495e; border-bottom: 1px solid #ccc; padding-bottom: 5px;}
            pre { white-space: pre-wrap; word-wrap: break-word; color: #34495e; font-family: monospace; background-color: #f8f8f8; padding: 1em; border: 1px solid #ddd; border-radius: 5px; }
            .info { background-color: #eaf2f8; border-left: 5px solid #3498db; padding: 1em; margin-bottom: 2em; border-radius: 5px; }
            #loader { text-align: center; padding: 2em; font-size: 1.2em; }
            .btn-container { margin-top: 1em; display: flex; gap: 10px; }
            .status-btn { color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-size: 1em; }
            .interested-btn { background-color: #27ae60; }
            .not-interested-btn { background-color: #c0392b; }
            .status-btn:disabled { background-color: #bdc3c7; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div id="sidebar">
            <h2>Jobs To Process</h2>
            <div id="job-list">
                {% for job in sidebar_jobs %}
                <div class="job-item" data-job-id="{{ job.id }}">
                    <h4>{{ job.title or 'N/A' }} (Score: {{ job.score if job.score is not none else 'N/A' }})</h4>
                    <p>{{ job.company or 'N/A' }} - {{ job.location or 'N/A' }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
        <div id="content">
            <div id="placeholder">
                <h1>Welcome to the Job Review Dashboard</h1>
                <p>Select a job from the list on the left to see its details.</p>
            </div>
            <div id="job-details" style="display: none;"></div>
        </div>

        <script>
            const jobsData = {{ all_jobs | tojson }};

            document.querySelectorAll('.job-item').forEach(item => {
                item.addEventListener('click', () => {
                    const jobId = item.dataset.jobId;
                    displayJobDetails(jobId);
                    document.querySelectorAll('.job-item').forEach(i => i.classList.remove('selected'));
                    item.classList.add('selected');
                });
            });

            function displayJobDetails(jobId) {
                document.getElementById('placeholder').style.display = 'none';
                const contentDiv = document.getElementById('job-details');
                contentDiv.style.display = 'block';
                
                const jobData = jobsData.find(j => j.id == jobId);
                if (!jobData) {
                    contentDiv.innerHTML = '<h2>Error: Job not found</h2>';
                    return;
                }

                // Initial render with stored data
                contentDiv.innerHTML = `
                    <h1>${ jobData.title || 'N/A' }</h1>
                    <h2>${ jobData.company || 'N/A' } - ${ jobData.location || 'N/A' }</h2>
                    <p><a href="${ jobData.job_link || '#' }" target="_blank">View Original Job Post</a></p>
                    <hr>
                    <div class="info">
                        <h3>Evaluation</h3>
                        <p><b>ID:</b> ${ jobData.id }</p>
                        <p><b>Score:</b> ${ jobData.score !== null ? jobData.score : 'N/A' }</p>
                        <p><b>Preferred Pitch:</b> ${ jobData.preferred_pitch || 'N/A' }</p>
                    </div>
                    <h2>Evaluation Grid</h2>
                    <pre>${ jobData.evaluation_grid || 'Not available.' }</pre>
                    <h2>Synthesis and Decision</h2>
                    <pre>${ jobData['synthesis and decision'] || 'Not available.' }</pre>
                    <h3>Full Job Description</h3>
                    <div id="live-description-container"><div id="loader">Fetching live details...</div></div>
                    <div class="btn-container">
                        <button id="interested-btn" class="status-btn interested-btn" data-job-id="${jobId}"></button>
                        <button id="not-interested-btn" class="status-btn not-interested-btn" data-job-id="${jobId}"></button>
                    </div>
                `;

                updateStatusButtons(jobId);

                // Fetch and render live description
                fetch(`/job/${jobId}`)
                    .then(response => response.json())
                    .then(data => {
                        const container = document.getElementById('live-description-container');
                        if (data.description) {
                            container.innerHTML = `<pre>${data.description}</pre>`;
                        } else {
                            container.innerHTML = `<pre>Could not retrieve live job description. Stored link: <a href="${jobData.job_link}" target="_blank">${jobData.job_link}</a></pre>`;
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching job details:', error);
                        const container = document.getElementById('live-description-container');
                        container.innerHTML = '<pre>Error fetching live details.</pre>';
                    });
            }
            
            function updateStatusButtons(jobId) {
                const interestedBtn = document.getElementById('interested-btn');
                const notInterestedBtn = document.getElementById('not-interested-btn');
                const jobData = jobsData.find(j => j.id == jobId);

                if (jobData.status) {
                    if (jobData.status.applied) {
                        interestedBtn.textContent = `Interested (${jobData.status.date})`;
                        interestedBtn.disabled = true;
                        notInterestedBtn.style.display = 'none';
                    } else {
                        notInterestedBtn.textContent = `Not Interested (${jobData.status.date})`;
                        notInterestedBtn.disabled = true;
                        interestedBtn.style.display = 'none';
                    }
                } else {
                    interestedBtn.textContent = 'Interested';
                    interestedBtn.disabled = false;
                    interestedBtn.style.display = 'inline-block';
                    notInterestedBtn.textContent = 'Not Interested';
                    notInterestedBtn.disabled = false;
                    notInterestedBtn.style.display = 'inline-block';

                    interestedBtn.onclick = () => updateJobStatus(jobId, true);
                    notInterestedBtn.onclick = () => updateJobStatus(jobId, false);
                }
            }

            function updateJobStatus(jobId, isInterested) {
                fetch(`/status/${jobId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ applied: isInterested })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Remove item from sidebar
                        const jobItem = document.querySelector(`.job-item[data-job-id='${jobId}']`);
                        if (jobItem) {
                            jobItem.remove();
                        }
                        // Hide details and show placeholder
                        document.getElementById('job-details').style.display = 'none';
                        document.getElementById('placeholder').style.display = 'block';
                    }
                });
            }
        </script>
    </body>
    </html>
    """,
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
