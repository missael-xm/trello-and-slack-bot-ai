# src/slack/slack_features.py
from utils.config import slack_app_user_key, slack_bot_channel, slack_bot_channel_id
from utils.search_functions import find_key_get_value
from utils.slack import client, bot_setting
from typing import Union
import json

class SlackFeatures():
    """
    Clase principal para las funcionalidades de Slack.
    Maneja envío de mensajes, búsqueda y comunicación con canales.
    """
    def __init__(self) -> None:
        self.channel_id = slack_bot_channel_id
        self.channel = slack_bot_channel
        self.bot_name = bot_setting["username"]
        self.bot_image = bot_setting["profile_img"]
        self.carlos_tag = f"<@U09ER0ZG9EH>"  # Mention específico

    def search_message(self, request_id: str = "") -> Union[dict, None]:
        """
        Busca mensajes existentes en Slack por request_id (card_id de Trello).
        Evita crear mensajes duplicados para la misma card.
        """
        wc = client(auth_token=slack_app_user_key)
        message_data = None

        try:
            response = wc.search_messages(
                query=f"request_id: {request_id} in:{self.channel}",
            ).data

            if response["messages"]["total"] > 0:
                message_data = {
                    "team": find_key_get_value("team", response),
                    "channel_id": find_key_get_value("id", response),
                    "ts": find_key_get_value("ts", response),  # Timestamp del mensaje
                }

        except Exception as e:
            print(f"Error searching message: {e}")

        return message_data

    def new_message(
        self,
        request_id: str = "",
        message: dict = {},
        title: str = "",
        shop_link: str = "",
    ) -> None:
        """
        Crea un nuevo mensaje en Slack con formato rico (blocks y attachments).
        Usado cuando una card de Trello se menciona por primera vez.
        """
        try:
            client().chat_postMessage(
                channel=self.channel_id,
                username=self.bot_name,
                icon_url=self.bot_image,
                text=json.dumps(message),  # Fallback text
                blocks=[
                    {
                        "type": "divider"
                    },
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"""{message['title']} ~ {title}"""
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"`request_id: {request_id}`"
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": self.carlos_tag,  # Mention específico
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message['tasks'],  # Tareas identificadas
                        }
                    },
                    {
                        "type": "divider"
                    },
                ],
                attachments=[
                    {
                        "title": "URL de la tienda",
                        "text": shop_link,
                        "color": "#11f74b",  # Color verde
                    }
                ] if shop_link else []
            )
        except Exception as e:
            print("Exception => ", e)

    def send_message_in_the_thread(
        self,
        slack_message_data,
        message: dict = {},
    ) -> None:
        """
        Responde en el hilo de un mensaje existente.
        Usado cuando ya hay un mensaje para la card y se agregan más tasks.
        """
        try:
            client().chat_postMessage(
                channel=self.channel_id,
                username=self.bot_name,
                icon_url=self.bot_image,
                text=json.dumps(message),  # Fallback text
                reply_broadcast=True,  # Notificar al canal
                thread_ts=slack_message_data["ts"],  # Timestamp del mensaje padre
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"`***{message['title']}***`"
                        },
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": self.carlos_tag,
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message['tasks'],
                        }
                    },
                ],
            )
        except Exception as e:
            print("Exception => ", e)

    def send_simple_message(self, text: str, channel: str = None):
        """
        Envía un mensaje simple de texto. 
        Útil para debugging y respuestas rápidas.
        """
        try:
            target_channel = channel or self.channel_id
            client().chat_postMessage(
                channel=target_channel,
                username=self.bot_name,
                icon_url=self.bot_image,
                text=text
            )
        except Exception as e:
            print(f"Error sending simple message: {e}")