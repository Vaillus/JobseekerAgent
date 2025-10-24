import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from jobseeker_agent.utils.paths import get_raw_jobs_json_path
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.scraper.date_parser import parse_relative_date


def load_raw_jobs() -> List[Dict[str, Any]]:
    """Charge les offres d'emploi brutes depuis le fichier JSON.

    Returns:
        List[Dict[str, Any]]: La liste des offres d'emploi.
    """
    raw_jobs_path = get_raw_jobs_json_path()
    if not raw_jobs_path.exists():
        return []
    with open(raw_jobs_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_raw_jobs(jobs: List[Dict[str, Any]]) -> None:
    """Sauvegarde la liste des offres d'emploi dans le fichier JSON.

    Args:
        jobs (List[Dict[str, Any]]): La liste des offres d'emploi à sauvegarder.
    """
    raw_jobs_path = get_raw_jobs_json_path()
    with open(raw_jobs_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=4, ensure_ascii=False)


def add_new_job(job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ajoute une nouvelle offre d'emploi si elle n'existe pas déjà.

    L'offre est identifiée par son URL pour éviter les doublons.
    Un identifiant unique est ajouté à l'offre.

    Args:
        job_data (Dict[str, Any]): Les données de l'offre d'emploi.

    Returns:
        Optional[Dict[str, Any]]: L'offre d'emploi ajoutée avec son ID, ou None si l'offre existait déjà.
    """
    jobs = load_raw_jobs()
    
    # Vérifier les doublons basés sur 'job_link'
    if any(job.get("job_link") == job_data.get("job_link") for job in jobs):
        return None
    
    # Enrichir les données de l'offre
    analysis_results = extract_job_details(job_data.get("job_link", ""))
    if analysis_results:
        job_data["status"] = analysis_results.get("status", "Unknown")
        job_data["workplace_type"] = analysis_results.get("workplace_type", "Not found")
    else:
        job_data["status"] = "Analysis Failed"
        job_data["workplace_type"] = "Analysis Failed"

    # Convertir la date de publication
    job_data["posted_date"] = parse_relative_date(job_data.get("posted_date", ""))

    # Déterminer le nouvel ID
    if jobs:
        new_id = jobs[-1].get("id", -1) + 1
    else:
        new_id = 1
    
    # Ajouter le nouvel emploi
    new_job = {"id": new_id, **job_data}
    jobs.append(new_job)
    
    save_raw_jobs(jobs)
    
    return new_job
