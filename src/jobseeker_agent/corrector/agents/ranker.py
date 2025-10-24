from dotenv import load_dotenv
from langchain.schema import HumanMessage
import json
from typing import List
from typing_extensions import TypedDict, Annotated

from jobseeker_agent.utils.paths import load_prompt, load_cv_template
from jobseeker_agent.utils.llm import get_llm
from jobseeker_agent.utils.paths import get_data_path, get_ranking_report_path

load_dotenv()

class SkillRanking(TypedDict):
    """Response structure for skill ranking."""
    expertise: Annotated[List[str], ..., "Expertise part of the skills section to rank."]
    programming_language: Annotated[List[str], ..., "Programming language part of the skills section to rank."]
    technologies: Annotated[List[str], ..., "Technologies part of the skills section to rank."]


class RankerResponse(TypedDict):
    """Response structure for ranking."""
    experience_ranking: Annotated[List[str], ..., "Ranking of the experiences in decreasing order of relevance for the job. eg. ['Thales', 'CameraCalibration', 'JobseekerAgent', 'IBM']"]
    skill_ranking: Annotated[SkillRanking, ..., "Ranking of the skills in decreasing order of relevance for the job."]


def rank(
    job_id: int,
    job_description: str, 
    profil_pro: str, 
    resume: str, 
    model: str="gpt-4-turbo") -> RankerResponse:
    """Ranks experiences in decreasing order of relevance for the job."""
    ranking_report_path = get_ranking_report_path(job_id)
    if ranking_report_path.exists():
        with open(ranking_report_path, "r") as f:
            return json.load(f)

    experience_ranker_prompt = load_prompt("ranker")
    llm = get_llm(model)
    llm = llm.with_structured_output(RankerResponse)
    message = HumanMessage(
        content=experience_ranker_prompt.format(job_description=job_description, profil_pro=profil_pro, resume=resume)
    )
    response = llm.invoke([message])

    with open(ranking_report_path, "w") as f:
        json.dump(response, f, indent=4)

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
    job_description = job_details["description"]
    ranking = rank(JOB_ID, job_description, profil_pro, cv_template)
    print(ranking)
    file_path = get_data_path() / "resume" / "test" / f"cv-test.tex"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cv_template)
        print(f"✅ Le fichier '{file_path}' a été créé avec succès !")
        print("Ouvrez-le avec votre éditeur de texte, il sera correctement formaté.")

    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")