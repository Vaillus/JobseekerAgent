from datetime import date
from flask import Blueprint, jsonify, render_template, request
import markdown
import threading

from jobseeker_agent.utils.paths import (
    load_reviews,
    load_raw_jobs,
    load_job_statuses,
    save_job_statuses,
    load_scraping_destinations,
    save_scraping_destinations,
    save_reviews,
    load_processed_jobs,
    save_processed_jobs,
)
from jobseeker_agent.scraper.extract_job_details import extract_job_details, extract_full_job_details
from jobseeker_agent.scraper.run_scraper import run_scraping
from jobseeker_agent.scraper.update_job_statuses import update_job_statuses
from jobseeker_agent.scraper.job_manager import add_new_job, load_raw_jobs as load_raw_jobs_manager, save_raw_jobs
from jobseeker_agent.reviewer.review_batch import JobReviewer
from jobseeker_agent.reviewer.agents.reviewer import review as review_agent
from jobseeker_agent.interface import state

bp = Blueprint("reviewer", __name__)

# Data loaded at module level (will be loaded when blueprint is imported)
print("--- Loading reviewer data ---")
reviews = load_reviews()
raw_jobs = load_raw_jobs()
print(f"Loaded {len(reviews)} reviews and {len(raw_jobs)} raw jobs.")

reviews_map = {int(e["id"]): e for e in reviews}
raw_jobs_map = {int(j["id"]): j for j in raw_jobs}

base_jobs = []
job_ids = sorted(list(set(raw_jobs_map.keys()) & set(reviews_map.keys())))
print(f"Found {len(job_ids)} common job IDs.")

for job_id in job_ids:
    # Skip jobs whose raw status is Closed
    if raw_jobs_map.get(job_id, {}).get("status") == "Closed":
        continue
    job_data = {
        "id": job_id,
        **raw_jobs_map.get(job_id, {}),
        **reviews_map.get(job_id, {}),
    }
    base_jobs.append(job_data)

# Sort by score descending
base_jobs.sort(key=lambda x: x.get("score", -float("inf")), reverse=True)
print("Jobs sorted by score.")


def run_review_latest_task(count: int):
    try:
        print(f"Starting latest-first review of {count} jobs")
        reviewer = JobReviewer()
        state.REVIEW_STATUS = {"status": "running", "current": 0, "total": count, "error": None}
        for i in range(count):
            job_review = reviewer.review_next_latest("gpt-5-mini", with_correction=True, reasoning_level="low")
            if job_review is None:
                state.REVIEW_STATUS["total"] = i
                break
            state.REVIEW_STATUS["current"] = i + 1
            print(f"Reviewed {i + 1}/{count} jobs (latest-first)")
        state.REVIEW_STATUS["status"] = "completed"
        print(f"Review (latest-first) completed. Reviewed {state.REVIEW_STATUS['current']} jobs.")
    except Exception as e:
        print(f"Error during latest-first review: {str(e)}")
        import traceback
        traceback.print_exc()
        state.REVIEW_STATUS = {
            "status": "error",
            "current": state.REVIEW_STATUS.get("current", 0),
            "total": count,
            "error": str(e)
        }

@bp.route("/")
def dashboard():
    """Renders the main dashboard HTML."""
    print("--- Request received for / route ---")
    job_statuses = load_job_statuses()
    job_statuses_map = {int(p["id"]): p for p in job_statuses}

    all_jobs = []
    for job in base_jobs:
        job_with_status = job.copy()
        job_with_status["status"] = job_statuses_map.get(job_with_status.get("id"))
        
        # Convert synthesis from Markdown to HTML
        if "synthesis_and_decision" in job_with_status and job_with_status["synthesis_and_decision"]:
            job_with_status["synthesis_and_decision"] = markdown.markdown(job_with_status["synthesis_and_decision"])

        all_jobs.append(job_with_status)

    unprocessed_jobs = [j for j in all_jobs if not j["status"]]
    print(f"Rendering dashboard with {len(unprocessed_jobs)} unprocessed jobs.")

    # Calculate review count info
    # Total: all open jobs (not Closed) in raw_jobs
    total_open_count = len([j for j in raw_jobs if j.get("status") != "Closed"])
    # Unreviewed: open jobs that are NOT in reviews.json
    unreviewed_count = len([
        j for j in raw_jobs 
        if j.get("status") != "Closed" and j["id"] not in reviews_map
    ])
    percentage = (unreviewed_count / total_open_count * 100) if total_open_count > 0 else 0
    review_count_info = {
        "unreviewed_count": unreviewed_count,
        "total_open_count": total_open_count,
        "percentage": round(percentage, 1)
    }

    return render_template(
        "reviewer/dashboard.html",
        sidebar_jobs=unprocessed_jobs,
        all_jobs=all_jobs,
        review_count_info=review_count_info,
    )


