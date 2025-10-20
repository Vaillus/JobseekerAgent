from typing import List, Dict
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

load_dotenv()


class KeywordCorrectorResponse(TypedDict):
    """Response structure for keyword correction."""
    report: Annotated[List[str], ..., "Report of the keyword correction process. Says which keywords were corrected and where, if any. If none, say so."]
    any_correction: Annotated[bool, ..., "Whether any correction was made."]
    resume: Annotated[str, ..., "Modified resume with the keywords corrected."]

def correct_keywords(job_description: str, profil_pro: str, cv_template: str, keywords: List[str], model: str="gpt-5-main") -> KeywordCorrectorResponse:
    """Corrects keywords in the resume."""
    keyword_corrector_prompt = load_prompt("keyword_corrector")
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordCorrectorResponse)
    message = HumanMessage(
        content=keyword_corrector_prompt.format(job_description=job_description, profil_pro=profil_pro, cv_template=cv_template, keywords=keywords)
    )
    response = llm.invoke([message])
    return response

if __name__ == "__main__":
    from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job
    from jobseeker_agent.utils.paths import load_raw_jobs

    JOB_ID = 312

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])
    job_description = job_details["description"]