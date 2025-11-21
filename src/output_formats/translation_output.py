# src/output_formats/translation_output.py
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from models.langchain import create_pydantic_output_config

class TranslatedTask(BaseModel):
    description: str = Field(description="Descripción de la tarea traducida al español")
    category: str = Field(description="Categoría técnica (Frontend, Backend, etc.)")
    priority: str = Field(description="Prioridad (Alta, Media, Baja)")
    # CAMPOS NUEVOS RECUPERADOS
    time_estimate: float = Field(description="Horas estimadas (copiar el valor numérico original)")
    complexity: str = Field(description="Complejidad técnica (copiar del original)")
    required_skills: List[str] = Field(description="Lista de habilidades técnicas (copiar del original)")

class TranslationOutput(BaseModel):
    translated_tasks: List[TranslatedTask] = Field(description="Lista de tareas traducidas con todos sus detalles técnicos")
    summary: str = Field(description="Resumen ejecutivo de las tareas")
    notes: Optional[str] = Field(description="Notas adicionales")

def translation_output_format():
    return create_pydantic_output_config(TranslationOutput)