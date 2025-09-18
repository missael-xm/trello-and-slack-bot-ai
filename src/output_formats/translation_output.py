from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from models.langchain import create_pydantic_output_config

class TranslatedTask(BaseModel):
    description: str = Field(description="Descripción de la tarea traducida")
    category: str = Field(description="Categoría de la tarea")
    priority: str = Field(description="Prioridad de la tarea")

class TranslationOutput(BaseModel):
    translated_tasks: List[TranslatedTask] = Field(description="Lista de tareas traducidas")
    summary: str = Field(description="Resumen general traducido")
    notes: Optional[str] = Field(description="Notas adicionales sobre la traducción")

def translation_output_format():
    """Define y retorna el parser para el formato de salida de traducción"""
    return create_pydantic_output_config(TranslationOutput)