from pathlib import Path
import json
import inspect

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


def load_cover_letter_template(lang: str = "en") -> str:
    """Loads the cover letter template from the file."""
    if lang not in ["en", "fr"]:
        raise ValueError("Language not supported, please choose 'en' or 'fr'")
    cover_letter_path = get_data_path() / "resume" / "template" / f"cover-letter-{lang}.md"
    with open(cover_letter_path, "r") as f:
        return f.read()


def get_reviewer_data_dir() -> Path:
    """Retourne le chemin vers le dossier reviewer."""
    reviewer_dir = get_data_path() / "reviewer"
    reviewer_dir.mkdir(parents=True, exist_ok=True)
    return reviewer_dir

def get_linkedin_keywords_path() -> Path:
    """Retourne le chemin vers les keywords de LinkedIn."""
    return get_data_path() / "linkedin_keywords"


def get_raw_jobs_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des jobs bruts."""
    raw_jobs_dir = get_data_path() / "raw_jobs"
    raw_jobs_dir.mkdir(parents=True, exist_ok=True)
    return raw_jobs_dir / "raw_jobs.json"

def get_reviews_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des reviews."""
    return get_reviewer_data_dir() / "reviews.json"

def get_job_statuses_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des statuts des jobs."""
    return get_reviewer_data_dir() / "job_statuses.json"

def get_processed_jobs_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des jobs traités."""
    return get_reviewer_data_dir() / "processed_jobs.json"

def get_reviewer_labels_path(generation_id: int) -> Path:
    """Retourne le chemin vers le fichier JSON des labels."""
    labels_dir = get_data_path() / "reviewer" / "tests" / str(generation_id)
    labels_dir.mkdir(parents=True, exist_ok=True)
    return labels_dir / "labels.json"

def get_test_reviews_json_path(generation_id: int) -> Path:
    """Retourne le chemin vers le fichier JSON des reviews."""
    reviews_dir = get_data_path() / "reviewer" / "tests" / str(generation_id)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    return reviews_dir / "evals.json"

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
    """
    Charge un prompt. Priorise un .md local au script appelant, sinon cherche dans data/prompts.
    """
    # First check if a local prompt exists in the folder of the script 
    # calling this function. The prompt must be named like the script but 
    # with a .md extension.
    caller_frame = inspect.stack()[1]
    caller_path = Path(caller_frame.filename).resolve()
    local_prompt_path = caller_path.with_suffix(".md")
    if local_prompt_path.exists():
        with open(local_prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    # If no local prompt exists, search in data/prompts.
    prompt_path = get_data_path() / "prompts" / f"{prompt_name}.md"
    # If the prompt is not found, raise an error.
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt {prompt_name} not found in {local_prompt_path} or data/prompts.")
    # If the prompt is found, return it.
    with open(prompt_path, "r", encoding="utf-8") as f:
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
    labels_path = get_reviewer_labels_path(generation_id)
    if not labels_path.exists():
        return []
    
    with open(labels_path, "r") as f:
        return json.load(f)

def save_labels(labels: List[Dict[str, Any]], generation_id: int) -> None:
    """Sauvegarde les labels dans le fichier JSON."""
    labels_path = get_reviewer_labels_path(generation_id)
    with open(labels_path, "w") as f:
        json.dump(labels, f, indent=4)


def load_test_reviews(generation_id: int) -> List[Dict[str, Any]]:
    """Charge les reviews depuis le fichier JSON."""
    reviews_path = get_test_reviews_json_path(generation_id)
    if not reviews_path.exists():
        return []
    with open(reviews_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_test_reviews(reviews: List[Dict[str, Any]], generation_id: int) -> None:
    """Sauvegarde les reviews dans le fichier JSON."""
    reviews_path = get_test_reviews_json_path(generation_id)
    with open(reviews_path, "w") as f:
        json.dump(reviews, f, indent=4)


def load_reviews() -> List[Dict[str, Any]]:
    """Charge les reviews depuis le fichier JSON principal."""
    reviews_path = get_reviews_json_path()
    if not reviews_path.exists():
        return []
    with open(reviews_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def load_review(job_id: int) -> Dict[str, Any]:
    """Charge la review depuis le fichier JSON principal."""
    reviews = load_reviews()
    review = next((r for r in reviews if r["id"] == job_id), None)
    if not review:
        raise ValueError(f"Review with ID {job_id} not found")
    return review

def save_reviews(reviews: List[Dict[str, Any]]) -> None:
    """Sauvegarde les reviews dans le fichier JSON principal."""
    reviews_path = get_reviews_json_path()
    with open(reviews_path, "w") as f:
        json.dump(reviews, f, indent=4)


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