@bp.route("/job/<int:job_id>")
def get_job_details(job_id: int):
    """Fetches live job details and returns as JSON."""
    print(f"--- Request received for /job/{job_id} ---")
    job_link = raw_jobs_map.get(job_id, {}).get("job_link")
    if not job_link:
        print(f"Job ID {job_id} not found in raw_jobs_map.")
        return jsonify({"error": "Job not found"}), 404
    
    print(f"Fetching live details for job link: {job_link}")
    
    # Utiliser extract_full_job_details qui est plus robuste
    from jobseeker_agent.scraper.extract_job_details import extract_full_job_details
    import time
    
    # Ajouter un petit délai pour éviter le rate limiting si plusieurs requêtes sont faites rapidement
    time.sleep(0.5)
    
    live_details = extract_full_job_details(job_link)
    
    # Si ça échoue, essayer avec extract_job_details en dernier recours
    if not live_details or not live_details.get("description"):
        print("extract_full_job_details failed, trying extract_job_details...")
        time.sleep(0.5)  # Délai supplémentaire
        live_details = extract_job_details(job_link)
    
    if not live_details or not live_details.get("description"):
        print("Could not fetch live details.")
        return jsonify({"description": None})

    # Convert description from Markdown to HTML
    if "description" in live_details and live_details["description"]:
        processed_markdown = live_details["description"].replace('**', '## ')
        live_details["description"] = markdown.markdown(processed_markdown)

    print("Successfully fetched live details.")
    return jsonify(live_details)


@bp.route("/status/<int:job_id>", methods=["POST"])
def update_status(job_id: int):
    """Marks a job's status as applied or not interested."""
    print(f"--- Request received for /status/{job_id} ---")
    data = request.get_json()
    has_applied = data.get("applied")
    print(f"Updating status for job {job_id} to applied={has_applied}")

    if has_applied is None:
        return jsonify({"success": False, "message": "Missing 'applied' field"}), 400

    today = date.today().isoformat()
    status = {"id": job_id, "date": today, "applied": has_applied}

    current_statuses = load_job_statuses()
    
    # Remove existing status for this job_id if it exists, then add the new one
    current_statuses = [s for s in current_statuses if s['id'] != job_id]
    current_statuses.append(status)
    
    save_job_statuses(current_statuses)
    print(f"Status for job {job_id} saved successfully.")

    return jsonify({"success": True, "status": status})


@bp.route("/scrape", methods=["POST"])
def start_scraping():
    """Launch scraping in a background thread."""
    print("--- Request received for /scrape ---")
    data = request.get_json()
    # Support either days (int) or legacy time_horizon (str)
    if "days" in data:
        try:
            time_horizon = int(data["days"])
        except Exception:
            return jsonify({"success": False, "message": "Invalid 'days' value"}), 400
    else:
        time_horizon = data.get("time_horizon", "day")

    # Optional destinations list; if not provided, load from server-side config
    destinations = data.get("destinations")
    if destinations is None:
        destinations = load_scraping_destinations()
    
    if state.SCRAPING_THREAD and state.SCRAPING_THREAD.is_alive():
        return jsonify({"success": False, "message": "Scraping already in progress"}), 400
    
    # Reset status
    state.SCRAPING_STATUS = {"status": "running", "new_jobs_count": 0, "error": None}
    
    def scrape_task():
        try:
            print(f"Starting scraping with time_horizon={time_horizon}")
            new_jobs_count = run_scraping(max_time=time_horizon, destinations_config=destinations)
            state.SCRAPING_STATUS = {
                "status": "completed",
                "new_jobs_count": new_jobs_count,
                "error": None
            }
            print(f"Scraping completed. Added {new_jobs_count} new jobs.")
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            state.SCRAPING_STATUS = {
                "status": "error",
                "new_jobs_count": 0,
                "error": str(e)
            }
    
    state.SCRAPING_THREAD = threading.Thread(target=scrape_task)
    state.SCRAPING_THREAD.start()
    
    return jsonify({"success": True, "message": "Scraping started"})


