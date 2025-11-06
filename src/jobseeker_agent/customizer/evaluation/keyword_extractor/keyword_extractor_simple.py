import json
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from typing import List
from typing_extensions import TypedDict, Annotated
from pathlib import Path

from jobseeker_agent.utils.paths import load_cv_template
from jobseeker_agent.utils.llm import get_llm

load_dotenv()

class KeywordExtractionResponse(TypedDict):
    """Simplified response structure for keyword extraction from job descriptions."""
    keywords: Annotated[List[str], ..., "All relevant keywords extracted from the job description, in decreasing order of relevance for the job. Flat list, no grouping."]

def load_prompt_simple() -> str:
    """Load the simplified keyword extractor prompt."""
    prompt_path = Path(__file__).parent / "keyword_extractor_simple.md"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_keywords_simple(job_title: str, job_description: str, profil_pro: str, cv_template: str, model: str = "gpt-4o") -> KeywordExtractionResponse:
    """Extracts keywords from a job description (simplified version - returns flat list only)."""
    keyword_extractor_prompt = load_prompt_simple()
    
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordExtractionResponse)
    
    message = HumanMessage(
        content=keyword_extractor_prompt.format(
            job_title=job_title,
            job_description=job_description,
            profil_pro=profil_pro,
            cv_template=cv_template,
        )
    )
    import time
    start_time = time.time()
    response = llm.invoke([message])
    end_time = time.time()
    print(f"Keyword extraction took {end_time - start_time:.2f} seconds")
    
    return response


if __name__ == "__main__":
    from jobseeker_agent.scraper.extract_job_details import extract_job_details
    from jobseeker_agent.utils.paths import load_raw_jobs, load_prompt

    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()

    JOB_ID = 18

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = extract_job_details(job["job_link"])
    if job_details:
        keywords = extract_keywords_simple(
            job_title=job["title"],
            job_description=job_details["description"],
            profil_pro=profil_pro,
            cv_template=cv_template,
            model="gpt-4o"
        )
        print(json.dumps(keywords, indent=4))
        print(f"\nTotal keywords: {len(keywords['keywords'])}")

