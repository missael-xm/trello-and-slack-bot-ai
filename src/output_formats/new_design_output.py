from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional, List
from models.langchain import create_pydantic_output_config

class NewDesignOutput(BaseModel):
    context: Optional[str] = Field(description="Contexto relevante extraído de la descripción")
    requirements: List[str] = Field(default_factory=list, description="Lista de requisitos técnicos")
    design_type: Optional[str] = Field(description="Tipo de diseño o desarrollo requerido")

def new_design_output_format():
    """Define y retorna el parser para el formato de salida de nuevo diseño"""
    return create_pydantic_output_config(NewDesignOutput)