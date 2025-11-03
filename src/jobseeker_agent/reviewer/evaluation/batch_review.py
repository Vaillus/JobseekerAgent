"""
Script pour exécuter des reviews en batch sur plusieurs jobs avec différentes configurations LLM.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from jobseeker_agent.scraper.job_manager import load_raw_jobs
from jobseeker_agent.scraper.extract_job_details import extract_job_details
from jobseeker_agent.reviewer.agents.reviewer import review
from jobseeker_agent.utils.paths import get_data_path


def get_batch_results_path(generation_id: int) -> Path:
    """Retourne le chemin vers le fichier JSON des résultats de batch."""
    batch_dir = get_data_path() / "reviewer" / "tests" / str(generation_id)
    batch_dir.mkdir(parents=True, exist_ok=True)
    return batch_dir / "batch_results.json"


def load_batch_results(generation_id: int) -> List[Dict[str, Any]]:
    """Charge les résultats de batch depuis le fichier JSON.
    
    Returns:
        Liste plate de reviews, chaque élément contient job_id, config_name, etc.
    """
    batch_path = get_batch_results_path(generation_id)
    if not batch_path.exists():
        return []
    
    with open(batch_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            # Si c'est l'ancien format (dict avec "jobs"), convertir
            if isinstance(data, dict) and "jobs" in data:
                # Convertir l'ancien format vers le nouveau
                reviews = []
                for job_data in data.get("jobs", []):
                    job_id = job_data.get("job_id")
                    for config_name, config_result in job_data.get("configs", {}).items():
                        review_entry = {
                            "job_id": job_id,
                            "config_name": config_name,
                            **config_result
                        }
                        reviews.append(review_entry)
                return reviews
            # Sinon, c'est déjà une liste
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


def save_batch_results(reviews: List[Dict[str, Any]], generation_id: int) -> None:
    """Sauvegarde les résultats de batch dans le fichier JSON.
    
    Args:
        reviews: Liste plate de reviews à sauvegarder
        generation_id: ID de génération pour déterminer le chemin
    """
    batch_path = get_batch_results_path(generation_id)
    with open(batch_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=4, ensure_ascii=False)


def run_batch_review(
    job_ids: List[int],
    configs: List[Dict[str, Any]],
    generation_id: int,
    skip_existing: bool = True
) -> List[Dict[str, Any]]:
    """
    Exécute des reviews en batch sur plusieurs jobs avec différentes configurations LLM.
    
    Args:
        job_ids: Liste des IDs de jobs à reviewer
        configs: Liste de configurations, chaque config doit contenir:
            - "name": nom de la configuration (ex: "gpt-4.1_corrected")
            - "model": nom du modèle LLM
            - "with_correction": booléen pour activer/désactiver la correction
            - "reasoning_level": niveau de raisonnement (optionnel)
        generation_id: ID de génération pour organiser les résultats
        skip_existing: Si True, skip les combinaisons job/config déjà traitées
    
    Returns:
        Liste plate de reviews, chaque élément contient:
        - job_id: int
        - config_name: str
        - model: str
        - with_correction: bool
        - reasoning_level: Optional[str]
        - review_result: Dict (evaluation_grid, score, id)
        - metadata: Dict (tokens, cost, execution_time, etc.)
        - error: Optional[str] (si erreur)
    """
    # Charger les résultats existants
    reviews = load_batch_results(generation_id)
    
    # Créer un set des combinaisons déjà traitées
    processed_combinations = set()
    if skip_existing:
        for review_entry in reviews:
            job_id = review_entry.get("job_id")
            config_name = review_entry.get("config_name")
            if job_id and config_name:
                processed_combinations.add((job_id, config_name))
    
    # Charger tous les jobs
    all_jobs = load_raw_jobs()
    jobs_map = {job["id"]: job for job in all_jobs}
    
    # Dict pour stocker les détails de job déjà extraits (évite de réextraire)
    job_details_cache = {}
    
    # Traiter chaque combinaison job/config
    for job_id in job_ids:
        if job_id not in jobs_map:
            print(f"⚠️ Job ID {job_id} not found in raw_jobs. Skipping.")
            continue
        
        job = jobs_map[job_id]
        
        # Extraire les détails du job une seule fois (mise en cache)
        if job_id not in job_details_cache:
            print(f"📋 Extracting details for job {job_id}...")
            job_details = extract_job_details(job["job_link"])
            
            if not job_details or not job_details.get("description"):
                print(f"⚠️ Could not extract details for job {job_id}. Skipping.")
                continue
            
            job_details_cache[job_id] = job_details
        else:
            job_details = job_details_cache[job_id]
        
        # Traiter chaque configuration
        for config in configs:
            config_name = config["name"]
            
            # Vérifier si déjà traité
            if skip_existing and (job_id, config_name) in processed_combinations:
                print(f"⏭️  Job {job_id} with config '{config_name}' already processed. Skipping.")
                continue
            
            print(f"\n🔄 Processing job {job_id} with config '{config_name}'...")
            print(f"   Model: {config['model']}, Correction: {config.get('with_correction', True)}")
            
            try:
                # Exécuter la review
                review_result = review(
                    job=job,
                    job_details=job_details,
                    model=config["model"],
                    with_correction=config.get("with_correction", True),
                    reasoning_level=config.get("reasoning_level")
                )
                
                # Extraire les métadonnées et le résultat de review
                metadata = review_result.pop("metadata", {})
                
                # Créer l'entrée de review
                review_entry = {
                    "job_id": job_id,
                    "config_name": config_name,
                    "model": config["model"],
                    "with_correction": config.get("with_correction", True),
                    "reasoning_level": config.get("reasoning_level"),
                    "review_result": review_result,  # evaluation_grid, score, id
                    "metadata": metadata  # input_tokens, output_tokens, total_tokens, total_cost, execution_time, etc.
                }
                
                # Ajouter à la liste
                reviews.append(review_entry)
                
                # Sauvegarder de manière incrémentale
                save_batch_results(reviews, generation_id)
                
                print(f"   ✅ Completed - Cost: ${metadata.get('total_cost', 0):.4f}, "
                      f"Time: {metadata.get('execution_time', 0):.2f}s, "
                      f"Tokens: {metadata.get('total_tokens', 0)}")
                
            except Exception as e:
                print(f"   ❌ Error processing job {job_id} with config '{config_name}': {e}")
                # Stocker l'erreur dans les résultats
                review_entry = {
                    "job_id": job_id,
                    "config_name": config_name,
                    "model": config["model"],
                    "with_correction": config.get("with_correction", True),
                    "reasoning_level": config.get("reasoning_level"),
                    "error": str(e),
                    "review_result": None,
                    "metadata": None
                }
                reviews.append(review_entry)
                save_batch_results(reviews, generation_id)
    
    return reviews


if __name__ == "__main__":
    # Exemple d'utilisation
    job_ids = [18]  # À remplacer par vos 10 job IDs
    configs = [
        {
            "name": "gpt-4.1_corrected",
            "model": "gpt-4.1",
            "with_correction": True,
            "reasoning_level": None
        },
        {
            "name": "gpt-4.1_basic",
            "model": "gpt-4.1",
            "with_correction": False,
            "reasoning_level": None
        }
    ]
    generation_id = 6  # À ajuster selon votre numérotation
    
    reviews = run_batch_review(job_ids, configs, generation_id)
    print(f"\n✅ Batch review completed. {len(reviews)} reviews saved to generation {generation_id}")

