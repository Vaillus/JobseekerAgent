from pathlib import Path
import json

from typing import List, Dict, Any

def get_project_root() -> Path:
    """Retourne la racine du projet."""
    return Path(__file__).resolve().parent.parent

def get_data_path() -> Path:
    """Retourne le chemin vers les données."""
    return get_project_root() / "data"

def get_linkedin_keywords_path() -> Path:
    """Retourne le chemin vers les keywords de LinkedIn."""
    return get_data_path() / "linkedin_keywords"


def get_raw_jobs_json_path() -> Path:
    """Retourne le chemin vers le fichier JSON des jobs bruts."""
    raw_jobs_dir = get_data_path() / "raw_jobs"
    raw_jobs_dir.mkdir(parents=True, exist_ok=True)
    return raw_jobs_dir / "raw_jobs.json"

def get_evaluator_labels_path() -> Path:
    """Retourne le chemin vers le fichier JSON des labels."""
    labels_dir = get_data_path() / "evaluator_labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    return labels_dir / "label.json"

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

def load_labels() -> List[Dict[str, Any]]:
    """Charge les labels depuis le fichier JSON."""
    labels_path = get_evaluator_labels_path()
    if not labels_path.exists():
        return []
    
    with open(labels_path, "r") as f:
        return json.load(f)

def save_labels(labels: List[Dict[str, Any]]) -> None:
    """Sauvegarde les labels dans le fichier JSON."""
    labels_path = get_evaluator_labels_path()
    with open(labels_path, "w") as f:
        json.dump(labels, f, indent=4)

if __name__ == "__main__":
    print(get_linkedin_keywords_path())