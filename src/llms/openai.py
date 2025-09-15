# src/llms/openai.py
from langchain_openai import ChatOpenAI
import utils.config as config

def get_models():
    """
    Factory de modelos OpenAI con diferentes configuraciones.
    Devuelve instancias preconfiguradas de ChatOpenAI.
    """
    models = {
        "base": ChatOpenAI(
            model=config.model_name,
            temperature=config.base_temperature,
            openai_api_key=config.openai_api_key_env
        ),
        "high_temp": ChatOpenAI(
            model=config.model_name,
            temperature=0.7,  # Más creativo
            openai_api_key=config.openai_api_key_env
        ),
        "zero_temp": ChatOpenAI(
            model=config.model_name,
            temperature=0,  # Determinístico
            openai_api_key=config.openai_api_key_env
        ),
    }

    return models