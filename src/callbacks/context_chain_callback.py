# src/callbacks/context_chain_callback.py
from typing import Any, Dict
from langchain.callbacks.base import BaseCallbackHandler
from database.mongo_db import MongoDB

class ContextChainCallback(BaseCallbackHandler, MongoDB):
    """
    Callback que se ejecuta después de que LangChain procesa el contexto.
    Persiste en MongoDB para evitar procesamiento duplicado y optimizar costos.
    """
    def __init__(self, trello_card_id: str) -> None:
        super().__init__()
        MongoDB.__init__(self)
        self.trello_card_id = trello_card_id

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Se ejecuta cuando LangChain termina de procesar"""
        try:
            print("bot decisions: ", outputs["conversation_context"]["decisions"])
            response = outputs["conversation_context"]["context"]
            output = self.filter_output(response=response)
            output_format = {"context": output}
            outputs["conversation_context"] = output_format
        except Exception as e:
            print("ON_CHAIN_END EXCEPTION => ", e)

    def on_chain_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Maneja errores en el procesamiento de la cadena"""
        print("ON_CHAIN_ERROR => ", error)

    def filter_output(self, response: list = []) -> list:
        """
        Filtra comentarios ya procesados usando MongoDB como memoria persistente.
        Evita llamadas redundantes a OpenAI y reduce costos.
        """
        data = self.data_select(card_id=self.trello_card_id)

        if data is not None:
            extracted_comments = set(response)
            history = set(data.comment_history)
            filter_comments = extracted_comments.difference(history)
            filtered_history = list(filter_comments)

            if len(filtered_history) > 0:
                new_history = list(history) + filtered_history
                self.data_update(
                    card_id=self.trello_card_id,
                    comment_history=new_history,
                )

            return filtered_history
        else:
            self.data_insert(
                card_id=self.trello_card_id,
                comment_history=response,
            )
            return response