from langchain.output_parsers import PydanticOutputParser
from models.analytics import ProjectAnalytics, AnalyticsTask
from models.langchain import create_pydantic_output_config

def analytics_output_format():
    """Define y retorna el parser para el formato de analytics"""
    return create_pydantic_output_config(ProjectAnalytics)