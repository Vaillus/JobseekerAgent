from typing import List, Dict
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

from jobseeker_agent.utils.paths import load_cv_template

load_dotenv()



class KeywordInsertionResponse(TypedDict):
    """Response structure for keyword extraction from job descriptions."""
    report: Annotated[List[str], ..., "Report of the keyword insertion process. Says which keywords were inserted and where. Also says which keywords wer not inserted and why."]
    resume: Annotated[str, ..., "Modified resume with the keywords inserted. It must be correct .tex code. For example, & character in the text should be escaped as \& when displayed in LaTeX."]
    keywords_present: Annotated[Dict[str, List[str]], ..., "Keywords present in the resume, updated with the new keywords that were inserted in this process. do not return empty lists. If the value of some key is empty, remove the key from the dictionary. Try to add the new keywords to existing groups when relevant."]

def insert_keywords(job_description: str, profil_pro: str, cv_template: str, keywords_present: List[str], keywords_absent: List[str], model: str="gpt-5-main") -> KeywordInsertionResponse:
    """Inserts keywords into the resume."""
    keyword_inserter_prompt = load_prompt("keyword_inserter")
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordInsertionResponse)

    message = HumanMessage(
        content=keyword_inserter_prompt.format(job_description=job_description, profil_pro=profil_pro, cv_template=cv_template, keywords_present=keywords_present, keywords_absent=keywords_absent)
    )
    response = llm.invoke([message])
    return response

if __name__ == "__main__":
    from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job
    from jobseeker_agent.utils.paths import load_raw_jobs

    JOB_ID = 270

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])
    job_description = job_details["description"]
    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()

    import json
    from jobseeker_agent.utils.paths import get_data_path
    
    keywords_file = get_data_path() / "resume" / "kw_270.json"
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = json.load(f)
    print("Keywords present in the resume:")
    print(json.dumps(keywords["match_present"], indent=2, ensure_ascii=False))
    print("Keywords absent in the resume:")
    print(json.dumps(keywords["match_absent"], indent=2, ensure_ascii=False))

    response = insert_keywords(job_description, profil_pro, cv_template, keywords["match_present"], keywords["match_absent"], model="gpt-5-mini")
    print(*response["report"], sep="\n")
    print(json.dumps(response["keywords_present"], indent=2, ensure_ascii=False))
    # print(response["resume"])
