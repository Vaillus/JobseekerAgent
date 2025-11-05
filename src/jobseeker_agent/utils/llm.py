# Importe toutes les classes de modèles au début
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from typing import Optional

# Prix par million de tokens (input/output) - À mettre à jour régulièrement selon les prix actuels
MODEL_PRICES = {
    # OpenAI
    "gpt-o4-mini": {"input": 4.00, "output": 16.00},
    "gpt-4.1-nano": {"input": 0.20, "output": 0.80},
    "gpt-4.1-mini": {"input": 0.80, "output": 3.20},
    "gpt-4.1": {"input": 3.00, "output": 12.00}, 
    "gpt-5-nano": {"input": 0.050, "output": 0.40},  
    "gpt-5-mini": {"input": 0.250, "output": 2.00},  
    "gpt-5": {"input": 1.250, "output": 10.00}, 
    "gpt-5-pro": {"input": 15.00, "output": 120.00}, 
    
    # Anthropic
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    
    # Google Gemini
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-pro": {"input": 1.25, "output": 5.00},  # Estimation - à vérifier
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calcule le coût basé sur les tokens utilisés et le modèle.
    
    Args:
        model_name: Nom du modèle utilisé
        input_tokens: Nombre de tokens d'entrée
        output_tokens: Nombre de tokens de sortie
    
    Returns:
        Coût total en dollars
    """
    model_lower = model_name.lower()
    
    # Chercher une correspondance exacte
    if model_lower in MODEL_PRICES:
        prices = MODEL_PRICES[model_lower]
    else:
        # Chercher par préfixe (ex: "gpt-4-0125-preview" -> "gpt-4")
        prices = None
        for known_model in MODEL_PRICES.keys():
            if model_lower.startswith(known_model):
                prices = MODEL_PRICES[known_model]
                break
        
        if not prices:
            print(f"⚠️ Prix non trouvé pour le modèle '{model_name}'. Coût = 0.")
            return 0.0
    
    input_cost = (input_tokens / 1_000_000) * prices["input"]
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    
    return input_cost + output_cost


def get_llm(model_name: str, temperature: float = 0, reasoning: Optional[dict] = None):
    """
    Retourne une instance du modèle de chat en fonction de son nom.
    Args:
        model_name: Nom du modèle à utiliser.
        temperature: Température du modèle.
        reasoning: Configuration du raisonnement. Attention, cette 
        fonctionnalité est disponible uniquement pour les modèles OpenAI 
        pour le moment.
    Returns:
        Instance du modèle de chat.
    """
    if model_name.startswith("gpt"):
        print(f"✅ Chargement du modèle OpenAI : {model_name}")
        return ChatOpenAI(model=model_name, temperature=temperature, reasoning=reasoning)
    
    elif "gemini" in model_name:
        if not reasoning:
            thinking_budget = -1
        elif "pro" in model_name:
            thinking_budget = 128 if reasoning["effort"] == "low" else -1
        else:
            thinking_budget = 0 if reasoning["effort"] == "low" else -1
        print(f"✅ Chargement du modèle Gemini : {model_name} with thinking budget {thinking_budget}")
        return ChatGoogleGenerativeAI(
            model=model_name, 
            temperature=temperature, 
            thinking_budget=thinking_budget
        )
        
    elif "claude" in model_name:
        print(f"✅ Chargement du modèle Claude : {model_name}")
        return ChatAnthropic(model=model_name, temperature=temperature)
        
    else:
        raise ValueError(f"Modèle inconnu ou non supporté : {model_name}")