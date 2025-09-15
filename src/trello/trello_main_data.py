# src/trello/trello_main_data.py
from models.trello import TrelloActionMainData
from utils.search_functions import find_key_get_value

class TrelloMainData():
    """
    Transforma el webhook crudo de Trello en datos estructurados y limpios.
    Es el primer paso en el procesamiento de cualquier evento de Trello.
    """
    def __init__(self, trello_event_action: dict) -> None:
        # Extracción segura de datos del webhook
        comment = find_key_get_value("text", trello_event_action['data'])
        card_title = find_key_get_value("name", trello_event_action['data']['card'])
        
        self.action_main_data = TrelloActionMainData(
            action_id=trello_event_action['id'],
            action_type=trello_event_action['type'],
            app_creator=trello_event_action['appCreator'],
            card_list_name=(
                trello_event_action['data']['list']['name']
                if 'list' in trello_event_action['data'] else ""
            ),
            card_list_before=(
                trello_event_action['data']['listBefore']['name']
                if 'listBefore' in trello_event_action['data'] else ""
            ),
            card_list_after=(
                trello_event_action['data']['listAfter']['name']
                if 'listAfter' in trello_event_action['data'] else ""
            ),
            username=trello_event_action['memberCreator']['username'],
            card_id=trello_event_action['data']['card']['id'],
            card_title=card_title if card_title else "",
            comment=comment if comment else "",
            comment_date=trello_event_action['date'],
        )

    def get_main_data(self) -> TrelloActionMainData:
        """Devuelve los datos estructurados del webhook"""
        return self.action_main_data