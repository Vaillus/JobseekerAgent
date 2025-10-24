import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Union

from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.paths import load_raw_jobs, save_evals, load_evals, load_labels
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.utils.llm import get_llm


load_dotenv()

class JobEvaluationResponse(TypedDict):
    """Response structure for job evaluation."""
    evaluation_grid: Annotated[List[Dict[str, Union[str, float]]], ..., "List of dictionaries with keys 'criteria', 'evidence', and 'score' for each relevant evaluation criterion"]
    score: Annotated[float, ..., "raw score computed from the evaluation grid. Can be negative."]
    synthesis_and_decision: Annotated[str, ..., "text of the synthesis and decision points, should provide context for further examination."]
    preferred_pitch: Annotated[int, ..., "Preferred pitch for the job. 1: Large Group, 2: Startup, 3: General Tech, 4: General"]



def evaluate_job(job, job_details, model="gpt-5-mini"):
    """Evaluates a job and returns a score."""
    evaluation_prompt = load_prompt("evaluation")
    profil_pro = load_prompt("profil_pro")
    llm = get_llm(model)
    llm = llm.with_structured_output(JobEvaluationResponse)
    # openai_llm = ChatOpenAI(model="gpt-4o")

    message = HumanMessage(
        content=evaluation_prompt.format(job_description=job_details["description"], profil_pro=profil_pro)
    )
    response = llm.invoke([message])


    # result = json.loads(response)
    response["id"] = job["id"]

    return response

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
    
    job_details = extract_job_details(job["job_link"])
    result = evaluate_job(job, job_details)

    evaluations = load_evals(generation_id)
    evaluations.append(result)
    save_evals(evaluations, generation_id)
    print(f"Saved evaluation for job {job['id']}")
    return result


def main(generation_id: int, model=str):
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

        job_details = extract_job_details(job["job_link"])
        result = evaluate_job(job, job_details, model=model)

        evaluations.append(result)
        save_evals(evaluations, generation_id)
        print(f"Saved evaluation for job {job['id']}")


if __name__ == "__main__":
    # load specific job
    # job_id = 15
    # raw_jobs = load_raw_jobs()
    # job = next((j for j in raw_jobs if j["id"] == job_id), None)
    # job_details = analyze_linkedin_job(job["job_link"])
    # result = evaluate_job(job, job_details, model="gpt-5-mini")
    
    # import json
    # formatted_result = json.dumps(result, indent=2, ensure_ascii=False)
    # # Replace escaped newlines with actual newlines for better readability
    # formatted_result = formatted_result.replace('\\n', '\n')
    # print(formatted_result)

    generation_id = 5
    main(generation_id, "gpt-5-mini")
    # result = evaluate_from_id(25, generation_id)
    # print(result)
    # main(generation_id)
    # print_eval(1, GENERATION_ID)

