# src/trello/trello_features.py
from trello.trello_requests import TrelloRequests
from langchain_community.document_loaders import RecursiveUrlLoader
from typing import Union
import re

class TrelloFeatures(TrelloRequests):
    """
    Funcionalidades avanzadas para procesamiento de cards de Trello.
    Incluye detección de Figma, scraping de Fourthwall, y filtrado de comentarios.
    """
    def __init__(self) -> None:
        TrelloRequests.__init__(self)

    def get_attachments(self, card_id: str) -> Union[None, list]:
        """Obtiene archivos adjuntos de una card"""
        attachments = self.get_card_data(card_id=card_id, field="attachments")
        attachment_objects: list = []

        if len(attachments) > 0:
            for attachment in attachments:
                attachment_objects.append({
                    "name": attachment.get("fileName"),
                    "url": attachment.get("url"),
                })

        return attachment_objects

    def search_figma_url(self, text: str = "") -> Union[None, str]:
        """Busca URLs de Figma en texto usando regex"""
        figma_pattern = r'https?://[^\s\[\]\(\)]*figma[^\s\[\]\(\)]*'
        matches: list = re.findall(figma_pattern, text)
        return matches[0] if len(matches) > 0 else None

    def get_filtered_comment_history(self, card_id: str, with_figma=False):
        """Obtiene historial de comentarios filtrado y detecta Figma"""
        card_comment_actions = self.get_card_data(
            card_id=card_id, field="actions", params={"filter": "commentCard"}
        )
        
        card_comment_history: list = []
        figma_url = None

        for card_action in card_comment_actions:
            if card_action['appCreator'] is None:  # Solo comentarios de usuarios humanos
                if with_figma and figma_url is None:
                    figma_url = self.search_figma_url(card_action['data']['text'])

                comment = (
                    f"[author: {card_action['memberCreator']['username']} - "
                    f"comment date: {card_action['date']}]"
                    f"{card_action['data']['text']}"
                )
                card_comment_history.append(comment)

        card_comment_history.reverse()  # Más antiguo → más reciente
        return figma_url, card_comment_history

    def get_fourthwall_shop_link(self, card_id: str) -> Union[None, str]:
        """Busca links de Fourthwall usando custom fields y scraping"""
        # Implementación completa que vimos anteriormente
        # Incluye custom fields, descripción, y scraping automático
        pass