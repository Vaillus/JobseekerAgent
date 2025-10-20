from jobseeker_agent.corrector.experience_corrector import correct_experiences
from jobseeker_agent.corrector.title_corrector import correct_title
from jobseeker_agent.corrector.experience_ranker import rank_experiences
from jobseeker_agent.corrector.skill_ranker import rank_skills
from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.paths import load_cv_template
from jobseeker_agent.corrector.keyword_extractor import extract_keywords
from jobseeker_agent.corrector.keyword_inserter import insert_keywords
from jobseeker_agent.corrector.keyword_corrector import correct_keywords

from jobseeker_agent.utils.paths import get_data_path


if __name__ == "__main__":
    from jobseeker_agent.scraper.linkedin_analyzer import analyze_linkedin_job
    from jobseeker_agent.utils.paths import load_raw_jobs

    JOB_ID = 312
    model = "gpt-4o-mini"
    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == JOB_ID), None)
    job_details = analyze_linkedin_job(job["job_link"])
    job_description = job_details["description"]
    profil_pro = load_prompt("profil_pro")
    resume = load_cv_template()
    response = rank_experiences(job_description, profil_pro, resume, model)
    print(response["ranking"])
    resume = response["resume"]

    keywords = extract_keywords(job_details, profil_pro, resume, model)
    import json
    print(json.dumps(keywords, indent=2, ensure_ascii=False))

    response = insert_keywords(job_description, profil_pro, resume, keywords, model)
    print(response["report"])
    resume = response["resume"]

    response = correct_keywords(job_description, profil_pro, resume, keywords, model)
    if response["any_correction"]:
        print(response["report"])
        resume = response["resume"]

    response = rank_skills(job_description, profil_pro, resume, model)
    resume = response["resume"]

    response = correct_title(job_description, profil_pro, resume, model)
    print(response["title"])
    resume = response["resume"]

    response = correct_experiences(job_description, profil_pro, resume, model)
    if response["any_correction"]:
        print(response["report"])
        resume = response["resume"]

    file_path = get_data_path() / "resume" / "test" / f"cv-test.tex"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(resume)
        print(f"✅ Le fichier '{file_path}' a été créé avec succès !")
        print("Ouvrez-le avec votre éditeur de texte, il sera correctement formaté.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")