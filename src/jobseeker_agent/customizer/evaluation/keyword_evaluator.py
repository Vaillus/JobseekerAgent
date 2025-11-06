"""
Module pour l'évaluation des keywords extraits.

Contient la structure de données pour les résultats d'évaluation
et les fonctions de calcul des métriques.
"""

from typing import List, Dict, Any
from typing_extensions import TypedDict, Annotated


class KeywordMatch(TypedDict):
    """Représente un match entre un keyword proposé et un keyword validé."""
    proposed: Annotated[str, ..., "The keyword proposed by Agent 1"]
    matched_with: Annotated[str, ..., "The keyword from ground truth it matches"]
    confidence: Annotated[float, ..., "Confidence score of the match (0.0 to 1.0)"]


class KeywordFalsePositive(TypedDict):
    """Représente un faux positif (proposé mais non validé)."""
    proposed: Annotated[str, ..., "The keyword proposed by Agent 1"]
    reason: Annotated[str, ..., "Reason why it was not validated (e.g., 'not in ground truth')"]


class KeywordFalseNegative(TypedDict):
    """Représente un faux négatif (validé mais non proposé)."""
    ground_truth: Annotated[str, ..., "The keyword from ground truth that was not proposed"]
    reason: Annotated[str, ..., "Reason why it was not proposed by Agent 1"]


class KeywordEvaluationResult(TypedDict):
    """Résultat de l'évaluation des keywords pour un job."""
    true_positives: Annotated[
        List[KeywordMatch],
        ...,
        "Keywords proposed by Agent 1 that match keywords in ground truth"
    ]
    false_positives: Annotated[
        List[KeywordFalsePositive],
        ...,
        "Keywords proposed by Agent 1 that are NOT in ground truth"
    ]
    false_negatives: Annotated[
        List[KeywordFalseNegative],
        ...,
        "Keywords in ground truth that were NOT proposed by Agent 1"
    ]
    metrics: Annotated[
        Dict[str, float],
        ...,
        "Calculated metrics: precision, recall, f1_score"
    ]


def calculate_metrics(
    tp: List[Any],
    fp: List[Any],
    fn: List[Any]
) -> Dict[str, float]:
    """
    Calcule les métriques Precision, Recall et F1-score.
    
    Args:
        tp: Liste des true positives
        fp: Liste des false positives
        fn: Liste des false negatives
    
    Returns:
        Dictionnaire avec precision, recall, f1_score
    """
    # Precision = TP / (TP + FP)
    precision = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) > 0 else 0.0
    
    # Recall = TP / (TP + FN)
    recall = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) > 0 else 0.0
    
    # F1 = 2 * (Precision * Recall) / (Precision + Recall)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4)
    }


def add_metrics_to_result(result: KeywordEvaluationResult) -> KeywordEvaluationResult:
    """
    Ajoute les métriques calculées à un résultat d'évaluation.
    
    Args:
        result: Résultat d'évaluation sans métriques calculées
    
    Returns:
        Résultat d'évaluation avec métriques calculées
    """
    metrics = calculate_metrics(
        tp=result["true_positives"],
        fp=result["false_positives"],
        fn=result["false_negatives"]
    )
    result["metrics"] = metrics
    return result


def print_evaluation_summary(result: KeywordEvaluationResult, job_id: int = None):
    """
    Affiche un résumé lisible d'un résultat d'évaluation.
    
    Args:
        result: Résultat d'évaluation
        job_id: ID du job (optionnel)
    """
    if job_id:
        print(f"\n{'='*80}")
        print(f"ÉVALUATION - JOB {job_id}")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print("ÉVALUATION")
        print(f"{'='*80}")
    
    metrics = result["metrics"]
    print(f"\n📊 MÉTRIQUES:")
    print(f"  Precision: {metrics['precision']:.2%} ({metrics['precision']:.4f})")
    print(f"  Recall:    {metrics['recall']:.2%} ({metrics['recall']:.4f})")
    print(f"  F1-Score:  {metrics['f1_score']:.2%} ({metrics['f1_score']:.4f})")
    
    print(f"\n✅ TRUE POSITIVES ({len(result['true_positives'])}):")
    for i, tp in enumerate(result["true_positives"][:10], 1):
        print(f"  {i:2d}. {tp['proposed']} → {tp['matched_with']} (conf: {tp['confidence']:.2f})")
    if len(result["true_positives"]) > 10:
        print(f"  ... et {len(result['true_positives']) - 10} autres")
    
    print(f"\n❌ FALSE POSITIVES ({len(result['false_positives'])}):")
    for i, fp in enumerate(result["false_positives"][:10], 1):
        print(f"  {i:2d}. {fp['proposed']} ({fp['reason']})")
    if len(result["false_positives"]) > 10:
        print(f"  ... et {len(result['false_positives']) - 10} autres")
    
    print(f"\n⚠️  FALSE NEGATIVES ({len(result['false_negatives'])}):")
    for i, fn in enumerate(result["false_negatives"][:10], 1):
        print(f"  {i:2d}. {fn['ground_truth']} ({fn['reason']})")
    if len(result["false_negatives"]) > 10:
        print(f"  ... et {len(result['false_negatives']) - 10} autres")
    
    print(f"\n{'='*80}\n")

