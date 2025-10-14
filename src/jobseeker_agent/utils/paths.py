from pathlib import Path

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


if __name__ == "__main__":
    print(get_linkedin_keywords_path())