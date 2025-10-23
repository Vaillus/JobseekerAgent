from pathlib import Path
import json

from typing import List, Dict, Any

def get_project_root() -> Path:
    """Retourne la racine du projet."""
    return Path(__file__).resolve().parent.parent

def get_data_path() -> Path:
    """Retourne le chemin vers les données."""
    return get_project_root() / "data"


def load_cv_template(lang: str = "en") -> str:
    """Loads the CV template from the file."""
    if lang not in ["en", "fr"]:
        raise ValueError("Language not supported, please choose 'en' or 'fr'")
    cv_path = get_data_path() / "resume" / "template" / f"cv-{lang}.tex"
    with open(cv_path, "r") as f:
        return f.read()


def get_evaluator_path() -> Path:
    """Retourne le chemin vers le dossier evaluator."""
    evaluator_dir = get_data_path() / "evaluator"
    evaluator_dir.mkdir(parents=True, exist_ok=True)
    return evaluator_dir

def get_linkedin_keywords_path() -> Path:
    """Retourne le chemin vers les keywords de LinkedIn."""
    return get_data_path() / "linkedin_keywords"


def get_raw_jobs_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des jobs bruts."""
    raw_jobs_dir = get_data_path() / "raw_jobs"
    raw_jobs_dir.mkdir(parents=True, exist_ok=True)
    return raw_jobs_dir / "raw_jobs.json"

def get_main_evals_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des evaluations."""
    return get_evaluator_path() / "evals.json"

def get_job_statuses_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des statuts des jobs."""
    return get_evaluator_path() / "job_statuses.json"

def get_processed_jobs_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des jobs traités."""
    return get_evaluator_path() / "processed_jobs.json"

def get_evaluator_labels_path(generation_id: int) -> Path:
    """Retourne le chemin vers le fichier JSON des labels."""
    labels_dir = get_data_path() / "evaluator" / "tests" / str(generation_id)
    labels_dir.mkdir(parents=True, exist_ok=True)
    return labels_dir / "labels.json"

def get_evaluator_evals_json_path(generation_id: int) -> Path:
    """Retourne le chemin vers le fichier JSON des evaluations."""
    evals_dir = get_data_path() / "evaluator" / "tests" / str(generation_id)
    evals_dir.mkdir(parents=True, exist_ok=True)
    return evals_dir / "evals.json"

def get_ranking_report_path(job_id: int) -> Path:
    """Retourne le chemin vers le rapport de ranking."""
    ranking_dir = get_data_path() / "resume" / str(job_id)
    ranking_dir.mkdir(parents=True, exist_ok=True)
    return ranking_dir / "ranking_report.json"


def get_opening_lines_path(job_id: int) -> Path:
    """Retourne le chemin vers le fichier des phrases d'accroche."""
    opening_lines_dir = get_data_path() / "resume" / str(job_id)
    opening_lines_dir.mkdir(parents=True, exist_ok=True)
    return opening_lines_dir / "opening_lines.json"


def load_prompt(prompt_name: str) -> str:
    """Charge le prompt depuis le fichier."""
    prompt_path = get_data_path() / "prompts" / f"{prompt_name}.md"
    with open(prompt_path, "r") as f:
        return f.read()

def load_raw_jobs() -> List[Dict[str, Any]]:
    """Charge les jobs bruts depuis le fichier JSON."""
    raw_jobs_path = get_raw_jobs_json_path()
    if not raw_jobs_path.exists():
        return []

    with open(raw_jobs_path, "r") as f:
        return json.load(f)

def load_raw_job(job_id: int) -> Dict[str, Any]:
    """Charge le job brut depuis le fichier JSON."""
    raw_jobs = load_raw_jobs()
    job = next((j for j in raw_jobs if j["id"] == job_id), None)
    if not job:
        raise ValueError(f"Job with ID {job_id} not found")
    return job

def load_labels(generation_id: int) -> List[Dict[str, Any]]:
    """Charge les labels depuis le fichier JSON."""
    labels_path = get_evaluator_labels_path(generation_id)
    if not labels_path.exists():
        return []
    
    with open(labels_path, "r") as f:
        return json.load(f)

def save_labels(labels: List[Dict[str, Any]], generation_id: int) -> None:
    """Sauvegarde les labels dans le fichier JSON."""
    labels_path = get_evaluator_labels_path(generation_id)
    with open(labels_path, "w") as f:
        json.dump(labels, f, indent=4)


def load_evals(generation_id: int) -> List[Dict[str, Any]]:
    """Charge les evals depuis le fichier JSON."""
    evals_path = get_evaluator_evals_json_path(generation_id)
    if not evals_path.exists():
        return []

    with open(evals_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_evals(evals: List[Dict[str, Any]], generation_id: int) -> None:
    """Sauvegarde les evals dans le fichier JSON."""
    evals_path = get_evaluator_evals_json_path(generation_id)
    with open(evals_path, "w") as f:
        json.dump(evals, f, indent=4)


def load_main_evals() -> List[Dict[str, Any]]:
    """Charge les evals depuis le fichier JSON principal."""
    evals_path = get_main_evals_json_path()
    if not evals_path.exists():
        return []

    with open(evals_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_main_evals(evals: List[Dict[str, Any]]) -> None:
    """Sauvegarde les evals dans le fichier JSON principal."""
    evals_path = get_main_evals_json_path()
    with open(evals_path, "w") as f:
        json.dump(evals, f, indent=4)


def load_job_statuses() -> List[Dict[str, Any]]:
    """Charge les statuts des jobs depuis le fichier JSON."""
    statuses_path = get_job_statuses_json_path()
    if not statuses_path.exists():
        return []
    with open(statuses_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_job_statuses(statuses: List[Dict[str, Any]]) -> None:
    """Sauvegarde les statuts des jobs dans le fichier JSON."""
    statuses_path = get_job_statuses_json_path()
    with open(statuses_path, "w") as f:
        json.dump(statuses, f, indent=4)


def load_processed_jobs() -> List[int]:
    """Charge les IDs des jobs traités depuis le fichier JSON."""
    processed_jobs_path = get_processed_jobs_json_path()
    if not processed_jobs_path.exists():
        return []

    with open(processed_jobs_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_processed_jobs(processed_jobs: List[int]) -> None:
    """Sauvegarde les IDs des jobs traités dans le fichier JSON."""
    processed_jobs_path = get_processed_jobs_json_path()
    with open(processed_jobs_path, "w") as f:
        json.dump(processed_jobs, f, indent=4)


if __name__ == "__main__":
    print(get_linkedin_keywords_path())