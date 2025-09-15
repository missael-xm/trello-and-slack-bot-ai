# src/output_formats/task_output.py
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from models.langchain import LangchainOutput

def task_output_format() -> LangchainOutput:
    """
    Define el formato de respuesta para la cadena de tareas.
    La IA debe devolver título y lista de tasks en bullet points.
    """
    response_schemas = [
        ResponseSchema(
            name="title",
            description="General goal. Empty or Null if there are no tasks",
            type="string"
        ),
        ResponseSchema(
            name="tasks",
            description="*Tasks:*\n• task_1\n• task_2\n ...\n• task_n. Empty" +
            " or Null if there are no tasks",
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