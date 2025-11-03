from dotenv import load_dotenv
from langchain.schema import HumanMessage, AIMessage
from langchain_core.callbacks import UsageMetadataCallbackHandler
from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Union, Optional, Any
import json
import time

from jobseeker_agent.utils.paths import load_prompt
from jobseeker_agent.utils.llm import get_llm, calculate_cost


load_dotenv()

class Evaluation(TypedDict):
    """Single evaluation criterion."""
    id: Annotated[int, ..., "The integer id of the criterion from the evaluation grid."]
    criteria: Annotated[str, ..., "The criteria that are met by the job description."]
    evidence: Annotated[str, ..., "The evidence for the criteria."]
    score: Annotated[float, ..., "The score for this criterion."]

class JobReviewResponse(TypedDict):
    """Response structure for job review."""
    evaluation_grid: Annotated[List[Evaluation], ..., "List of evaluations for each relevant evaluation criterion"]
    score: Annotated[float, ..., "raw score computed from the evaluation grid. Can be negative."]



def _model_supports_reasoning(model_name: str) -> bool:
    """Vérifie si le modèle supporte le paramètre reasoning.
    
    Seuls les modèles gpt-5* supportent le reasoning.
    Les modèles gpt-4* ne le supportent pas.
    """
    model_lower = model_name.lower()
    # Seuls les modèles gpt-5* supportent le reasoning
    return model_lower.startswith("gpt-5")


def review(
    job: Dict[str, Any], 
    job_details: Dict[str, Any], 
    model: str = "gpt-4.1", 
    with_correction: bool = True, 
    reasoning_level: Optional[str] = None
):
    """Reviews a job using specified model and optional self-correction.
    
    Args:
        job: Job dict containing at least 'id', 'title', 'company', 'location'
        job_details: Job details dict containing 'description'
        model: Model name to use (default: "gpt-4.1")
        with_correction: Whether to apply self-correction (default: True)
        reasoning_level: Level of reasoning to use. "low", "medium", "high" (default: None)
            Note: Only supported for gpt-5* models. Ignored for other models.
    
    Returns:
        Dict with evaluation_grid, score, id, and metadata (tokens, cost, execution_time)
    """
    start_time = time.time()
    
    review_prompt = load_prompt("reviewer")
    profil_pro = load_prompt("profil_pro")

    # Ne passer le paramètre reasoning que si le modèle le supporte
    reasoning = None
    if reasoning_level and _model_supports_reasoning(model):
        reasoning = {
            "effort": reasoning_level,
            "summary": None
        }
    elif reasoning_level and not _model_supports_reasoning(model):
        print(f"⚠️  Model {model} does not support reasoning_level. Ignoring parameter.")
    
    llm = get_llm(model, reasoning=reasoning)
    llm = llm.with_structured_output(JobReviewResponse)
    
    # Créer le callback pour capturer les métadonnées de tokens
    usage_callback = UsageMetadataCallbackHandler()
    
    message = HumanMessage(
        content=review_prompt.format(
            job_description=job_details["description"],
            job_title=job["title"],
            company_name=job["company"],
            location=job["location"],
            profil_pro=profil_pro
        )
    )
    
    # Invoquer avec le callback - les tokens seront cumulés automatiquement
    response = llm.invoke([message], config={"callbacks": [usage_callback]})
    
    if with_correction:
        messages = [
            message,
            AIMessage(content=json.dumps(response)),
            HumanMessage(content="Please correct the evaluation grid. Evaluate each element. Is it correct ? Are there any missing element ? If elements are removed from the evaluation grid, don't put them in the evaluation grid.")
        ]
        response = llm.invoke(messages, config={"callbacks": [usage_callback]})
    
    # Récupérer les métadonnées depuis le callback
    execution_time = time.time() - start_time
    
    # UsageMetadataCallbackHandler expose usage_metadata comme un dict organisé par modèle
    # Structure: {'model-name': {'input_tokens': X, 'output_tokens': Y, 'total_tokens': Z, ...}}
    usage_metadata = getattr(usage_callback, 'usage_metadata', {})
    
    # Sommer les tokens de tous les modèles (au cas où plusieurs appels avec différents modèles)
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    
    if usage_metadata:
        for model_usage in usage_metadata.values():
            if isinstance(model_usage, dict):
                input_tokens += model_usage.get('input_tokens', 0)
                output_tokens += model_usage.get('output_tokens', 0)
                total_tokens += model_usage.get('total_tokens', 0)
    
    # Si total_tokens n'est pas fourni, le calculer
    if total_tokens == 0 and (input_tokens > 0 or output_tokens > 0):
        total_tokens = input_tokens + output_tokens
    
    # Calculer le coût
    cost = calculate_cost(model, input_tokens, output_tokens)
    
    # Enrichir la réponse avec les métadonnées
    response["id"] = job["id"]
    response["metadata"] = {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "total_cost": cost,
        "execution_time": execution_time,
        "with_correction": with_correction
    }
    
    return response
