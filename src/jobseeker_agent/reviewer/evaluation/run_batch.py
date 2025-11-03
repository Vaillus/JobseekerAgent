"""
Script principal pour lancer le batch processing de reviews LLM.
Définit les jobs à tester et les configurations LLM, puis lance le batch processing.
"""

from jobseeker_agent.reviewer.evaluation.batch_review import run_batch_review
from jobseeker_agent.scraper.job_manager import load_raw_jobs


def main():
    """Lance le batch processing avec les jobs et configurations définis."""
    
    # Charger les jobs et prendre les 10 derniers
    all_jobs = load_raw_jobs()
    if len(all_jobs) < 10:
        print(f"⚠️  Seulement {len(all_jobs)} jobs disponibles. Il en faut au moins 10.")
        return
    
    # Prendre les 10 derniers job IDs
    job_ids = [ 883, 911, 920, 929, 937, 938]
    print(f"📋 Using last 10 job IDs: {job_ids}")
    print()
    
    # Définir les configurations LLM à tester
    # Focus sur OpenAI: gpt-4.1, gpt-5-mini, gpt-5-main
    # Sans reasoning et sans correction
    configs = [
        {
            "name": "gpt-4.1_normal",
            "model": "gpt-4.1",
            "with_correction": False,
            "reasoning_level": None
        },
        {
            "name": "gpt-4.1_corrected",
            "model": "gpt-4.1",
            "with_correction": True,
            "reasoning_level": None
        },
        {
            "name": "gpt-5-mini_low",
            "model": "gpt-5-mini",
            "with_correction": False,
            "reasoning_level": "low"
        },
        {
            "name": "gpt-5-mini_normal",
            "model": "gpt-5-mini",
            "with_correction": False,
            "reasoning_level": None
        },
        {
            "name": "gpt-5-mini_low_corrected",
            "model": "gpt-5-mini",
            "with_correction": True,
            "reasoning_level": "low"
        },
        {
            "name": "gpt-5-mini_normal_corrected",
            "model": "gpt-5-mini",
            "with_correction": True,
            "reasoning_level": None
        },
        # {
        #     "name": "gpt-5_normal",
        #     "model": "gpt-5",
        #     "with_correction": False,
        #     "reasoning_level": None
        # },
        {
            "name": "gpt-5_low",
            "model": "gpt-5",
            "with_correction": False,
            "reasoning_level": "low"
        },
        {
            "name": "gpt-5_low_corrected",
            "model": "gpt-5",
            "with_correction": True,
            "reasoning_level": "low"
        },
    ]
    
    # Définir le generation_id
    # Générer automatiquement ou demander à l'utilisateur
    generation_id = 6  # À ajuster selon votre numérotation
    
    print("=" * 60)
    print("🚀 Starting Batch Review Processing")
    print("=" * 60)
    print(f"📊 Generation ID: {generation_id}")
    print(f"📋 Jobs to process: {len(job_ids)}")
    print(f"⚙️  Configurations: {len(configs)}")
    print(f"   Total reviews to execute: {len(job_ids) * len(configs)}")
    print("=" * 60)
    print()
    
    # Lancer le batch processing
    results = run_batch_review(
        job_ids=job_ids,
        configs=configs,
        generation_id=generation_id,
        skip_existing=True  # Skip les combinaisons déjà traitées
    )
    
    # Calculer les statistiques
    total_cost = 0.0
    total_time = 0.0
    successful_reviews = 0
    failed_reviews = 0
    
    for review_entry in results:
        if review_entry.get("error"):
            failed_reviews += 1
        else:
            successful_reviews += 1
            metadata = review_entry.get("metadata", {})
            total_cost += metadata.get("total_cost", 0.0)
            total_time += metadata.get("execution_time", 0.0)
    
    # Afficher le résumé
    print()
    print("=" * 60)
    print("📊 Batch Review Summary")
    print("=" * 60)
    print(f"✅ Successful reviews: {successful_reviews}")
    print(f"❌ Failed reviews: {failed_reviews}")
    print(f"💰 Total cost: ${total_cost:.4f}")
    print(f"⏱️  Total execution time: {total_time:.2f}s")
    if successful_reviews > 0:
        print(f"💰 Average cost per review: ${total_cost / successful_reviews:.4f}")
        print(f"⏱️  Average time per review: {total_time / successful_reviews:.2f}s")
    print("=" * 60)
    print(f"💾 Results saved to: data/reviewer/tests/{generation_id}/batch_results.json")
    print()


if __name__ == "__main__":
    main()

