from typing import List
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

load_dotenv()


class SkillRankerResponse(TypedDict):
    """Response structure for skill ranking."""
    resume: Annotated[str, ..., "The same resume as the template, but with the skills ranked in the order of the ranking."]

def rank_skills(job_description: str, profil_pro: str, cv_template: str, model: str="gpt-5-main") -> SkillRankerResponse:
    """Ranks skills in decreasing order of relevance for the job."""
    skill_ranker_prompt = load_prompt("skill_ranker")
    llm = get_llm(model)
    llm = llm.with_structured_output(SkillRankerResponse)
    message = HumanMessage(
        content=skill_ranker_prompt.format(job_description=job_description, profil_pro=profil_pro, cv_template=cv_template)
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
    print(f"Ranking skills for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])