@bp.route("/scrape/config", methods=["GET"])
def get_scraping_config():
    """Return scraping destinations configuration. If empty, generate defaults in-memory."""
    destinations = load_scraping_destinations()
    if not destinations:
        destinations = [
            {"id": 1, "location": "Sidney, Australia", "remote_type": "any", "enabled": True},
            {"id": 2, "location": "Australia", "remote_type": "remote", "enabled": True},
            {"id": 3, "location": "Paris, France", "remote_type": "any", "enabled": True},
            {"id": 4, "location": "France", "remote_type": "remote", "enabled": True},
            {"id": 5, "location": "Germany", "remote_type": "remote", "enabled": True},
            {"id": 6, "location": "Amsterdam, Netherlands", "remote_type": "any", "enabled": True},
            {"id": 7, "location": "Netherlands", "remote_type": "remote", "enabled": True},
        ]
    return jsonify({"destinations": destinations})


@bp.route("/scrape/config", methods=["POST"])
def save_scraping_config():
    """Persist scraping destinations configuration to JSON."""
    data = request.get_json()
    destinations = data.get("destinations")
    if not isinstance(destinations, list):
        return jsonify({"success": False, "message": "Field 'destinations' must be a list"}), 400
    try:
        save_scraping_destinations(destinations)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route("/scrape/status", methods=["GET"])
def get_scraping_status():
    """Get current scraping status."""
    return jsonify(state.SCRAPING_STATUS)


@bp.route("/update-status", methods=["POST"])
def start_update_status():
    """Launch job status update in a background thread."""
    print("--- Request received for /update-status ---")
    
    if state.UPDATE_STATUS_THREAD and state.UPDATE_STATUS_THREAD.is_alive():
        return jsonify({"success": False, "message": "Status update already in progress"}), 400
    
    # Reset status
    state.UPDATE_STATUS_STATUS = {"status": "running", "current": 0, "total": 0, "jobs_updated_count": 0, "error": None}
    
    def update_status_task():
        try:
            print("Starting job status update...")
            
            def progress_callback(current, total):
                state.UPDATE_STATUS_STATUS = {
                    "status": "running",
                    "current": current,
                    "total": total,
                    "jobs_updated_count": 0,
                    "error": None
                }
            
            jobs_updated_count = update_job_statuses(status_callback=progress_callback)
            final_total = state.UPDATE_STATUS_STATUS.get("total", 0)
            state.UPDATE_STATUS_STATUS = {
                "status": "completed",
                "current": final_total,
                "total": final_total,
                "jobs_updated_count": jobs_updated_count,
                "error": None
            }
            print(f"Status update completed. {jobs_updated_count} jobs updated to 'Closed'.")
        except Exception as e:
            print(f"Error during status update: {str(e)}")
            import traceback
            traceback.print_exc()
            state.UPDATE_STATUS_STATUS = {
                "status": "error",
                "current": state.UPDATE_STATUS_STATUS.get("current", 0),
                "total": state.UPDATE_STATUS_STATUS.get("total", 0),
                "jobs_updated_count": 0,
                "error": str(e)
            }
    
    state.UPDATE_STATUS_THREAD = threading.Thread(target=update_status_task)
    state.UPDATE_STATUS_THREAD.start()
    
    return jsonify({"success": True, "message": "Status update started"})


@bp.route("/update-status/status", methods=["GET"])
def get_update_status_status():
    """Get current update status status."""
    return jsonify(state.UPDATE_STATUS_STATUS)


