from dotenv import load_dotenv
from langchain.schema import HumanMessage
import json
from typing import List
from typing_extensions import TypedDict, Annotated

from jobseeker_agent.utils.paths import load_prompt, load_cv_template
from jobseeker_agent.utils.llm import get_llm
from jobseeker_agent.utils.paths import get_data_path

load_dotenv()

class IntroducerResponse(TypedDict):
    """Response structure for opening lines suggestions."""
    opening_lines: List[Annotated[str, ..., "Opening lines for the resume."]]
    

def suggest_introductions(
    job_description: str, 
    profil_pro: str, 
    resume: str, 
    model: str="gpt-5-mini") -> IntroducerResponse:
    """Suggest introductions for the resume."""
    introducer_prompt = load_prompt("introducer")
    llm = get_llm(model)
    llm = llm.with_structured_output(IntroducerResponse)
    message = HumanMessage(
        content=introducer_prompt.format(job_description=job_description, profil_pro=profil_pro, resume=resume)
    )
    response = llm.invoke([message])
    return response
