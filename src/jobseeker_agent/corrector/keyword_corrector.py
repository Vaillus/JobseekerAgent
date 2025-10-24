from typing import List, Dict
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

load_dotenv()


class KeywordCorrectionSuggestion(TypedDict):
    """A suggestion for a keyword correction."""
    keyword: Annotated[List[str], ..., "The keyword concerned with this modification."]
    interpretation: Annotated[str, ..., "What exactly this keyword means for the job, in the context of the job description."]
    importance: Annotated[int, ..., "The importance of this keyword for the job ('not important' = 1, 'important' = 2, 'very important' = 3)"]
    justification: Annotated[str, ..., "Explicit citation from the candidate's profile justifying the keyword addition."]
    confirmation: Annotated[bool, ..., "True if you still believe this keyword should be added to the resume, given interpretation, importance and justification, otherwise False. False if importance is < 3."]
    position: Annotated[str, ..., "The position in the resume where the keyword should be inserted (e.g., in a specific experience or skill section). (choose at most one experience. You may add it to both one experience and skill section if it fits best in both). If 'confirmation' is false, this key should be None."]


class KeywordCorrectorResponse(TypedDict):
    """Response structure for keyword correction."""
    report: Annotated[List[KeywordCorrectionSuggestion], ..., "A list of suggestions for keyword corrections. If no correction is needed for any keyword, this list will be empty."]
    any_correction: Annotated[bool, ..., "Whether any correction was made."]
    resume: Annotated[str, ..., "Modified resume with the keywords corrected. If no correction was made, this should contain nothing."]
    keywords_present: Annotated[Dict[str, List[str]], ..., "Keywords present in the resume, updated with the new keywords that were corrected in this process. do not return empty lists. If the value of some key is empty, remove the key from the dictionary. Try to add the new keywords to existing groups when relevant."]

def correct_keywords(job_description: str, profil_pro: str, cv_template: str, keywords_present: List[str], keywords_absent: List[str], model: str="gpt-5-main") -> KeywordCorrectorResponse:
    """Corrects keywords in the resume."""
    keyword_corrector_prompt = load_prompt("keyword_corrector")
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordCorrectorResponse)
    message = HumanMessage(
        content=keyword_corrector_prompt.format(job_description=job_description, profil_pro=profil_pro, cv_template=cv_template, keywords_present=keywords_present, keywords_absent=keywords_absent)
    )
    response = llm.invoke([message])
    return response

if __name__ == "__main__":
    from jobseeker_agent.scraper.extract_job_details import extract_job_details
    from jobseeker_agent.utils.paths import load_raw_jobs
    from jobseeker_agent.utils.paths import (load_cv_template, get_project_root, get_data_path, load_raw_job)

    import json

    JOB_ID = 270

    job = load_raw_job(JOB_ID)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = extract_job_details(job["job_link"])
    job_description = job_details["description"]
    # keywords_file = get_data_path() / "resume" / f"kw_{JOB_ID}.json"
    keywords_file = get_data_path() / "resume" / "process" / "3_inserted_keywords" / f"keywords.json"
    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = json.load(f)
    print(json.dumps(keywords["mismatch_absent"], indent=2, ensure_ascii=False))

    profil_pro = load_prompt("profil_pro")
    # cv_template = load_cv_template()
    cv_path = get_data_path() / "resume" / "process" / "3_inserted_keywords" / f"resume.tex"
    with open(cv_path, "r", encoding="utf-8") as f:
        cv_template = f.read()

    response = correct_keywords(job_description, profil_pro, cv_template, keywords["match_present"], keywords["mismatch_absent"], model="gpt-5-mini")
    print(json.dumps(response["report"], indent=2, ensure_ascii=False))
    # print(response["resume"])