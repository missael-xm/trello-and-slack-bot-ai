# src/database/mongo_db.py
from pymongo import MongoClient
from pymongo.collection import Collection
from models.mongo_db import TrelloCard
from utils.config import mongodb_uri
from typing import Union

class MongoDB():
    """
    Cliente de MongoDB para persistencia del estado de procesamiento.
    Evita procesar comentarios duplicados y reduce costos de OpenAI.
    """
    def __init__(self) -> None:
        self.client = MongoClient(mongodb_uri)
        self.collection = self.init_db_and_get_collection()

    def init_db_and_get_collection(self) -> Union[None, Collection]:
        """Inicializa la base de datos y devuelve la colección"""
        db = self.client["trello_db"]
        collection = db["card"]
        return collection

    def data_insert(self, card_id: str = "", comment_history: list = []):
        """Inserta un nuevo documento para una card"""
        card_data = self.data_select(card_id=card_id)
        if card_data is not None:
            return card_data

        data = self.collection.insert_one({
            "card_id": card_id,
            "comment_history": comment_history
        })

        print("INSERTED: ", data.inserted_id)
        return None

    def data_update(self, card_id: str = "", comment_history: list = []):
        """Actualiza el historial de comentarios de una card"""
        self.collection.update_one(
            {"card_id": card_id},
            {"$set": {"comment_history": comment_history}}
        )

    def data_select(self, card_id: str = "") -> Union[None, TrelloCard]:
        """Obtiene los datos de una card específica"""
        data = self.collection.find_one({"card_id": card_id})

        if data is not None:
            format_data = TrelloCard(
                _id=str(data["_id"]),
                card_id=data["card_id"],
                comment_history=data["comment_history"],
            )
            return format_data

        return None