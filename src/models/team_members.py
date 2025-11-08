# src/models/team_members.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class SkillLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"

class TeamMember(BaseModel):
    """Modelo para miembros del equipo de desarrollo"""
    slack_id: str = Field(..., description="ID de Slack del miembro")
    name: str = Field(..., description="Nombre del miembro")
    email: str = Field(..., description="Email del miembro")
    skills: List[str] = Field(..., description="Habilidades técnicas")
    skill_level: SkillLevel = Field(..., description="Nivel de habilidad")
    max_tasks: int = Field(..., description="Máximo de tareas simultáneas")
    current_tasks: int = Field(default=0, description="Tareas actualmente asignadas")
    completed_tasks: int = Field(default=0, description="Tareas completadas total")
    weekly_capacity: int = Field(..., description="Capacidad semanal en horas")
    current_weekly_hours: float = Field(default=0.0, description="Horas asignadas esta semana")
    
    # Métricas de desempeño
    avg_completion_time: float = Field(default=0.0, description="Tiempo promedio de completación en horas")
    success_rate: float = Field(default=0.0, description="Tasa de éxito en completación")
    specialization: List[str] = Field(default_factory=list, description="Especializaciones")
    
    # Disponibilidad
    available: bool = Field(default=True, description="Disponible para nuevas tareas")
    available_from: Optional[datetime] = Field(None, description="Disponible desde")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True

class TeamMetrics(BaseModel):
    """Métricas del equipo"""
    total_members: int
    available_members: int
    total_tasks_assigned: int
    total_tasks_completed: int
    completion_rate: float
    avg_completion_time: float
    workload_distribution: Dict[str, float]  # slack_id -> porcentaje
    skill_coverage: Dict[str, int]  # skill -> cantidad de miembros
    busy_members: List[str]  # IDs de miembros con alta carga

class AssignmentResult(BaseModel):
    """Resultado de asignación de tarea"""
    assigned_to: str
    slack_id: str
    member_name: str
    confidence_score: float
    reason: str
    estimated_completion_time: float