from dotenv import load_dotenv
from langchain.schema import HumanMessage
import json
from typing import List
from typing_extensions import TypedDict, Annotated

from jobseeker_agent.utils.paths import load_prompt, load_cv_template
from jobseeker_agent.utils.llm import get_llm
from jobseeker_agent.utils.paths import get_data_path

load_dotenv()


class ExperienceRankerResponse(TypedDict):
    """Response structure for experience ranking."""
    ranking: Annotated[List[str], ..., "Ranking of the experiences in decreasing order of relevance for the job. eg. ['Thales', 'CameraCalibration', 'JobseekerAgent', 'IBM']"]
    resume: Annotated[str, ..., "The same resume as the template, but with the experiences ranked in the order of the ranking."]

def rank_experiences(job_description: str, profil_pro: str, cv_template: str, model: str="gpt-5-main") -> ExperienceRankerResponse:
    """Ranks experiences in decreasing order of relevance for the job."""
    experience_ranker_prompt = load_prompt("experience_ranker")
    llm = get_llm(model)
    llm = llm.with_structured_output(ExperienceRankerResponse)
    message = HumanMessage(
        content=experience_ranker_prompt.format(job_description=job_description, profil_pro=profil_pro, cv_template=cv_template)
    )
    response = llm.invoke([message])
    return response

if __name__ == "__main__":
    from jobseeker_agent.scraper.extract_job_details import extract_job_details
    from jobseeker_agent.utils.paths import load_raw_jobs


    profil_pro = load_prompt("profil_pro")
    cv_template = load_cv_template()
    JOB_ID = 312

    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    print(job)
    print(f"Extracting keywords for job: {job['id']} - {job['title']}")
    job_details = extract_job_details(job["job_link"])
    job_description = job_details["description"]
    ranking, resume = rank_experiences(job_description, profil_pro, cv_template)
    print(ranking)
    file_path = get_data_path() / "resume" / "test" / f"cv-test.tex"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(resume)
        print(f"✅ Le fichier '{file_path}' a été créé avec succès !")
        print("Ouvrez-le avec votre éditeur de texte, il sera correctement formaté.")

    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")