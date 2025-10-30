# src/chains/new_design_chain.py - CORREGIDO
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates.new_design_chain_template import NEW_DESIGN_CHAIN_TEMPLATE
from output_formats.new_design_output import new_design_output_format

def generate_new_design(llm) -> LLMChain:
    """
    Cadena especializada para analizar descripciones de cards
    y detectar requisitos de desarrollo cuando se mueven a 'Ready To Code'.
    """
    output_config = new_design_output_format()
    
    prompt = PromptTemplate(
        input_variables=[
            'card_description',
        ],
        # ELIMINADO: name='Assistant Rol',
        template=NEW_DESIGN_CHAIN_TEMPLATE,
        partial_variables={
            "format_instructions": output_config.format_instructions
        }
    )

    llm_chain = LLMChain(
        # ELIMINADO: name="Agatha Trunchbull",
        llm=llm,
        prompt=prompt,
        output_parser=output_config.parser,
        verbose=False,
        output_key="new_design",
    )

    return llm_chain