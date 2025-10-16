import sys
import os
import argparse
import webbrowser
import tempfile
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from jobseeker_agent.utils.paths import load_main_evals, load_raw_jobs
from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job


def display_job_details(job_data: dict):
    """Creates a temporary HTML file with job details and opens it in the browser."""
    print(f"Fetching details for job ID {job_data['id']}...")
    job_description = analyze_linkedin_job(job_data["job_link"])
    if not job_description:
        print(
            f"Could not retrieve details for job ID {job_data['id']}. Displaying stored data."
        )
        description_html = f"<pre>Could not retrieve live job description. Stored link: {job_data['job_link']}</pre>"
    else:
        description_html = (
            f"<pre>{job_description.get('description', 'Not available.')}</pre>"
        )

    html_content = f"""
    <html>
    <head>
        <title>Job Review: {job_data.get('title', 'N/A')}</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; padding: 2em; max-width: 1200px; margin: auto; display: flex; gap: 2em; }}
            .column {{ flex: 1; overflow-y: auto; max-height: 95vh;}}
            .description {{ border-right: 1px solid #ccc; padding-right: 2em;}}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #ccc; padding-bottom: 5px;}}
            pre {{ white-space: pre-wrap; word-wrap: break-word; color: #34495e; font-family: monospace; background-color: #f8f8f8; padding: 1em; border: 1px solid #ddd; border-radius: 5px;}}
            .info {{ background-color: #eaf2f8; border-left: 5px solid #3498db; padding: 1em; margin-bottom: 2em; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="column description">
            <h1>{job_data.get('title', 'N/A')}</h1>
            <h2>{job_data.get('company', 'N/A')} - {job_data.get('location', 'N/A')}</h2>
            <p><a href="{job_data.get('job_link', '#')}" target="_blank">View Original Job Post</a></p>
            <hr>
            <h3>Full Job Description</h3>
            {description_html}
        </div>
        <div class="column evaluation">
            <div class="info">
                <h3>Evaluation</h3>
                <p><b>ID:</b> {job_data['id']}</p>
                <p><b>Score:</b> {job_data.get('score', 'N/A')}</p>
                <p><b>Preferred Pitch:</b> {job_data.get('preferred_pitch', 'N/A')}</p>
            </div>
            <h2>Evaluation Grid</h2>
            <pre>{job_data.get('evaluation_grid', 'Not available.')}</pre>
            <h2>Synthesis and Decision</h2>
            <pre>{job_data.get('synthesis and decision', 'Not available.')}</pre>
        </div>
    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile(
        "w", delete=False, suffix=".html", encoding="utf-8"
    ) as f:
        f.write(html_content)
        webbrowser.open("file://" + os.path.realpath(f.name))


def main(job_id: int):
    """Main function to review a job evaluation."""
    print(f"Loading data for job ID: {job_id}")
    evals = load_main_evals()
    raw_jobs = load_raw_jobs()

    evals_map = {int(e["id"]): e for e in evals}
    raw_jobs_map = {int(j["id"]): j for j in raw_jobs}

    if job_id not in evals_map:
        print(f"Error: Evaluation for Job ID {job_id} not found.")
        return
    if job_id not in raw_jobs_map:
        print(f"Error: Raw job data for Job ID {job_id} not found.")
        return

    job_data = {
        **raw_jobs_map[job_id],
        **evals_map[job_id],
    }

    display_job_details(job_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review a specific job evaluation.")
    parser.add_argument(
        "job_id", type=int, help="The ID of the job to review."
    )
    args = parser.parse_args()
    main(args.job_id)
