# src/models/mongo_db.py - COMPATIBLE CON PYDANTIC v1
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from enum import Enum

class PyObjectId(ObjectId):
    """Wrapper para ObjectId de MongoDB para compatibilidad con Pydantic v1"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Enums para categorización
class TaskPriority(str, Enum):
    LOW = "baja"
    MEDIUM = "media" 
    HIGH = "alta"
    CRITICAL = "crítica"

class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderada"
    COMPLEX = "compleja"
    VERY_COMPLEX = "muy_compleja"

class TaskCategory(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "base_de_datos"
    DESIGN = "diseño"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "mantenimiento"
    DOCUMENTATION = "documentación"
    OTHER = "otro"

class ProjectStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Modelo para estimaciones de tiempo
class TimeEstimate(BaseModel):
    optimistic: float = Field(..., description="Estimación optimista en horas")
    realistic: float = Field(..., description="Estimación realista en horas")
    pessimistic: float = Field(..., description="Estimación pesimista en horas")

# Modelo para tareas individuales con metadatos
class TaskDetail(BaseModel):
    description: str = Field(..., description="Descripción detallada de la tarea")
    category: TaskCategory = Field(..., description="Categoría de la tarea")
    priority: TaskPriority = Field(..., description="Prioridad de la tarea")
    complexity: TaskComplexity = Field(..., description="Complejidad de la tarea")
    time_estimate: TimeEstimate = Field(..., description="Estimación de tiempo en horas")
    dependencies: List[str] = Field(default_factory=list, description="IDs de tareas dependientes")
    required_skills: List[str] = Field(default_factory=list, description="Habilidades técnicas requeridas")
    risk_level: str = Field(..., description="Nivel de riesgo (bajo/medio/alto)")
    assigned_to: Optional[str] = Field(None, description="Usuario asignado")
    due_date: Optional[datetime] = Field(None, description="Fecha límite")
    actual_hours: Optional[float] = Field(None, description="Horas reales trabajadas")
    status: str = Field(default="pending", description="Estado de la tarea")

# Modelo principal para Trello Cards
class TrelloCard(BaseModel):
    """Modelo para documentos MongoDB de cards de Trello"""
    id: Optional[str] = Field(None, alias="_id")
    card_id: str = Field(..., description="ID de la card de Trello")
    comment_history: List[str] = Field(default_factory=list, description="Historial de comentarios procesados")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('updated_at', pre=True, always=True)
    def update_timestamp(cls, v):
        return datetime.utcnow()

# Modelo simplificado para Analytics
class AnalyticsData(BaseModel):
    """Modelo simplificado para datos de analytics"""
    id: Optional[str] = Field(None, alias="_id")
    project_id: str = Field(..., description="ID único del proyecto")
    card_id: str = Field(..., description="ID de la card de Trello")
    card_title: str = Field(..., description="Título de la card")
    requested_by: str = Field(..., description="Usuario que solicitó las tareas")
    request_date: datetime = Field(..., description="Fecha de la solicitud")
    total_tasks: int = Field(..., description="Número total de tareas generadas")
    total_estimated_hours: float = Field(..., description="Horas totales estimadas")
    average_complexity: str = Field(..., description="Complejidad promedio")
    highest_priority: str = Field(..., description="Prioridad más alta")
    tasks: List[Dict[str, Any]] = Field(default_factory=list, description="Lista de tareas")
    status: str = Field(default="pending", description="Estado del proyecto")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

    @validator('updated_at', pre=True, always=True)
    def update_timestamp(cls, v):
        return datetime.utcnow()

# Exportar modelos principales
__all__ = [
    'PyObjectId',
    'TaskPriority', 
    'TaskComplexity',
    'TaskCategory',
    'ProjectStatus',
    'TimeEstimate',
    'TaskDetail',
    'TrelloCard',
    'AnalyticsData'
]