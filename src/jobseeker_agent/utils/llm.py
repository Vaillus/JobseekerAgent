# Importe toutes les classes de modèles au début
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# --- 🏭 Ta fonction "Factory" ---
def get_llm(model_name: str, temperature: float = 0):
    """
    Retourne une instance du modèle de chat en fonction de son nom.
    """
    if model_name.startswith("gpt"):
        print(f"✅ Chargement du modèle OpenAI : {model_name}")
        return ChatOpenAI(model=model_name, temperature=temperature)
    
    elif "gemini" in model_name:
        print(f"✅ Chargement du modèle Gemini : {model_name}")
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        
    elif "claude" in model_name:
        print(f"✅ Chargement du modèle Claude : {model_name}")
        return ChatAnthropic(model=model_name, temperature=temperature)
        
    else:
        raise ValueError(f"Modèle inconnu ou non supporté : {model_name}")