from typing import List, Dict
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

from jobseeker_agent.corrector.keyword_extractor import extract_keywords
from jobseeker_agent.corrector.keyword_corrector import correct_keywords

load_dotenv()



class KeywordInsertionResponse(TypedDict):
    """Response structure for keyword extraction from job descriptions."""
    report: Annotated[List[str], ..., "Report of the keyword insertion process. Says which keywords were inserted and where. Also says which keywords wer not inserted and why."]
    resume: Annotated[str, ..., "Modified resume with the keywords inserted."]

def insert_keywords(job_description: str, profil_pro: str, cv_template: str, keywords: List[str], model: str="gpt-5-main") -> KeywordInsertionResponse:
    """Inserts keywords into the resume."""
    keyword_inserter_prompt = load_prompt("keyword_inserter")
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordInsertionResponse)

    message = HumanMessage(
        content=keyword_inserter_prompt.format(job_description=job_description, profil_pro=profil_pro, cv_template=cv_template, keywords=keywords)
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
    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()
    keywords = extract_keywords(job_details, profil_pro, cv_template)
    print(keywords)
