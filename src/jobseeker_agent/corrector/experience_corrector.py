from typing import List
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

load_dotenv()

class ExperienceCorrectorResponse(TypedDict):
    """Response structure for experience correction."""
    report: Annotated[List[str], ..., "Report of the experience correction process. Says which experiences were corrected and where, if any. If none, say so."]
    any_correction: Annotated[bool, ..., "Whether any correction was made."]
    resume: Annotated[str, ..., "Modified resume with the experiences corrected."]

def correct_experiences(job_description: str, profil_pro: str, resume: str, model: str="gpt-5-main") -> ExperienceCorrectorResponse:
    """Corrects experiences in the resume."""
    experience_corrector_prompt = load_prompt("experience_corrector")
    llm = get_llm(model)
    llm = llm.with_structured_output(ExperienceCorrectorResponse)
    message = HumanMessage(
        content=experience_corrector_prompt.format(job_description=job_description, profil_pro=profil_pro, resume=resume)
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
    print(f"Correcting experiences for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])
    job_description = job_details["description"]
    profil_pro = load_prompt("profil_pro")
    resume = load_cv_template()
    correct_experiences(job_description, profil_pro, resume)