# src/models/analytics.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

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

class TimeEstimate(BaseModel):
    optimistic: float = Field(description="Estimación optimista en horas")
    realistic: float = Field(description="Estimación realista en horas")
    pessimistic: float = Field(description="Estimación pesimista en horas")

class AnalyticsTask(BaseModel):
    description: str = Field(description="Descripción de la tarea")
    category: TaskCategory = Field(description="Categoría de la tarea")
    priority: TaskPriority = Field(description="Prioridad de la tarea")
    complexity: TaskComplexity = Field(description="Complejidad de la tarea")
    time_estimate: TimeEstimate = Field(description="Estimación de tiempo")
    dependencies: List[str] = Field(default_factory=list, description="Tareas dependientes")
    required_skills: List[str] = Field(default_factory=list, description="Habilidades requeridas")
    risk_level: str = Field(description="Nivel de riesgo (bajo/medio/alto)")

class ProjectAnalytics(BaseModel):
    project_id: str = Field(description="ID del proyecto en Trello")
    card_id: str = Field(description="ID de la card en Trello")
    card_title: str = Field(description="Título de la card")
    requested_by: str = Field(description="Usuario que solicitó las tareas")
    request_date: datetime = Field(description="Fecha de la solicitud")
    total_tasks: int = Field(description="Número total de tareas generadas")
    total_estimated_hours: float = Field(description="Horas totales estimadas")
    average_complexity: str = Field(description="Complejidad promedio")
    highest_priority: TaskPriority = Field(description="Prioridad más alta")
    tasks: List[AnalyticsTask] = Field(description="Lista de tareas con metadatos")
    status: str = Field(default="pending", description="Estado del proyecto")
    completion_date: Optional[datetime] = Field(default=None, description="Fecha de completación")
    actual_hours: Optional[float] = Field(default=None, description="Horas reales trabajadas")