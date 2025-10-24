
import sys
from pathlib import Path
import webbrowser
import tempfile
import os

from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.utils.paths import (
    load_raw_jobs,
    load_labels,
    save_labels,
    load_prompt,
)


def display_job_in_browser(job, job_details):
    """Creates a temporary HTML file with job details and opens it in the browser."""
    # Generate job summary
    summarize_prompt = load_prompt("summarize_offer")
    profil_pro = load_prompt("profil_pro")
    openai_llm = ChatOpenAI(model="gpt-5")

    message = HumanMessage(
        content=summarize_prompt.format(
            job_description=job_details["description"], profil_pro=profil_pro
        )
    )
    response = openai_llm.invoke([message])
    summary = response.content

    html_content = f"""
    <html>
    <head>
        <title>Job Offer: {job['title']}</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; padding: 2em; max-width: 800px; margin: auto; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; border-bottom: 1px solid #ccc; padding-bottom: 5px;}}
            p {{ white-space: pre-wrap; color: #34495e; }}
            .summary {{ background-color: #f0f0f0; border-left: 5px solid #007bff; padding: 1em; margin-bottom: 2em; }}
        </style>
    </head>
    <body>
        <div class="summary">
            <h3>Summary</h3>
            <p>{summary}</p>
        </div>
        <h1>{job['title']}</h1>
        <h2>{job['company']} - {job['location']}</h2>
        <p><b>Workplace Type:</b> {job_details['workplace_type']}</p>
        <hr>
        <h3>Description</h3>
        <p>{job_details['description']}</p>
    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile(
        "w", delete=False, suffix=".html", encoding="utf-8"
    ) as f:
        f.write(html_content)
        webbrowser.open("file://" + os.path.realpath(f.name))


def main():
    """
    Main function to label job offers.
    """
    raw_jobs = load_raw_jobs()
    labels = load_labels()
    labeled_job_ids = {label["id"] for label in labels}

    for job in raw_jobs:
        if job["id"] in labeled_job_ids:
            continue

        print(f"\n--- Processing Job Offer: {job['id']}: {job['title']} ---")
        job_details = extract_job_details(job["job_link"])

        if job_details:
            display_job_in_browser(job, job_details)

            while True:
                answer = input("Are you interested in this offer? (y/n): ").lower()
                if answer in ["y", "n"]:
                    break
                print("Invalid input. Please enter 'y' or 'n'.")

            interested = answer == "y"
            labels.append({"id": job["id"], "interested": interested})
            save_labels(labels)
            print(f"-> Your answer '{answer}' has been saved.")
        else:
            print(f"Could not retrieve details for job ID {job['id']}.")

    print("\nAll job offers have been labeled.")

if __name__ == "__main__":
    main()
