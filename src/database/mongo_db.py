# src/database/mongo_db.py - CONEXIÓN CORREGIDA
from pymongo import MongoClient
from pymongo.collection import Collection
from models.mongo_db import TrelloCard
from utils.config import mongodb_uri
from typing import Union
import certifi
from datetime import datetime, timedelta
from collections import Counter

class MongoDB():
    """
    Cliente de MongoDB para persistencia del estado de procesamiento.
    Evita procesar comentarios duplicados y reduce costos de OpenAI.
    """
    def __init__(self) -> None:
        # CONEXIÓN CORREGIDA para problemas SSL en Windows
        try:
            # Opción 1: Intentar con certifi
            self.client = MongoClient(mongodb_uri, tlsCAFile=certifi.where())
            print("✅ MongoDB conectado con certifi")
        except Exception as e:
            try:
                # Opción 2: Intentar sin verificación SSL (solo para desarrollo)
                self.client = MongoClient(mongodb_uri, tlsAllowInvalidCertificates=True)
                print("✅ MongoDB conectado sin verificación SSL")
            except Exception as e2:
                # Opción 3: Conexión local como fallback
                print(f"❌ Error conexión MongoDB: {e}")
                print("🔄 Intentando con MongoDB local...")
                self.client = MongoClient("mongodb://localhost:27017/")
                print("✅ MongoDB local conectado")
        
        db = self.client["trello_db"]
        self.collection = db["card"]  # Colección existente
        self.analytics_collection = db["analytics"]

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

    def get_projects_since(self, start_date: datetime):
        """Obtiene proyectos desde una fecha específica"""
        return list(self.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }).sort("request_date", -1))

    def get_all_projects(self):
        """Obtiene todos los proyectos para analytics"""
        return list(self.analytics_collection.find().sort("request_date", -1))

    def get_project_by_id(self, project_id: str):
        """Obtiene un proyecto específico por ID"""
        return self.analytics_collection.find_one({"project_id": project_id})

    def update_project_status(self, project_id: str, status: str, actual_hours: float = None):
        """Actualiza el estado y horas reales de un proyecto"""
        update_data = {
            "status": status, 
            "updated_at": datetime.utcnow(),
            "progress_percentage": 100.0 if status == "completed" else 50.0
        }

        if actual_hours is not None:
            update_data["actual_total_hours"] = actual_hours

        self.analytics_collection.update_one(
            {"project_id": project_id},
            {"$set": update_data}
        )

    def get_analytics_metrics(self, days: int = 30):
        """Obtiene métricas agregadas para el dashboard"""
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = self.get_projects_since(start_date)

        if not projects:
            return {
                "total_projects": 0,
                "total_tasks": 0,
                "total_estimated_hours": 0,
                "completed_projects": 0,
                "pending_projects": 0,
                "in_progress_projects": 0,
                "average_tasks_per_project": 0,
                "average_hours_per_project": 0,
                "success_rate": 0
            }

        total_tasks = sum(project.get('total_tasks', 0) for project in projects)
        total_hours = sum(project.get('total_estimated_hours', 0) for project in projects)
        
        status_counts = Counter(project.get('status', 'pending') for project in projects)
        
        metrics = {
            "total_projects": len(projects),
            "total_tasks": total_tasks,
            "total_estimated_hours": round(total_hours, 2),
            "completed_projects": status_counts.get('completed', 0),
            "pending_projects": status_counts.get('pending', 0),
            "in_progress_projects": status_counts.get('in_progress', 0),
            "average_tasks_per_project": round(total_tasks / len(projects), 2) if projects else 0,
            "average_hours_per_project": round(total_hours / len(projects), 2) if projects else 0,
            "success_rate": round((status_counts.get('completed', 0) / len(projects)) * 100, 2) if projects else 0
        }
        
        return metrics