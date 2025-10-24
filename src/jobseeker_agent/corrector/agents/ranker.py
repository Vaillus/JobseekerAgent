from dotenv import load_dotenv
from langchain.schema import HumanMessage
import json
from typing import List, Dict
from typing_extensions import TypedDict, Annotated
import re

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


def reorder_experiences(tex_content: str, ranked_experiences: List[str]) -> str:
    """
    Reorders the experience entries in the resume's .tex file content.
    """
    section_pattern = re.compile(r"(\\section{Experience}.*?)(?=\\section{|\\end{resume})", re.DOTALL)
    section_match = section_pattern.search(tex_content)
    if not section_match:
        return tex_content

    experience_section_content = section_match.group(1)
    
    # Find all individual experience entries
    entry_pattern = re.compile(r"(?:\\textbf{|Personal Project –).*?(?=\\vspace{-2mm})", re.DOTALL)
    entries = entry_pattern.findall(experience_section_content)
    
    # Add the vspace back to each entry as it's used as a delimiter
    entries = [entry + "\\vspace{-2mm}\n" for entry in entries]

    entry_map = {}
    for block in entries:
        key = "Unknown"
        if "\\textbf{Thales DMS}" in block: key = "Thales DMS"
        elif "Job-Seeking Agentic Workflow" in block: key = "JobseekerAgent"
        elif "Camera Calibration for Autonomous Vehicle" in block: key = "CameraCalibration"
        elif "\\textbf{IBM France}" in block: key = "IBM France"
        entry_map[key] = block

    # Build the new section
    new_entries_str = ""
    for exp_name in ranked_experiences:
        if exp_name in entry_map:
            new_entries_str += entry_map[exp_name]

    # Replace old entries block with the new one
    # We need to find the content between \section{Experience} and the next \section
    content_inside_section = re.search(r"\\section{Experience}(.*?)(?=\\section{|\\end{resume})", tex_content, re.DOTALL)
    if content_inside_section:
        old_block = content_inside_section.group(1)
        # Reconstruct the section with title and new entries
        new_section = f"\\section{{Experience}}\n{new_entries_str}"
        return tex_content.replace(f"\\section{{Experience}}{old_block}", new_section)

    return tex_content # Fallback

def reorder_skills(tex_content: str, ranked_skills: Dict[str, List[str]]) -> str:
    """
    Reorders the skills within each category in the resume's .tex file content.
    """
    skill_ranking = ranked_skills
    for category, skills in skill_ranking.items():
        tex_category = category

        # This more flexible pattern should find the category regardless of minor spacing issues
        pattern = re.compile(f"(\\{{\\\\sl\\s*{tex_category}:}})(.*?)(?=\\\\|\\n)", re.IGNORECASE)
        
        def replacer(match):
            prefix = match.group(1)
            new_skills_str = "; ".join(skills)
            return f"{prefix} {new_skills_str}"

        tex_content, count = pattern.subn(replacer, tex_content, count=1)
        if count == 0:
            print(f"Warning: Could not find skill category '{tex_category}' in resume to reorder.")
            
    return tex_content

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