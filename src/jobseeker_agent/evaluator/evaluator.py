import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.paths import load_raw_jobs, save_evals, load_evals
from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job

load_dotenv()


def evaluate_job(job, job_details):
    """Evaluates a job and returns a score."""
    evaluation_prompt = load_prompt("evaluation")
    profil_pro = load_prompt("profil_pro")
    openai_llm = ChatOpenAI(model="gpt-5")

    message = HumanMessage(
        content=evaluation_prompt.format(job_description=job_details["description"], profil_pro=profil_pro)
    )
    response = openai_llm.invoke([message])

    result = json.loads(response.content)
    result["id"] = job["id"]

    return result

def print_eval(job_id):
    evaluations = load_evals()
    for evaluation in evaluations:
        if evaluation["id"] == job_id:
            from rich.console import Console
            from rich.markdown import Markdown
            
            console = Console()
            console.print(Markdown(evaluation["evaluation_grid"]))
            return
    print(f"No evaluation found for job ID {job_id}")


def main():
    """Main function to evaluate jobs."""
    raw_jobs = load_raw_jobs()
    for job in raw_jobs:
        evaluations = load_evals()
        if any(e["id"] == job["id"] for e in evaluations):
            print(f"Job {job['id']} already evaluated. Skipping.")
            continue

        job_details = analyze_linkedin_job(job["job_link"])
        result = evaluate_job(job, job_details)

        evaluations.append(result)
        save_evals(evaluations)
        print(f"Saved evaluation for job {job['id']}")


if __name__ == "__main__":
    main()
    # print_eval(1)