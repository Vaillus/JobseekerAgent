import json
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from typing import List, Dict
from typing_extensions import TypedDict, Annotated

from jobseeker_agent.utils.paths import load_prompt, load_cv_template
from jobseeker_agent.utils.llm import get_llm

load_dotenv()

class KeywordExtractionResponse(TypedDict):
    """Response structure for keyword extraction from job descriptions."""
    raw: Annotated[List[str], ..., "All raw keywords extracted from the job description. No groups here. Just a raw list. Put them in decreasing order of relevance for the job."]
    match_present: Annotated[Dict[str, List[str]], ..., "Keywords that are in the job description, correspond to candidate's profile and are present in the resume (grouped by domain)."]
    match_absent: Annotated[Dict[str, List[str]], ..., "Keywords that are in the job description, are mentioned in candidate's profile but are absent in the resume (grouped by domain)."]
    mismatch_absent: Annotated[Dict[str, List[str]], ..., "Remaining keywords."]
    irrelevant: Annotated[Dict[str, List[str]], ..., "keywords, skills and domains that are present in the resume, but likely to be irrelevant for the job (grouped by domain)."]



def extract_keywords(job_details: dict, profil_pro: str, cv_template: str, model: str="gpt-5-main") -> KeywordExtractionResponse:
    """Extracts keywords from a job description."""
    keyword_extractor_prompt = load_prompt("keyword_extractor")
    
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordExtractionResponse)

    message = HumanMessage(
        content=keyword_extractor_prompt.format(
            job_description=job_details["description"],
            profil_pro=profil_pro,
            cv_template=cv_template,
        )
    )
    response = llm.invoke([message])
    # convert to dict
    # response = response.model_dump()

    return response


if __name__ == "__main__":
    from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job
    from jobseeker_agent.utils.paths import load_raw_jobs

    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()

    JOB_ID = 312

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])
    if job_details:
        keywords = extract_keywords(job_details, profil_pro, cv_template)
        print(keywords)
        # print(json.dumps(keywords.dict(), indent=4))
