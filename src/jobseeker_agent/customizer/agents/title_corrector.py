from typing import List
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

load_dotenv()



class TitleCorrectorResponse(TypedDict):
    """Response structure for title correction."""
    title: Annotated[str, ..., "The corrected title for the resume."]
    resume: Annotated[str, ..., "Modified resume with the title corrected."]

def correct_title(job_description: str, profil_pro: str, resume: str, model: str="gpt-5-main") -> TitleCorrectorResponse:
    """Corrects the title of the resume."""
    title_corrector_prompt = load_prompt("title_corrector")
    llm = get_llm(model)
    llm = llm.with_structured_output(TitleCorrectorResponse)
    message = HumanMessage(
        content=title_corrector_prompt.format(job_description=job_description, profil_pro=profil_pro, resume=resume)
    )
    response = llm.invoke([message])
    return response

if __name__ == "__main__":
    from jobseeker_agent.scraper.extract_job_details import extract_job_details
    from jobseeker_agent.utils.paths import load_raw_jobs

    JOB_ID = 312
    