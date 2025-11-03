"""
Script d'analyse des performances des LLMs sur la tâche de review.
Compare les détections des modèles avec la ground truth.
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from sklearn.metrics import precision_score, recall_score, f1_score
import numpy as np

from jobseeker_agent.reviewer.evaluation.batch_review import load_batch_results
from jobseeker_agent.utils.paths import get_data_path


def load_ground_truth(generation_id: int) -> Dict[int, Set[int]]:
    """
    Charge la ground truth.
    
    Returns:
        Dict[job_id] = Set de criterion_ids validés
    """
    gt_path = get_data_path() / "reviewer" / "tests" / str(generation_id) / "ground_truth.json"
    
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth not found: {gt_path}")
    
    with open(gt_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)
    
    # Convertir en dict[job_id] = set(criterion_ids)
    ground_truth = {}
    for entry in gt_data:
        job_id = entry['job_id']
        validated_criteria = set(entry['validated_criteria'])
        ground_truth[job_id] = validated_criteria
    
    return ground_truth


def compute_metrics_per_model(
    reviews: List[Dict],
    ground_truth: Dict[int, Set[int]],
    all_criteria_ids: Set[int]
) -> Dict[str, Dict]:
    """
    Calcule les métriques pour chaque modèle.
    
    Returns:
        Dict[config_name] = {
            'precision': float,
            'recall': float,
            'f1': float,
            'avg_cost': float,
            'avg_time': float,
            'total_jobs': int
        }
    """
    # Grouper les reviews par config
    reviews_by_config = defaultdict(list)
    for review in reviews:
        config_name = review['config_name']
        reviews_by_config[config_name].append(review)
    
    metrics_by_model = {}
    
    for config_name, config_reviews in reviews_by_config.items():
        # Préparer les données pour sklearn
        y_true_all = []
        y_pred_all = []
        costs = []
        times = []
        
        for review in config_reviews:
            job_id = review['job_id']
            
            # Ground truth pour ce job
            gt_criteria = ground_truth.get(job_id, set())
            
            # Prédictions du modèle
            detected_criteria = set()
            review_result = review.get('review_result', {})
            if review_result and 'evaluation_grid' in review_result:
                for criterion in review_result['evaluation_grid']:
                    detected_criteria.add(criterion['id'])
            
            # Convertir en vecteurs binaires (un élément par critère)
            for criterion_id in all_criteria_ids:
                y_true_all.append(1 if criterion_id in gt_criteria else 0)
                y_pred_all.append(1 if criterion_id in detected_criteria else 0)
            
            # Métriques de coût et temps
            metadata = review.get('metadata', {})
            costs.append(metadata.get('total_cost', 0))
            times.append(metadata.get('execution_time', 0))
        
        # Calculer les métriques agrégées
        y_true_arr = np.array(y_true_all)
        y_pred_arr = np.array(y_pred_all)
        
        # Si aucun positif dans y_true, les métriques ne sont pas définies
        # On utilise zero_division=0 pour gérer ce cas
        precision = precision_score(y_true_arr, y_pred_arr, zero_division=0)
        recall = recall_score(y_true_arr, y_pred_arr, zero_division=0)
        f1 = f1_score(y_true_arr, y_pred_arr, zero_division=0)
        
        metrics_by_model[config_name] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'avg_cost': np.mean(costs) if costs else 0,
            'avg_time': np.mean(times) if times else 0,
            'total_jobs': len(config_reviews)
        }
    
    return metrics_by_model


def print_metrics_table(metrics: Dict[str, Dict]):
    """Affiche un tableau formaté des métriques."""
    
    print("\n" + "=" * 100)
    print("📊 MÉTRIQUES AGRÉGÉES PAR MODÈLE")
    print("=" * 100)
    print()
    
    # Header
    header = f"{'Model':<20} {'F1-Score':>10} {'Précision':>10} {'Rappel':>10} {'Coût ($)':>12} {'Temps (s)':>12} {'Jobs':>8}"
    print(header)
    print("-" * 100)
    
    # Trier par F1-score décroissant
    sorted_models = sorted(metrics.items(), key=lambda x: x[1]['f1'], reverse=True)
    
    for config_name, m in sorted_models:
        row = (
            f"{config_name:<20} "
            f"{m['f1']:>10.4f} "
            f"{m['precision']:>10.4f} "
            f"{m['recall']:>10.4f} "
            f"${m['avg_cost']:>11.5f} "
            f"{m['avg_time']:>12.2f} "
            f"{m['total_jobs']:>8d}"
        )
        print(row)
    
    print("=" * 100)
    print()


def compute_detailed_errors(
    reviews: List[Dict],
    ground_truth: Dict[int, Set[int]]
) -> Dict[str, Dict]:
    """
    Calcule les erreurs détaillées par modèle.
    
    Returns:
        Dict[config_name] = {
            'false_positives': List[(job_id, criterion_id)],
            'false_negatives': List[(job_id, criterion_id)],
            'true_positives': int,
            'true_negatives': int
        }
    """
    errors_by_model = defaultdict(lambda: {
        'false_positives': [],
        'false_negatives': [],
        'true_positives': 0,
        'true_negatives': 0
    })
    
    for review in reviews:
        config_name = review['config_name']
        job_id = review['job_id']
        
        # Ground truth
        gt_criteria = ground_truth.get(job_id, set())
        
        # Prédictions
        detected_criteria = set()
        review_result = review.get('review_result', {})
        if review_result and 'evaluation_grid' in review_result:
            for criterion in review_result['evaluation_grid']:
                detected_criteria.add(criterion['id'])
        
        # Analyser les erreurs
        false_positives = detected_criteria - gt_criteria
        false_negatives = gt_criteria - detected_criteria
        true_positives = len(detected_criteria & gt_criteria)
        
        for fp in false_positives:
            errors_by_model[config_name]['false_positives'].append((job_id, fp))
        
        for fn in false_negatives:
            errors_by_model[config_name]['false_negatives'].append((job_id, fn))
        
        errors_by_model[config_name]['true_positives'] += true_positives
    
    return dict(errors_by_model)


def print_error_summary(errors: Dict[str, Dict]):
    """Affiche un résumé des erreurs par modèle."""
    
    print("\n" + "=" * 80)
    print("🔍 RÉSUMÉ DES ERREURS PAR MODÈLE")
    print("=" * 80)
    print()
    
    for config_name, error_data in errors.items():
        fp_count = len(error_data['false_positives'])
        fn_count = len(error_data['false_negatives'])
        tp_count = error_data['true_positives']
        
        print(f"📌 {config_name}")
        print(f"   ✅ Vrais positifs:  {tp_count}")
        print(f"   ❌ Faux positifs:   {fp_count}")
        print(f"   ⚠️  Faux négatifs:  {fn_count}")
        print()


def save_detailed_results(
    generation_id: int,
    metrics: Dict[str, Dict],
    errors: Dict[str, Dict]
):
    """Sauvegarde les résultats détaillés en JSON."""
    
    output_path = get_data_path() / "reviewer" / "tests" / str(generation_id) / "performance_metrics.json"
    
    results = {
        'metrics': metrics,
        'errors': {
            config: {
                'false_positives': [{'job_id': jid, 'criterion_id': cid} for jid, cid in data['false_positives']],
                'false_negatives': [{'job_id': jid, 'criterion_id': cid} for jid, cid in data['false_negatives']],
                'true_positives': data['true_positives']
            }
            for config, data in errors.items()
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Résultats détaillés sauvegardés: {output_path}")
    print()


def analyze_generation(generation_id: int):
    """Analyse complète d'une génération."""
    
    print("\n" + "=" * 80)
    print(f"🔬 ANALYSE DES PERFORMANCES - Generation {generation_id}")
    print("=" * 80)
    print()
    
    # Charger les données
    print("📥 Chargement des données...")
    reviews = load_batch_results(generation_id)
    ground_truth = load_ground_truth(generation_id)
    
    # Tous les critères possibles (1-24)
    all_criteria_ids = set(range(1, 25))
    
    print(f"   ✅ {len(reviews)} reviews chargées")
    print(f"   ✅ {len(ground_truth)} jobs avec ground truth")
    print()
    
    # Calculer les métriques
    print("📊 Calcul des métriques...")
    metrics = compute_metrics_per_model(reviews, ground_truth, all_criteria_ids)
    print()
    
    # Afficher le tableau
    print_metrics_table(metrics)
    
    # Calculer et afficher les erreurs
    print("🔍 Analyse des erreurs...")
    errors = compute_detailed_errors(reviews, ground_truth)
    print_error_summary(errors)
    
    # Sauvegarder les résultats
    save_detailed_results(generation_id, metrics, errors)
    
    # Recommandations
    print("=" * 80)
    print("💡 RECOMMANDATIONS")
    print("=" * 80)
    print()
    
    best_f1 = max(metrics.items(), key=lambda x: x[1]['f1'])
    best_cost = min(metrics.items(), key=lambda x: x[1]['avg_cost'])
    
    print(f"🏆 Meilleur F1-score:  {best_f1[0]} (F1={best_f1[1]['f1']:.4f})")
    print(f"💰 Plus économique:    {best_cost[0]} (${best_cost[1]['avg_cost']:.5f}/job)")
    print()
    
    # Calcul du ratio coût/performance
    cost_performance = {
        name: m['avg_cost'] / m['f1'] if m['f1'] > 0 else float('inf')
        for name, m in metrics.items()
    }
    best_ratio = min(cost_performance.items(), key=lambda x: x[1])
    
    print(f"⚖️  Meilleur ratio coût/performance: {best_ratio[0]} (${best_ratio[1]:.5f} par point de F1)")
    print()


def main():
    """Point d'entrée principal."""
    generation_id = 6
    analyze_generation(generation_id)


if __name__ == "__main__":
    main()

