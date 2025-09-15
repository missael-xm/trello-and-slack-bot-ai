# src/trello/trello_action_events.py
from trello.trello_main_data import TrelloMainData
from trello.trello_features import TrelloFeatures
from trello_to_slack.tts_features import TrelloToSlackFeatures
from models.trello import TrelloEvent
from utils.search_functions import find_mentions
from llms.openai import get_models
import re

class TrelloActionEvents(TrelloMainData, TrelloFeatures, TrelloToSlackFeatures):
    """
    Manejador principal de eventos de Trello. Decide qué acción tomar
    basado en el tipo de evento y ejecuta el flujo correspondiente.
    """
    def __init__(self, trello_event: TrelloEvent = None) -> None:
        TrelloFeatures.__init__(self)
        TrelloMainData.__init__(self, trello_event_action=trello_event.action)
        
        self.main_data = self.get_main_data()
        TrelloToSlackFeatures.__init__(
            self,
            llm=get_models()["base"],
            recent_comment=(
                f"[author: {self.main_data.username} - comment date:" +
                f"{self.main_data.comment_date}]{self.main_data.comment}"
            ),
            card_id=self.main_data.card_id,
            card_title=self.main_data.card_title,
            event_type=self.main_data.action_type,
        )
        
        # Validaciones de seguridad y filtrado
        self.valid_user = (self.main_data.username in self.main_data.allowed_users)
        self.mentions = find_mentions(
            text=self.main_data.comment,
            users_trello=self.main_data.allowed_users,
        )

    def get_data_and_comment_in_slack(self, with_figma: bool = False):
        """Prepara los datos y ejecuta el envío a Slack"""
        figma_url, card_comment_history = self.get_filtered_comment_history(
            card_id=self.main_data.card_id,
            with_figma=with_figma,
        )

        # Agregar task automática de Figma si se detectó
        if figma_url:
            card_comment_history.append(
                f"[author: {self.main_data.username} - comment date: date " +
                "of first comment]@carloschilque Code the figma design " +
                f"[figma]({figma_url})."
            )

        self.card_comment_history = card_comment_history
        self.slack_message_data = self.search_message(request_id=self.card_id)
        self.allowed_users = self.main_data.allowed_users

        # Obtener link de Fourthwall si es un nuevo mensaje
        if self.slack_message_data is None:
            self.shop_link = self.get_fourthwall_shop_link(
                card_id=self.main_data.card_id
            )

        result = self.comment_on_slack()
        print(result)
        print("______________________FINISH_________________________")

    def create_card_action(self):
        """Maneja la creación de nuevas cards"""
        match_stg3 = re.search("En proceso", self.main_data.card_list_name)
        match_stg4 = re.search("Lista de tareas", self.main_data.card_list_name)

        if match_stg3 or match_stg4:
            self.get_data_and_comment_in_slack(with_figma=True)

    def update_card_action(self):
        """Maneja la actualización de cards (movimientos entre listas)"""
        if self.main_data.card_list_after == "En proceso":
            self.get_data_and_comment_in_slack(with_figma=True)

    def comment_update_action(self):
        """Maneja actualizaciones de comentarios"""
        self.get_data_and_comment_in_slack()

    def comment_card_action(self) -> None:
        """Maneja nuevos comentarios en cards"""
        list_of_names = ("En proceso","Lista de tareas")
        match = None

        for list_name in list_of_names:
            pattern = r'\b' + re.escape(list_name) + r'\b'
            match = re.search(pattern, self.main_data.card_list_name)
            if match:
                break

        # Validaciones complejas de qué procesar
        if isinstance(self.main_data.app_creator, dict) is False and match:
            print(f'card commented on in {self.main_data.card_list_name} by {self.main_data.username}')

            if self.valid_user or self.mentions:
                self.get_data_and_comment_in_slack()
            else:
                print(f"'{self.main_data.card_title}' requires no action")
        elif isinstance(self.main_data.app_creator, dict):
            print("**Butler bot comment**")  # Ignorar bots de Trello
        else:
            print("__No matches__")