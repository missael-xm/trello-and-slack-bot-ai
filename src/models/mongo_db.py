# src/models/mongo_db.py
from pydantic import BaseModel
from bson import ObjectId

class TrelloCard(BaseModel):
    """Modelo para documentos MongoDB de cards de Trello"""
    _id: ObjectId
    card_id: str = ""
    comment_history: list = []