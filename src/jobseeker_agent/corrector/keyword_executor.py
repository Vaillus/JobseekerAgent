from typing import List, Dict, Any
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm

from jobseeker_agent.utils.paths import load_cv_template

load_dotenv()

class KeywordExecutorResponse(TypedDict):
    """Response structure for keyword executor."""
    report: Annotated[List[str], ..., "The report of the editions applied to the document."]
    resume: Annotated[str, ..., "Modified resume with the modifications applied."]

def execute_keywords(job_description: str, profil_pro: str, resume: str, instructions: List[Dict[str, Any]], model: str="gpt-5-mini") -> KeywordExecutorResponse:
    """Executes the keyword executor."""
    keyword_executor_prompt = load_prompt("keyword_executor")
    llm = get_llm(model)
    llm = llm.with_structured_output(KeywordExecutorResponse)
    message = HumanMessage(
        content=keyword_executor_prompt.format(job_description=job_description, profil_pro=profil_pro, resume=resume, instructions=instructions)
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
    job_details = extract_job_details(job["job_link"])
    job_description = job_details["description"]

    # Load validated keywords and instructions
    keywords_file = get_data_path() / "resume" / str(JOB_ID) / "keywords_validated.json"
    with open(keywords_file, "r", encoding="utf-8") as f:
        instructions = json.load(f)
    print(instructions)

    profil_pro = load_prompt("profil_pro")
    resume = load_cv_template()

    response = execute_keywords(job_description, profil_pro, resume, instructions, model="gpt-5-mini")
    print(*response["report"], sep="\n\n")