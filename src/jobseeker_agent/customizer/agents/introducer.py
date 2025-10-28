from dotenv import load_dotenv
from langchain.schema import HumanMessage
import json
from typing import List
from typing_extensions import TypedDict, Annotated

from jobseeker_agent.utils.paths import load_prompt, load_cv_template
from jobseeker_agent.utils.llm import get_llm
from jobseeker_agent.utils.paths import get_data_path, get_opening_lines_path

load_dotenv()


class IntroducerResponse(TypedDict):
    """Response structure for opening lines suggestions."""

    opening_lines: List[Annotated[str, ..., "Opening lines for the resume."]]


def suggest_introductions(
    job_id: int,
    job_description: str,
    profil_pro: str,
    synthesis_and_decision: str,
    resume: str,
    model: str = "gpt-5-mini",
) -> IntroducerResponse:
    """Suggest introductions for the resume."""
    opening_lines_path = get_opening_lines_path(job_id)
    if opening_lines_path.exists():
        with open(opening_lines_path, "r") as f:
            return json.load(f)

    introducer_prompt = load_prompt("introducer")
    llm = get_llm(model, temperature= 0.2)
    llm = llm.with_structured_output(IntroducerResponse)
    message = HumanMessage(
        content=introducer_prompt.format(
            job_description=job_description, profil_pro=profil_pro, synthesis_and_decision=synthesis_and_decision, resume=resume
        )
    )
    response = llm.invoke([message])

    with open(opening_lines_path, "w") as f:
        json.dump(response, f, indent=4)
        
    return response
