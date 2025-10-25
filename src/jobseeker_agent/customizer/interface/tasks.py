import os
import json
from . import state, utils
from jobseeker_agent.utils.paths import (
    load_prompt,
    load_cv_template,
    get_data_path,
    load_raw_job,
)
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.customizer.agents.keyword_extractor import extract_keywords
from jobseeker_agent.customizer.agents.keyword_executor import execute_keywords
from jobseeker_agent.customizer.agents.ranker import rank, reorder_experiences, reorder_skills
from jobseeker_agent.customizer.agents.introducer import suggest_introductions


def run_keyword_extraction_task():
    """The actual keyword extraction logic to be run in a background thread."""
    try:
        print("➡️ [THREAD] Keyword extraction task started.")
        state.EXTRACTION_STATUS["status"] = "pending"

        print("    [THREAD] Loading job, prompt, and resume...")
        job = load_raw_job(state.JOB_ID)
        profil_pro = load_prompt("profil_pro")
        resume = load_cv_template()
        print("    [THREAD] ...data loaded.")

        print("    [THREAD] Analyzing LinkedIn job page...")
        job_details = extract_job_details(job["job_link"])
        if not job_details:
            raise Exception("Failed to analyze LinkedIn job page.")
        print("    [THREAD] ...LinkedIn page analyzed.")

        print("    [THREAD] Calling LLM to extract keywords...")
        extraction_response = extract_keywords(job,
            job_details, profil_pro, resume, model="gpt-5-mini"
        )
        print("    [THREAD] ...LLM response received.")

        job_dir = get_data_path() / "resume" / str(state.JOB_ID)
        titles_file = job_dir / "titles.json"
        with open(titles_file, "w", encoding="utf-8") as f:
            json.dump(extraction_response["title_suggestions"], f, indent=4)

        keywords_file = job_dir / "keywords.json"
        with open(keywords_file, "w", encoding="utf-8") as f:
            json.dump(extraction_response["classified"], f, indent=4)

        state.EXTRACTION_STATUS["status"] = "complete"
        print("✅ Background keyword extraction complete.")
    except Exception as e:
        print(f"❌ Background keyword extraction failed: {e}")
        state.EXTRACTION_STATUS["status"] = "failed"
        state.EXTRACTION_STATUS["error"] = str(e)


def run_initial_load_task():
    """Loads all necessary data in a background thread."""
    try:
        print("➡️ [THREAD] Initial load task started.")
        state.DATA_LOADING_STATUS["status"] = "pending"

        job = load_raw_job(state.JOB_ID)
        print("    [THREAD] Analyzing LinkedIn job page...")
        job_details_live = extract_job_details(job["job_link"])
        print("    [THREAD] ...LinkedIn page analyzed.")

        if not job_details_live:
            raise Exception("Failed to fetch live job details from LinkedIn.")

        state.JOB_DESCRIPTION = job_details_live.get(
            "description", "Could not fetch job description."
        )

        print("    [THREAD] Loading reviews.json...")
        reviews_path = get_data_path() / "reviewer" / "reviews.json"
        job_review = {}
        try:
            with reviews_path.open("r", encoding="utf-8") as f:
                reviews_data = json.load(f)
            job_review_data = next(
                (item for item in reviews_data if item.get("id") == state.JOB_ID), None
            )
            if job_review_data:
                job_review = job_review_data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Could not load or parse reviews.json: {e}")
        print("    [THREAD] ...reviews.json loaded.")

        state.JOB_DETAILS = {
            "title": job.get("title"),
            "company_name": job.get("company"),
            "location": job.get("location"),
            "posted_date": job.get("posted_date"),
            "workplace_type": job.get("workplace_type"),
            "job_link": job.get("job_link"),
            "description": state.JOB_DESCRIPTION,
            "score": job_review.get("score"),
            "evaluation_grid": job_review.get("evaluation_grid"),
            "synthesis": job_review.get("synthesis_and_decision"),
        }
        print("--- [SERVER-SIDE] Job Details Prepared ---")
        print(json.dumps(state.JOB_DETAILS, indent=2))
        print("-----------------------------------------")

        job_dir = get_data_path() / "resume" / f"{state.JOB_ID}"
        os.makedirs(job_dir, exist_ok=True)

        # Save job details to a file
        job_details_file = job_dir / "job_details.json"
        with open(job_details_file, "w", encoding="utf-8") as f:
            json.dump(state.JOB_DETAILS, f, indent=4, ensure_ascii=False)

        resume = load_cv_template()
        with open(job_dir / "resume.tex", "w", encoding="utf-8") as f:
            f.write(resume)

        print("    [THREAD] Compiling initial TeX file...")
        utils.compile_tex()
        print("    [THREAD] ...TeX file compiled.")

        state.DATA_LOADING_STATUS["status"] = "complete"
        print("✅ Background initial data load complete.")
        print("JOB DETAILS COLLECTED")

    except Exception as e:
        print(f"❌ Background initial data load failed: {e}")
        state.DATA_LOADING_STATUS["status"] = "failed"
        state.DATA_LOADING_STATUS["error"] = str(e)


