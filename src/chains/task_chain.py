# src/chains/task_chain.py
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates.task_chain_template import TASK_CHAIN_TEMPLATE
from output_formats.task_output import task_output_format

def generate_tasks(llm) -> LLMChain:
    """
    Cadena que identifica tareas específicas de desarrollo web
    a partir del contexto de conversación.
    """
    prompt = PromptTemplate(
        input_variables=[
            'conversation_context',
            'allowed_users',
        ],
        template=TASK_CHAIN_TEMPLATE,
        partial_variables={
            "format_instructions": task_output_format().format
        }
    )

    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=task_output_format().parser,
        verbose=False,
        output_key="task_output",
    )

    return llm_chain