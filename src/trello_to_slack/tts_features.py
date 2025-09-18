from langchain_openai import ChatOpenAI
from slack.slack_features import SlackFeatures
from assistant.ecommerce_assistant import EcommerceAssistant
from typing import Union
from langchain_community.callbacks import get_openai_callback
import json
from pydantic import BaseModel

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
        try:
            with get_openai_callback() as cb:
                self.message = self.get_answer(event_type=self.event_type)
                print("\nOpenAI Usage Cost:\n", cb, "\n")

            # Convertir Pydantic model a dict si es necesario
            if hasattr(self.message, 'dict'):
                self.message = self.message.dict()

            # Verificar la estructura del mensaje
            if isinstance(self.message, dict):
                # Si tiene la clave 'translation', usarla
                if 'translation' in self.message:
                    translation_data = self.message['translation']
                else:
                    # Si no tiene 'translation', usar el mensaje completo
                    translation_data = self.message
            else:
                print(f"❌ Invalid message format: {type(self.message)}")
                return f"Invalid message format: {type(self.message)}"

            # Validar si hay tasks para enviar
            if (
                isinstance(translation_data, dict) and
                'translated_tasks' in translation_data and
                not translation_data['translated_tasks']
            ):
                return "No new task requests found"

            # Convertir el formato del translator al formato que espera Slack
            slack_message = self._convert_to_slack_format(translation_data)
            
            print(f"📋 SLACK MESSAGE FORMAT: {slack_message}")

            # Enviar a Slack (nuevo mensaje o respuesta en hilo)
            if self.slack_message_data is None:
                self.new_message(
                    request_id=self.card_id,
                    title=self.card_title,
                    message=slack_message,  # Usar el formato convertido
                    shop_link=self.shop_link,
                )
            else:
                self.send_message_in_the_thread(
                    message=slack_message,  # Usar el formato convertido
                    slack_message_data=self.slack_message_data,
                )

            return json.dumps(self.message, indent=2, default=str)
            
        except Exception as e:
            print(f"❌ Error in comment_on_slack: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

    def _convert_to_slack_format(self, translation_data: dict) -> dict:
        """Convierte el formato del translator al formato que espera Slack"""
        try:
            # Extraer las tareas y convertirlas a formato markdown
            tasks_markdown = ""
            if 'translated_tasks' in translation_data and translation_data['translated_tasks']:
                for task in translation_data['translated_tasks']:
                    if isinstance(task, dict) and 'description' in task:
                        tasks_markdown += f"• {task['description']}\n"
            
            # Usar el summary como título o crear uno por defecto
            title = translation_data.get('summary', 'Tareas de desarrollo')
            
            # Crear el formato que espera Slack
            slack_format = {
                'title': title,
                'tasks': tasks_markdown.strip()
            }
            
            return slack_format
            
        except Exception as e:
            print(f"❌ Error converting to Slack format: {e}")
            # Fallback: devolver formato básico
            return {
                'title': 'Tareas de desarrollo',
                'tasks': 'Error procesando las tareas'
            }