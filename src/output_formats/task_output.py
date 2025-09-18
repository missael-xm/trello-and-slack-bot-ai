from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from models.langchain import create_pydantic_output_config

class TaskOutput(BaseModel):
    title: str = Field(description="Título general de las tareas")
    tasks: List[str] = Field(description="Lista de tareas específicas en formato bullet points")
    categories: List[str] = Field(description="Categorías de cada tarea")
    priorities: List[str] = Field(description="Prioridades de cada tarea")

def task_output_format():
    """Define y retorna el parser para el formato de salida de tareas"""
    return create_pydantic_output_config(TaskOutput)