# src/chains/context_chain.py
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from templates.context_chain_template import CONTEXT_CHAIN_TEMPLATE
from callbacks.context_chain_callback import ContextChainCallback
from output_formats.context_output import context_output_format

def generate_conversation_context(llm, trello_card_id) -> LLMChain:
    """
    Cadena que analiza el historial de comentarios y extrae contexto relevante.
    Usa callback para persistir en MongoDB y evitar procesamiento duplicado.
    """
    prompt = PromptTemplate(
        input_variables=[
            'card_comment_history',
            'recent_comment',
            'allowed_users',
        ],
        name='Assistant Rol',
        template=CONTEXT_CHAIN_TEMPLATE,
        partial_variables={
            "format_instructions": context_output_format().format
        },
        validate_template=True,
    )

    llm_chain = LLMChain(
        name="Agatha Trunchbull",
        llm=llm,
        prompt=prompt,
        output_parser=context_output_format().parser,
        verbose=False,
        output_key="conversation_context",
        callbacks=[ContextChainCallback(trello_card_id=trello_card_id)]
    )

    return llm_chain