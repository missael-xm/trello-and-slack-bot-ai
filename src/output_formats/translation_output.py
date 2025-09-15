# src/output_formats/translation_output.py
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from models.langchain import LangchainOutput

def translation_output_format() -> LangchainOutput:
    """
    Define el formato de respuesta para la cadena de traducción.
    La IA debe devolver un diccionario con la traducción.
    """
    response_schemas = [
        ResponseSchema(
            name="translation",
            description="translated",
            type="Dict"
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