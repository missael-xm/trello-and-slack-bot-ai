# src/models/langchain.py
from langchain.output_parsers import StructuredOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Union, Any, Optional
from langchain.schema import BaseOutputParser

class LangchainOutput(BaseModel):
    """Estructura estandarizada para output parsers de LangChain"""
    format_instructions: str = Field(description="Instrucciones de formato para el prompt")
    parser: Optional[Any] = Field(default=None, description="Parser para la salida (StructuredOutputParser o PydanticOutputParser)")
    schema_model: Optional[Any] = Field(default=None, description="Esquema Pydantic si es aplicable")

    model_config = {
        'arbitrary_types_allowed': True,
        'json_schema_extra': {
            "example": {
                "format_instructions": "Instrucciones de formato...",
                "parser": None,
                "schema_model": None
            }
        }
    }

# Funciones de utilidad para crear configuraciones estandarizadas
def create_pydantic_output_config(pydantic_model: BaseModel) -> LangchainOutput:
    """Crea configuración para output parser basado en Pydantic"""
    parser = PydanticOutputParser(pydantic_object=pydantic_model)
    return LangchainOutput(
        format_instructions=parser.get_format_instructions(),
        parser=parser,
        schema_model=pydantic_model
    )

def create_structured_output_config(response_schemas: list) -> LangchainOutput:
    """Crea configuración para output parser estructurado"""
    parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return LangchainOutput(
        format_instructions=parser.get_format_instructions(),
        parser=parser
    )