# src/assistant/ecommerce_assistant.py
from langchain_openai import ChatOpenAI
from langchain.chains import SequentialChain
from chains.new_design_chain import generate_new_design
from chains.context_chain import generate_conversation_context
from chains.task_chain import generate_tasks
from chains.translator_chain import translate_text_string
from trello.trello_requests import TrelloRequests
from database.mongo_db import MongoDB
from typing import Union

class EcommerceAssistant(TrelloRequests, MongoDB):
    """
    Asistente principal de IA que orquesta las cadenas de LangChain.
    Hereda de TrelloRequests y MongoDB para tener acceso a datos.
    """
    def __init__(
        self,
        llm: ChatOpenAI = None,
        trello_card_id: str = "",
        recent_comment: str = "",
        card_comment_history: list = [],
        allowed_users: list = [],
        input_language: str = "English",
        output_language: str = "Spanish"
    ) -> None:
        TrelloRequests.__init__(self)
        MongoDB.__init__(self)
        self.llm = llm
        self.trello_card_id = trello_card_id
        self.card_comment_history = card_comment_history
        self.recent_comment = recent_comment
        self.input_language = input_language
        self.output_language = output_language
        self.allowed_users = allowed_users

    def get_context_by_event_type(self, event_type: str) -> Union[None, list, str]:
        """Selecciona la estrategia de contexto basado en el tipo de evento"""
        if event_type == "updateCard":
            # Análisis de descripción para nuevos diseños
            output = generate_new_design(llm=self.llm).invoke(
                input={
                    "card_description": self.get_card_data(
                        card_id=self.trello_card_id,
                        field="desc",
                    ).get("_value", "")
                },
                return_only_outputs=True
            )

            if not output['new_design']['context']:
                print("Description without relevant information")
            else:
                comment: list = [
                    "[author: any - comment date: date of first comment]" +
                    output['new_design']['context']
                ]
                self.data_insert(
                    card_id=self.trello_card_id,
                    comment_history=self.card_comment_history
                )
                comment.extend(self.card_comment_history)
                self.card_comment_history = comment

            return self.card_comment_history
        else:
            # Análisis de comentarios para tasks
            output = generate_conversation_context(
                llm=self.llm,
                trello_card_id=self.trello_card_id,
            ).invoke(
                input={
                    "card_comment_history": (
                        self.card_comment_history
                        if len(self.card_comment_history) > 0 else ""
                    ),
                    "recent_comment": self.recent_comment,
                    "allowed_users": self.allowed_users,
                },
                return_only_outputs=True
            )

            if len(output['conversation_context']['context']) == 0:
                return None
            else:
                return output['conversation_context']['context']

    def get_answer(self, event_type: str) -> dict:
        """Ejecuta la cadena secuencial completa de IA"""
        new_context = self.get_context_by_event_type(event_type=event_type)

        print("Context: ", new_context)
        if new_context is None or len(new_context) == 0:
            return "no relevant information"

        # Cadena secuencial: Context → Tasks → Translation
        overall_chain = SequentialChain(
            name='Sequential execution of chains',
            input_variables=[
                'conversation_context',
                'allowed_users',
                'input_language',
                'output_language'
            ],
            chains=[
                generate_tasks(llm=self.llm),
                translate_text_string(llm=self.llm),
            ],
            output_variables=['translate_output'],
            verbose=True
        )

        result = overall_chain.invoke(
            input={
                "conversation_context": new_context,
                "allowed_users": self.allowed_users,
                "input_language": self.input_language,
                "output_language": self.output_language,
            },
            return_only_outputs=True
        )

        return result["translate_output"]