# src/output_formats/context_output.py
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from models.langchain import create_pydantic_output_config

class ContextOutput(BaseModel):
    decisions: str = Field(description="Respuestas a las preguntas de decisión (yes/no/request/etc)")
    context: List[str] = Field(description="Lista de comentarios extraídos del contexto")

def context_output_format():
    """
    Define el formato de respuesta para la cadena de contexto usando Pydantic.
    Esto evita errores de JSON mal formados.
    """
    return create_pydantic_output_config(ContextOutput)