from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage
from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Union
import json

from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm


load_dotenv()

class Evaluation(TypedDict):
    """Single evaluation criterion."""
    id: Annotated[int, ..., "The integer id of the criterion from the evaluation grid."]
    criteria: Annotated[str, ..., "The criteria that are met by the job description."]
    evidence: Annotated[str, ..., "The evidence for the criteria."]
    score: Annotated[float, ..., "The score for this criterion."]

class JobReviewResponse(TypedDict):
    """Response structure for job review."""
    evaluation_grid: Annotated[List[Evaluation], ..., "List of evaluations for each relevant evaluation criterion"]
    score: Annotated[float, ..., "raw score computed from the evaluation grid. Can be negative."]



def review(job, job_details, model="gpt-4.1", with_correction=True):
    """Reviews a job using specified model and optional self-correction.
    
    Args:
        job: Job dict containing at least 'id', 'title', 'company', 'location'
        job_details: Job details dict containing 'description'
        model: Model name to use (default: "gpt-4.1")
        with_correction: Whether to apply self-correction (default: True)
    
    Returns:
        Dict with evaluation_grid, score, and job id
    """
    review_prompt = load_prompt("reviewer")
    profil_pro = load_prompt("profil_pro")
    
    llm = get_llm(model)
    llm = llm.with_structured_output(JobReviewResponse)
    
    message = HumanMessage(
        content=review_prompt.format(
            job_description=job_details["description"],
            job_title=job["title"],
            company_name=job["company"],
            location=job["location"],
            profil_pro=profil_pro
        )
    )
    
    response = llm.invoke([message])
    
    if with_correction:
        messages = [
            message,
            AIMessage(content=json.dumps(response)),
            HumanMessage(content="Please correct the evaluation grid. Evaluate each element. Is it correct ? Are there any missing element ? If elements are removed from the evaluation grid, don't put them in the evaluation grid.")
        ]
        response = llm.invoke(messages)
    
    response["id"] = job["id"]
    
    return response
