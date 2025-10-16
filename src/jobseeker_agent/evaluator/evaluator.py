import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.paths import load_raw_jobs, save_evals, load_evals, load_labels
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

def print_eval(job_id, generation_id: int):
    evaluations = load_evals(generation_id)
    for evaluation in evaluations:
        if evaluation["id"] == job_id:
            from rich.console import Console
            from rich.markdown import Markdown
            
            console = Console()
            console.print(Markdown(evaluation["evaluation_grid"]))
            return
    print(f"No evaluation found for job ID {job_id}")

def evaluate_from_id(job_id, generation_id: int):
    job = load_raw_jobs()
    job = next((j for j in job if j["id"] == job_id), None)
    if not job:
        print(f"No job found for ID {job_id}")
        return
    
    job_details = analyze_linkedin_job(job["job_link"])
    result = evaluate_job(job, job_details)

    evaluations = load_evals(generation_id)
    evaluations.append(result)
    save_evals(evaluations, generation_id)
    print(f"Saved evaluation for job {job['id']}")
    return result


def main(generation_id: int):
    """Main function to evaluate jobs."""
    labels = load_labels(generation_id)
    if not labels:
        print(f"No labels found for generation {generation_id}. Nothing to evaluate.")
        return
    
    labeled_job_ids = {label["id"] for label in labels}
    
    raw_jobs = load_raw_jobs()
    jobs_to_evaluate = [job for job in raw_jobs if job["id"] in labeled_job_ids]

    evaluations = load_evals(generation_id)
    evaluated_job_ids = {e["id"] for e in evaluations}

    for job in jobs_to_evaluate:
        if job["id"] in evaluated_job_ids:
            print(f"Job {job['id']} already evaluated. Skipping.")
            continue

        job_details = analyze_linkedin_job(job["job_link"])
        result = evaluate_job(job, job_details)

        evaluations.append(result)
        save_evals(evaluations, generation_id)
        print(f"Saved evaluation for job {job['id']}")


if __name__ == "__main__":
    generation_id = 3
    # result = evaluate_from_id(25, GENERATION_ID)
    # print(result)
    main(generation_id)
    # print_eval(1, GENERATION_ID)