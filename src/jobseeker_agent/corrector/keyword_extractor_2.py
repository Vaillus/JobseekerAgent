import json
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from typing import List, Dict
from typing_extensions import TypedDict, Annotated

from jobseeker_agent.utils.paths import load_prompt, load_cv_template
from jobseeker_agent.utils.llm import get_llm

load_dotenv()

class KeywordGroup(TypedDict):
    """A group of keywords related to a domain."""
    match_present: Annotated[Dict[str, List[str]], ..., "Same keywords as in the corresponding group in 'grouped' that satisfy the followin criteria: are present in the resume and the candidate's profile."]
    match_absent: Annotated[Dict[str, List[str]], ..., "Same keywords as in the corresponding group in 'grouped' that satisfy the followin criteria: are mentioned in the candidate's profile but are absent in the resume."]
    mismatch_absent: Annotated[Dict[str, List[str]], ..., "Remaining keywords as in the corresponding group in 'grouped' that do not satisfy the criteria for 'match_present' or 'match_absent'."]

class KeywordExtractionResponse(TypedDict):
    """Response structure for keyword extraction from job descriptions."""
    raw: Annotated[List[str], ..., "All raw keywords extracted from the job description. No groups here. Just a raw list. Put them in decreasing order of relevance for the job."]
    grouped: Annotated[Dict[str, List[str]], ..., "Keywords grouped by domain. The key is the domain name. The value is a list of keywords related to that domain. The list is in decreasing order of relevance for the job."]
    classified: Annotated[Dict[str, KeywordGroup], ..., "Exact same list as 'grouped'  but within each group, the keywords are subdivided in three groups: match_present, match_absent and mismatch_absent."]
    
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
    import time
    start_time = time.time()
    response = llm.invoke([message])
    end_time = time.time()
    print(f"Keyword extraction took {end_time - start_time:.2f} seconds")
    # convert to dict
    # response = response.model_dump()

    return response


if __name__ == "__main__":
    from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job
    from jobseeker_agent.utils.paths import load_raw_jobs

    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()

    JOB_ID = 270

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])
    if job_details:
        keywords = extract_keywords(job_details, profil_pro, cv_template, model="gpt-5-mini")
        # print(keywords)
        print(json.dumps(keywords, indent=4))