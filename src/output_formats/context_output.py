# src/output_formats/context_output.py
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from models.langchain import LangchainOutput

def context_output_format() -> LangchainOutput:
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

    structured_output_parser = StructuredOutputParser.from_response_schemas(
        response_schemas=response_schemas
    )
    format_instructions = structured_output_parser.get_format_instructions(
        only_json=True
    )

    output = LangchainOutput(
        format=format_instructions,
        parser=structured_output_parser,
    )

    return output