from dotenv import load_dotenv
from langchain.schema import HumanMessage
from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Union

from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm


load_dotenv()

class JobReviewResponse(TypedDict):
    """Response structure for job review."""
    evaluation_grid: Annotated[List[Dict[str, Union[str, float]]], ..., "List of dictionaries with keys 'criteria', 'evidence', and 'score' for each relevant evaluation criterion"]
    score: Annotated[float, ..., "raw score computed from the evaluation grid. Can be negative."]
    synthesis_and_decision: Annotated[str, ..., "text of the synthesis and decision points, should provide context for further examination."]
    preferred_pitch: Annotated[int, ..., "Preferred pitch for the job. 1: Large Group, 2: Startup, 3: General Tech, 4: General"]



def review(job, job_details, model="gpt-5-mini"):
    """Reviews a job."""
    review_prompt = load_prompt("reviewer")
    profil_pro = load_prompt("profil_pro")
    llm = get_llm(model)
    llm = llm.with_structured_output(JobReviewResponse)

    message = HumanMessage(
        content=review_prompt.format(job_description=job_details["description"], profil_pro=profil_pro)
    )
    response = llm.invoke([message])

    response["id"] = job["id"]

    return response
