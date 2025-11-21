# src/assistant/ecommerce_assistant.py
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import SequentialChain
from chains.new_design_chain import generate_new_design
from chains.context_chain import generate_conversation_context
from chains.task_chain import generate_tasks
from chains.translator_chain import translate_text_string
from trello.trello_requests import TrelloRequests
from database.mongo_db import MongoDB
from typing import Union
import json
import time

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
        try:
            if event_type == "updateCard":
                # Análisis de descripción para nuevos diseños
                card_data = self.get_card_data(
                    card_id=self.trello_card_id,
                    field="desc",
                )
                card_description = card_data.get("_value", "") if hasattr(card_data, 'get') else str(card_data)
                
                output = generate_new_design(llm=self.llm).invoke(
                    input={"card_description": card_description},
                    return_only_outputs=True
                )

                if not output['new_design']['context']:
                    print("Description without relevant information")
                    return None
                else:
                    comment = [
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

                # FIX: Manejar tanto Objeto Pydantic como Diccionario
                ctx_result = output['conversation_context']
                if hasattr(ctx_result, 'dict'):
                    ctx_data = ctx_result.dict()
                else:
                    ctx_data = ctx_result

                # Validar contenido
                if not ctx_data.get('context') or len(ctx_data['context']) == 0:
                    return None
                else:
                    return ctx_data['context']
                    
        except Exception as e:
            print(f"❌ Error in get_context_by_event_type: {e}")
            return None

    def get_answer(self, event_type: str) -> dict:
        """Ejecuta la cadena secuencial completa de IA con control de Rate Limit"""
        try:
            print("🔄 Paso 1: Obteniendo contexto...")
            new_context = self.get_context_by_event_type(event_type=event_type)

            print("Context: ", new_context)
            if new_context is None or len(new_context) == 0:
                return {"translation": {"translated_tasks": [], "summary": "No relevant information", "notes": ""}}

            # 🛑 PAUSA OBLIGATORIA (Rate Limit)
            print("⏳ Esperando 21s para respetar límite de OpenAI (3 RPM)...")
            time.sleep(21)

            print("🔄 Paso 2: Ejecutando análisis y traducción...")
            
            overall_chain = SequentialChain(
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

            try:
                result = overall_chain.invoke(
                    input={
                        "conversation_context": new_context,
                        "allowed_users": self.allowed_users,
                        "input_language": self.input_language,
                        "output_language": self.output_language,
                    },
                    return_only_outputs=True
                )
            except Exception as chain_error:
                if "Rate limit" in str(chain_error):
                    print("⚠️ Rate limit alcanzado de nuevo. Reintentando en 30s...")
                    time.sleep(30)
                    result = overall_chain.invoke(
                        input={
                            "conversation_context": new_context,
                            "allowed_users": self.allowed_users,
                            "input_language": self.input_language,
                            "output_language": self.output_language,
                        },
                        return_only_outputs=True
                    )
                else:
                    raise chain_error

            output = result["translate_output"]
            # Asegurar que devolvemos un diccionario, no un objeto Pydantic
            if hasattr(output, 'dict'): 
                return output.dict()
            return output

        except Exception as e:
            print(f"❌ Error in get_answer: {e}")
            if "Rate limit" not in str(e):
                import traceback
                traceback.print_exc()
            return {"translation": {"translated_tasks": [], "summary": f"Error: {str(e)}", "notes": ""}}