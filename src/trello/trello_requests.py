# src/trello/trello_requests.py
from requests.exceptions import RequestException
from requests import get
from typing import Union
from utils.config import trello_api_url, trello_api_key, trello_api_token
import json

class TrelloRequests():
    """
    Cliente para hacer requests a la API de Trello.
    Maneja autenticación y construye URLs automáticamente.
    """
    def __init__(self) -> None:
        self.default_headers = {
            "Accept": "application/json"
        }
        self.default_params = {
            "key": trello_api_key,
            "token": trello_api_token,
        }

    def get_card_data(
        self,
        card_id: str,
        params: dict = {},
        metadata: bool = False,
        field: str = None,
        headers: dict = {}
    ) -> Union[None, list, dict]:
        """
        Obtiene datos de una card de Trello.
        
        Args:
            card_id: ID de la card
            metadata: True para custom fields
            field: Campo específico (actions, desc, attachments)
        """
        try:
            card_data = None
            card_data_url = self.url_for_card_data(
                card_id=card_id,
                metadata=metadata,
                field=field,
            )
            headers.update(self.default_headers)
            params.update(self.default_params)

            card_data_response = get(
                url=card_data_url,
                params=params,
                headers=headers
            )

            card_data_response.raise_for_status()
            card_data = json.loads(card_data_response.content)
        except RequestException as e:
            print("GET request failed: ", e)

        return card_data

    def url_for_card_data(
        self,
        card_id: str,
        metadata: bool,
        field: str
    ) -> str:
        """Construye la URL para la API de Trello basado en los parámetros"""
        card_data_url = f"{trello_api_url}/1/cards/{card_id}"

        if metadata:
            card_data_url = card_data_url + "/customFieldItems"
        elif field is not None:
            card_data_url = card_data_url + f"/{field}"

        return card_data_url