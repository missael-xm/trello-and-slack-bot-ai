# src/chains/analytics_chain.py - CORREGIDO
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates.analytics_chain_template import ANALYTICS_CHAIN_TEMPLATE
from output_formats.analytics_output import analytics_output_format
from datetime import datetime

def generate_analytics(llm) -> LLMChain:
    """
    Cadena que genera análisis detallado con estimaciones y metadatos
    para el dashboard de analytics.
    """
    output_config = analytics_output_format()
    
    prompt = PromptTemplate(
        input_variables=[
            'conversation_context',
            'requested_by',
            'request_date'
        ],
        template=ANALYTICS_CHAIN_TEMPLATE,
        partial_variables={
            "format_instructions": output_config.format_instructions
        }
    )

    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=output_config.parser,
        verbose=False,
        output_key="analytics_output",
    )

    return llm_chain