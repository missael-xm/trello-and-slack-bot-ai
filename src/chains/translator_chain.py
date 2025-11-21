# src/chains/translator_chain.py - CORREGIDO
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates.translator_chain_template import TRANSLATOR_CHAIN_TEMPLATE
from output_formats.translation_output import translation_output_format

def translate_text_string(llm) -> LLMChain:
    """
    Cadena que traduce y formatea las tareas identificadas
    para el equipo de desarrollo, manteniendo terminología técnica.
    """
    output_config = translation_output_format()
    
    prompt = PromptTemplate(
        input_variables=[
            "input_language",
            "output_language",
            "task_output"
        ],
        template=TRANSLATOR_CHAIN_TEMPLATE,
        partial_variables={
            "format_instructions": output_config.format_instructions
        }
    )

    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=output_config.parser,
        verbose=False,
        output_key="translate_output"
    )

    return llm_chain