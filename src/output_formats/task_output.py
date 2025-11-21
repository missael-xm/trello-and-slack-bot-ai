from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from models.langchain import create_pydantic_output_config

class TaskOutput(BaseModel):
    title: str = Field(description="Título general de las tareas")
    tasks: List[str] = Field(description="Lista de tareas específicas en formato bullet points")
    categories: List[str] = Field(description="Categorías de cada tarea")
    priorities: List[str] = Field(description="Prioridades de cada tarea")
    time_estimates: List[float] = Field(description="Estimación realista de horas para desarrollar cada tarea (ej: 2.0, 4.5, 8.0)")
    complexities: List[str] = Field(description="Nivel de complejidad técnica (Baja, Media, Alta)")
    required_skills: List[List[str]] = Field(description="Lista de listas con las habilidades técnicas requeridas para CADA tarea (ej: [['React', 'CSS'], ['Python', 'SQL']] )")

def task_output_format():
    """Define y retorna el parser para el formato de salida de tareas"""
    return create_pydantic_output_config(TaskOutput)