@bp.route("/review", methods=["POST"])
def start_review():
    """Launch review in a background thread."""
    print("--- Request received for /review ---")
    data = request.get_json()
    count = data.get("count", 10)
    
    if state.REVIEW_STATUS.get("status") == "running":
        return jsonify({"success": False, "message": "Review already in progress"}), 400
    
    # Reset status
    state.REVIEW_STATUS = {"status": "running", "current": 0, "total": count, "error": None}
    
    def review_task():
        try:
            print(f"Starting review of {count} jobs")
            reviewer = JobReviewer()
            
            for i in range(count):
                job_review = reviewer.review_random_job("gpt-5-mini", with_correction=True, reasoning_level="low")
                if job_review is None:
                    # No more jobs to review
                    state.REVIEW_STATUS["total"] = i
                    break
                state.REVIEW_STATUS["current"] = i + 1
                print(f"Reviewed {i + 1}/{count} jobs")
            
            state.REVIEW_STATUS["status"] = "completed"
            print(f"Review completed. Reviewed {state.REVIEW_STATUS['current']} jobs.")
        except Exception as e:
            print(f"Error during review: {str(e)}")
            import traceback
            traceback.print_exc()
            state.REVIEW_STATUS = {
                "status": "error",
                "current": state.REVIEW_STATUS.get("current", 0),
                "total": count,
                "error": str(e)
            }
    
    state.REVIEW_THREAD = threading.Thread(target=review_task)
    state.REVIEW_THREAD.start()
    
    return jsonify({"success": True, "message": "Review started"})


@bp.route("/review/latest", methods=["POST"])
def start_review_latest():
    """Launch latest-first review in a background thread."""
    print("--- Request received for /review/latest ---")
    data = request.get_json()
    count = data.get("count", 10)

    if state.REVIEW_STATUS.get("status") == "running":
        return jsonify({"success": False, "message": "Review already in progress"}), 400

    state.REVIEW_STATUS = {"status": "running", "current": 0, "total": count, "error": None}
    state.REVIEW_THREAD = threading.Thread(target=run_review_latest_task, args=(count,))
    state.REVIEW_THREAD.start()

    return jsonify({"success": True, "message": "Latest-first review started"})

@bp.route("/review/status", methods=["GET"])
def get_review_status():
    """Get current review status."""
    return jsonify(state.REVIEW_STATUS)


@bp.route("/refresh-jobs", methods=["GET"])
def refresh_jobs():
    """Reload job data and return updated lists."""
    print("--- Request received for /refresh-jobs ---")
    
    try:
        # Reload data
        reviews = load_reviews()
        raw_jobs = load_raw_jobs()
        job_statuses = load_job_statuses()
        
        print(f"Reloaded {len(reviews)} reviews and {len(raw_jobs)} raw jobs.")
        
        reviews_map = {int(e["id"]): e for e in reviews}
        raw_jobs_map = {int(j["id"]): j for j in raw_jobs}
        job_statuses_map = {int(p["id"]): p for p in job_statuses}
        
        base_jobs = []
        job_ids = sorted(list(set(raw_jobs_map.keys()) & set(reviews_map.keys())))
        
        for job_id in job_ids:
            # Skip jobs whose raw status is Closed
            if raw_jobs_map.get(job_id, {}).get("status") == "Closed":
                continue
            job_data = {
                "id": job_id,
                **raw_jobs_map.get(job_id, {}),
                **reviews_map.get(job_id, {}),
            }
            base_jobs.append(job_data)
        
        # Sort by score descending
        base_jobs.sort(key=lambda x: x.get("score", -float("inf")), reverse=True)
        
        all_jobs = []
        for job in base_jobs:
            job_with_status = job.copy()
            job_with_status["status"] = job_statuses_map.get(job_with_status.get("id"))
            
            # Convert synthesis from Markdown to HTML
            if "synthesis_and_decision" in job_with_status and job_with_status["synthesis_and_decision"]:
                job_with_status["synthesis_and_decision"] = markdown.markdown(job_with_status["synthesis_and_decision"])
            
            all_jobs.append(job_with_status)
        
        unprocessed_jobs = [j for j in all_jobs if not j["status"]]
        
        # Calculate review count info
        # Total: all open jobs (not Closed) in raw_jobs
        total_open_count = len([j for j in raw_jobs if j.get("status") != "Closed"])
        # Unreviewed: open jobs that are NOT in reviews.json
        unreviewed_count = len([
            j for j in raw_jobs 
            if j.get("status") != "Closed" and j["id"] not in reviews_map
        ])
        percentage = (unreviewed_count / total_open_count * 100) if total_open_count > 0 else 0
        review_count_info = {
            "unreviewed_count": unreviewed_count,
            "total_open_count": total_open_count,
            "percentage": round(percentage, 1)
        }
        
        print(f"Returning {len(unprocessed_jobs)} unprocessed jobs.")
        
        return jsonify({
            "success": True,
            "jobs": all_jobs,
            "sidebar_jobs": unprocessed_jobs,
            "review_count_info": review_count_info
        })
    except Exception as e:
        print(f"Error refreshing jobs: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/review/manual", methods=["POST"])
