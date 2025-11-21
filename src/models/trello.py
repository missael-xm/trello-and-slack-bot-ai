# src/models/trello.py
from pydantic import BaseModel
from typing import Optional

class TrelloAppCreator(BaseModel):
    """Modelo para la estructura detallada de appCreator"""
    id: str
    name: str

class TrelloEvent(BaseModel):
    """Modelo para el webhook crudo de Trello"""
    action: dict
    model: dict
    webhook: dict

class TrelloActionMainData(BaseModel):
    """Modelo para datos procesados de Trello"""
    action_id: str = ""
    action_type: str = ""
    app_creator: Optional[TrelloAppCreator] = None
    card_list_name: str = ""
    card_list_before: str = ""
    card_list_after: str = ""
    name_before_action: str = ""
    name_after_action: str = ""
    username: str = ""
    card_id: str = ""
    card_title: str = ""
    comment: str = ""
    comment_date: str = ""
    allowed_users: list = ["carloschilque"]