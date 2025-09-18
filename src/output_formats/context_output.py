from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from models.langchain import create_structured_output_config

def context_output_format():
    """
    Define el formato de respuesta para la cadena de contexto.
    La IA debe devolver decisiones y contexto extraído.
    """
    response_schemas = [
        ResponseSchema(
            name="decisions",
            description="answers to the questions",
            type="string"
        ),
        ResponseSchema(
            name="context",
            description="Final answer",
            type="List"
        ),
    ]

    return create_structured_output_config(response_schemas)  # ← Esto ahora funcionará