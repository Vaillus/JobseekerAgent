from typing import List, Dict
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

load_dotenv()


class KeywordCorrectionSuggestion(TypedDict):
    """A suggestion for a keyword correction."""
    keywords: Annotated[List[str], ..., "The list of keywords concerned with this modification."]
    interpretation: Annotated[str, ..., "What exactly this keyword means for the job, in the context of the job description."]
    importance: Annotated[int, ..., "The importance of this keyword for the job ('not important' = 1, 'important' = 2, 'very important' = 3)"]
    justification: Annotated[str, ..., "Explicit citation from the candidate's profile justifying the keyword addition."]
    confirmation: Annotated[bool, ..., "Confirmation of whether the keyword is still considered relevant for the job."]
    position: Annotated[str, ..., "The place in the resume where the keyword should be inserted. (choose at most one experience. You may add it to both one experience and skill section if it fits best in both)"]


class KeywordCorrectorResponse(TypedDict):
    """Response structure for keyword correction."""
    report: Annotated[List[KeywordCorrectionSuggestion], ..., "A list of suggestions for keyword corrections. If no correction is needed for any keyword, this list will be empty."]
    any_correction: Annotated[bool, ..., "Whether any correction was made."]
    resume: Annotated[str, ..., "Modified resume with the keywords corrected. If no correction was made, this should contain nothing."]

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
    from jobseeker_agent.utils.paths import get_data_path
    from jobseeker_agent.utils.paths import load_cv_template
    import json

    JOB_ID = 73

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = analyze_linkedin_job(job["job_link"])
    job_description = job_details["description"]
    keywords_file = get_data_path() / "resume" / "kw_73.json"
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = json.load(f)
    print(json.dumps(keywords["mismatch_absent"], indent=2, ensure_ascii=False))

    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()

    response = correct_keywords(job_description, profil_pro, cv_template, keywords["mismatch_absent"], model="gpt-5-mini")
    print(json.dumps(response["report"], indent=2, ensure_ascii=False))
    # print(response["resume"])