# src/database/mongo_db.py - CONEXIÓN ROBUSTA
from pymongo import MongoClient
from pymongo.collection import Collection
from models.mongo_db import TrelloCard
from utils.config import mongodb_uri
from typing import Union
import certifi
from datetime import datetime, timedelta
from collections import Counter
import sys

class MongoDB():
    """
    Cliente de MongoDB con soporte para colección de equipo y manejo robusto de conexión.
    """
    def __init__(self) -> None:
        self.client = None
        self.db = None
        
        # 1. Configuración de opciones de conexión
        # Aumentamos timeout a 30s para evitar falsos negativos en conexiones lentas
        connection_options = {
            "serverSelectionTimeoutMS": 30000,
            "connectTimeoutMS": 30000,
            "socketTimeoutMS": 30000,
        }

        # 2. Intentos de conexión
        print(f"🔄 Conectando a MongoDB...")
        
        # Intento 1: Estándar con certifi (Recomendado para Atlas)
        try:
            self.client = MongoClient(
                mongodb_uri,
                tlsCAFile=certifi.where(),
                **connection_options
            )
            # Forzar verificación de conexión
            self.client.admin.command('ping')
            print("✅ MongoDB conectado (Modo Seguro con Certifi)")
        except Exception as e1:
            print(f"⚠️ Falló conexión segura: {e1}")
            
            # Intento 2: Inseguro (Saltar verificación SSL - Útil para debug/Windows)
            try:
                print("🔄 Reintentando sin verificación SSL...")
                self.client = MongoClient(
                    mongodb_uri,
                    tlsAllowInvalidCertificates=True,
                    **connection_options
                )
                self.client.admin.command('ping')
                print("✅ MongoDB conectado (Modo Inseguro SSL)")
            except Exception as e2:
                print(f"❌ Falló conexión remota: {e2}")
                
                # Intento 3: Local (Fallback)
                print("🔄 Intentando MongoDB Local...")
                try:
                    self.client = MongoClient("mongodb://localhost:27017/", **connection_options)
                    self.client.admin.command('ping')
                    print("✅ MongoDB Local conectado")
                except Exception as e3:
                    print(f"❌ Error crítico: No se pudo conectar a ninguna base de datos. {e3}")
                    self.client = None

        # 3. Inicializar colecciones si hay cliente
        if self.client:
            try:
                self.db = self.client.get_database("trello_db") # Usar get_database para mejor compatibilidad
                self.collection = self.db["card"]
                self.analytics_collection = self.db["analytics"]
                self.team_collection = self.db["team_members"]
            except Exception as e:
                print(f"❌ Error obteniendo base de datos: {e}")
                self.collection = None
                self.analytics_collection = None
                self.team_collection = None
        else:
            self.collection = None
            self.analytics_collection = None
            self.team_collection = None

    def init_db_and_get_collection(self) -> Union[None, Collection]:
        """Devuelve la colección de cards"""
        return self.collection

    def data_insert(self, card_id: str = "", comment_history: list = []):
        if not self.collection: return None
        try:
            card_data = self.data_select(card_id=card_id)
            if card_data is not None:
                return card_data

            data = self.collection.insert_one({
                "card_id": card_id,
                "comment_history": comment_history
            })
            return None
        except Exception as e:
            print(f"Error en data_insert: {e}")
            return None

    def data_update(self, card_id: str = "", comment_history: list = []):
        if not self.collection: return
        try:
            self.collection.update_one(
                {"card_id": card_id},
                {"$set": {"comment_history": comment_history}}
            )
        except Exception as e:
            print(f"Error en data_update: {e}")

    def data_select(self, card_id: str = "") -> Union[None, TrelloCard]:
        if not self.collection: return None
        try:
            data = self.collection.find_one({"card_id": card_id})
            if data is not None:
                return TrelloCard(
                    _id=str(data["_id"]),
                    card_id=data["card_id"],
                    comment_history=data["comment_history"],
                )
            return None
        except Exception as e:
            print(f"Error en data_select: {e}")
            return None

    def get_projects_since(self, start_date: datetime):
        if not self.analytics_collection: return []
        return list(self.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }).sort("request_date", -1))

    def get_all_projects(self):
        if not self.analytics_collection: return []
        return list(self.analytics_collection.find().sort("request_date", -1))

    def get_project_by_id(self, project_id: str):
        if not self.analytics_collection: return None
        return self.analytics_collection.find_one({"project_id": project_id})

    def update_project_status(self, project_id: str, status: str, actual_hours: float = None):
        if not self.analytics_collection: return
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
        if not self.analytics_collection:
            return {"total_projects": 0, "total_tasks": 0, "success_rate": 0} # Return dummy
            
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