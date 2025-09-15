# src/models/langchain.py
from langchain.output_parsers import StructuredOutputParser
from pydantic import BaseModel
from typing import Union

class LangchainOutput(BaseModel):
    """Estructura estandarizada para output parsers de LangChain"""
    format: str  # Instrucciones de formato para el prompt
    parser: Union[None, StructuredOutputParser]  # Parser para la salida