def run_ranker_task():
    """The actual ranking logic to be run in a background thread."""
    try:
        print("➡️ [THREAD] Ranker task started.")
        state.RANKING_STATUS["status"] = "pending"

        print("    [THREAD] Loading job, prompt, and resume...")
        profil_pro = load_prompt("profil_pro")
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")
        print("    [THREAD] ...data loaded.")

        print("    [THREAD] Calling LLM to rank experiences and skills...")
        response = rank(
            job_id=state.JOB_ID,
            job_description=state.JOB_DESCRIPTION,
            profil_pro=profil_pro,
            resume=resume_content,
        )
        print("    [THREAD] ...LLM response received.")

        # Reorder the resume content using the new manipulator
        print("    [THREAD] Reordering experiences and skills in .tex file...")
        updated_content = reorder_experiences(resume_content, response["experience_ranking"])
        final_content = reorder_skills(updated_content, response["skill_ranking"])
        resume_file.write_text(final_content, encoding="utf-8")
        print("    [THREAD] ...Reordering complete.")

        print("    [THREAD] Compiling ranked TeX file...")
        utils.compile_tex()
        print("    [THREAD] ...TeX file compiled.")

        state.RANKING_STATUS["status"] = "complete"
        print("✅ Background ranking complete.")
    except Exception as e:
        print(f"❌ Background ranking failed: {e}")
        state.RANKING_STATUS["status"] = "failed"
        state.RANKING_STATUS["error"] = str(e)


def run_introducer_task():
    """The actual introduction suggestion logic to be run in a background thread."""
    try:
        print("➡️ [THREAD] Introducer task started.")
        state.INTRODUCTION_STATUS["status"] = "pending"

        print("    [THREAD] Loading job, prompt, and resume...")
        profil_pro = load_prompt("profil_pro")
        resume_file = get_data_path() / "resume" / str(state.JOB_ID) / "resume.tex"
        resume_content = resume_file.read_text(encoding="utf-8")
        print("    [THREAD] ...data loaded.")

        print("    [THREAD] Calling LLM to suggest introductions...")
        response = suggest_introductions(
            job_id=state.JOB_ID,
            job_description=state.JOB_DESCRIPTION,
            profil_pro=profil_pro,
            resume=resume_content,
        )
        print("    [THREAD] ...LLM response received.")

        state.INTRODUCTION_STATUS["status"] = "complete"
        print("✅ Background introduction suggestion complete.")
    except Exception as e:
        print(f"❌ Background introduction suggestion failed: {e}")
        state.INTRODUCTION_STATUS["status"] = "failed"
        state.INTRODUCTION_STATUS["error"] = str(e)
