# src/trello_to_slack/tts_features.py
from langchain_openai import ChatOpenAI
from slack.slack_features import SlackFeatures
from assistant.ecommerce_assistant import EcommerceAssistant
from typing import Union
from langchain_community.callbacks import get_openai_callback
import json

class TrelloToSlackFeatures(SlackFeatures, EcommerceAssistant):
    """
    Orquestador principal que conecta Trello → IA → Slack.
    Hereda de SlackFeatures y EcommerceAssistant para tener todas las funcionalidades.
    """
    def __init__(
        self,
        llm: ChatOpenAI = None,
        card_comment_history: list = [],
        recent_comment: str = "",
        card_id: str = "",
        card_title: str = "",
        shop_link: str = "",
        message: dict = {},
        slack_message_data: Union[None, dict] = None,
        event_type: str = "",
    ) -> None:
        SlackFeatures.__init__(self)
        EcommerceAssistant.__init__(
            self,
            llm=llm,
            trello_card_id=card_id,
            card_comment_history=card_comment_history,
            recent_comment=recent_comment,
        )
        self.card_id = card_id
        self.card_title = card_title
        self.shop_link = shop_link
        self.message = message
        self.slack_message_data = slack_message_data
        self.event_type = event_type

    def comment_on_slack(self) -> Union[None, str]:
        """
        Ejecuta la cadena completa de IA y envía el resultado a Slack.
        Monitorea el costo de OpenAI con get_openai_callback().
        """
        with get_openai_callback() as cb:
            self.message = self.get_answer(event_type=self.event_type)
            print("\nOpenAI Usage Cost:\n", cb, "\n")

        # Validar si hay tasks para enviar
        if (
            isinstance(self.message, dict) and
            not self.message['translation']['tasks']
        ):
            return "No new task requests found"
        elif isinstance(self.message, str):
            return self.message

        # Enviar a Slack (nuevo mensaje o respuesta en hilo)
        if self.slack_message_data is None:
            self.new_message(
                request_id=self.card_id,
                title=self.card_title,
                message=self.message['translation'],
                shop_link=self.shop_link,
            )
        else:
            self.send_message_in_the_thread(
                message=self.message['translation'],
                slack_message_data=self.slack_message_data,
            )

        return json.dumps(self.message, indent=2)