def manual_review():
    """Review a job manually from a LinkedIn URL."""
    print("--- Request received for /review/manual ---")
    data = request.get_json()
    job_url = data.get("url", "").strip()
    
    if not job_url:
        return jsonify({"success": False, "message": "Missing 'url' field"}), 400
    
    # Nettoyer l'URL (retirer les paramètres de tracking)
    clean_url = job_url.split("?")[0] if "?" in job_url else job_url
    
    if not clean_url.startswith("https://www.linkedin.com/jobs/view/"):
        return jsonify({"success": False, "message": "Invalid LinkedIn job URL"}), 400
    
    try:
        # Vérifier si le job existe déjà dans raw_jobs
        raw_jobs = load_raw_jobs_manager()
        existing_job = None
        for job in raw_jobs:
            # Comparer avec l'URL nettoyée
            job_link = job.get("job_link", "")
            job_link_clean = job_link.split("?")[0] if "?" in job_link else job_link
            if job_link_clean == clean_url:
                existing_job = job
                break
        
        # Si le job n'existe pas, l'ajouter
        if not existing_job:
            print(f"Job not found in raw_jobs, adding it...")
            # Extraire les détails complets du job
            job_details = extract_full_job_details(clean_url)
            
            if not job_details:
                return jsonify({"success": False, "message": "Failed to extract job details from URL"}), 400
            
            # Créer les données du job pour l'ajout
            new_job_data = {
                "title": job_details.get("title", "Unknown"),
                "company": job_details.get("company", "Unknown"),
                "location": "Unknown",  # On ne peut pas extraire la location depuis la page individuelle facilement
                "job_link": clean_url,
                "posted_date": "N/A",  # On ne peut pas extraire la date depuis la page individuelle facilement
            }
            
            # Utiliser add_new_job mais avec les détails déjà extraits
            # Pour éviter de refaire l'extraction, on va ajouter manuellement
            jobs = load_raw_jobs_manager()
            
            # Vérifier les doublons basés sur 'job_link' (nettoyé)
            if any(
                (job.get("job_link", "").split("?")[0] if "?" in job.get("job_link", "") else job.get("job_link", "")) == clean_url
                for job in jobs
            ):
                return jsonify({"success": False, "message": "Job already exists"}), 400
            
            # Ajouter status et workplace_type depuis job_details
            new_job_data["status"] = job_details.get("status", "Unknown")
            new_job_data["workplace_type"] = job_details.get("workplace_type", "Not found")
            
            # Convertir la date de publication
            from jobseeker_agent.scraper.date_parser import parse_relative_date
            new_job_data["posted_date"] = parse_relative_date(new_job_data.get("posted_date", ""))
            
            # Déterminer le nouvel ID
            if jobs:
                new_id = jobs[-1].get("id", -1) + 1
            else:
                new_id = 1
            
            # Ajouter le nouvel emploi
            new_job = {"id": new_id, **new_job_data}
            jobs.append(new_job)
            save_raw_jobs(jobs)
            
            existing_job = new_job
            print(f"Job {existing_job['id']} added successfully.")
        else:
            print(f"Job {existing_job['id']} already exists in raw_jobs.")
        
        # Maintenant, faire le review
        print(f"Reviewing job {existing_job['id']}...")
        
        # Récupérer les détails à jour pour le review
        job_details = extract_full_job_details(existing_job["job_link"])
        if not job_details:
            return jsonify({"success": False, "message": "Failed to retrieve job details for review"}), 400
        
        # Faire le review directement
        review = review_agent(existing_job, job_details, "gpt-4.1", with_correction=True)
        
        # Sauvegarder le review
        reviews = load_reviews()
        reviews.append(review)
        save_reviews(reviews)
        
        # Marquer comme traité
        processed_jobs = set(load_processed_jobs())
        processed_jobs.add(existing_job["id"])
        save_processed_jobs(list(processed_jobs))
        
        print(f"Review completed for job {existing_job['id']}.")
        
        return jsonify({
            "success": True,
            "message": f"Job reviewed successfully",
            "job_id": existing_job["id"],
            "review": review
        })
        
    except Exception as e:
        print(f"Error during manual review: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

