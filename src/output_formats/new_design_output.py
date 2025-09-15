# src/output_formats/new_design_output.py
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from models.langchain import LangchainOutput

def new_design_output_format() -> LangchainOutput:
    """
    Define el formato de respuesta para la cadena de nuevos diseños.
    La IA debe devolver contexto de diseño.
    """
    response_schemas = [
        ResponseSchema(
            name="context",
            description="Final Answer",
            type="string"
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