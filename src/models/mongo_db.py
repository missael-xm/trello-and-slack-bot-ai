# src/models/mongo_db.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime
from enum import Enum
from pydantic.json_schema import SkipJsonSchema

class PyObjectId(ObjectId):
    """Wrapper para ObjectId de MongoDB para compatibilidad con Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        return {
            'type': 'str',
            'from_attributes': True,
        }

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return handler(core_schema={'type': 'str'})

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
    optimistic: float = Field(description="Estimación optimista en horas")
    realistic: float = Field(description="Estimación realista en horas")
    pessimistic: float = Field(description="Estimación pesimista en horas")

# Modelo para tareas individuales con metadatos
class TaskDetail(BaseModel):
    description: str = Field(description="Descripción detallada de la tarea")
    category: TaskCategory = Field(description="Categoría de la tarea")
    priority: TaskPriority = Field(description="Prioridad de la tarea")
    complexity: TaskComplexity = Field(description="Complejidad de la tarea")
    time_estimate: TimeEstimate = Field(description="Estimación de tiempo en horas")
    dependencies: List[str] = Field(default_factory=list, description="IDs de tareas dependientes")
    required_skills: List[str] = Field(default_factory=list, description="Habilidades técnicas requeridas")
    risk_level: str = Field(description="Nivel de riesgo (bajo/medio/alto)")
    assigned_to: Optional[str] = Field(default=None, description="Usuario asignado")
    due_date: Optional[datetime] = Field(default=None, description="Fecha límite")
    actual_hours: Optional[float] = Field(default=None, description="Horas reales trabajadas")
    status: str = Field(default="pending", description="Estado de la tarea")

# Modelo principal para Trello Cards (existente)
class TrelloCard(BaseModel):
    """Modelo para documentos MongoDB de cards de Trello"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    card_id: str = Field(description="ID de la card de Trello")
    comment_history: List[str] = Field(default_factory=list, description="Historial de comentarios procesados")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    model_config = {
        'populate_by_name': True,  # Cambiado de allow_population_by_field_name
        'arbitrary_types_allowed': True,
        'json_encoders': {ObjectId: str},
        'json_schema_extra': {
            "example": {
                "card_id": "trello_card_123",
                "comment_history": ["comment1", "comment2"],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    }

    @validator('updated_at', pre=True, always=True)
    def update_timestamp(cls, v, values):
        return datetime.utcnow()

# Nuevo modelo para Analytics y Dashboard
class AnalyticsData(BaseModel):
    """Modelo para datos de analytics y métricas del dashboard"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    
    # Información básica del proyecto
    project_id: str = Field(description="ID único del proyecto")
    card_id: str = Field(description="ID de la card de Trello")
    card_title: str = Field(description="Título de la card")
    card_description: Optional[str] = Field(default=None, description="Descripción de la card")
    board_id: str = Field(description="ID del tablero de Trello")
    board_name: str = Field(description="Nombre del tablero")
    
    # Información de solicitud
    requested_by: str = Field(description="Usuario que solicitó las tareas")
    request_date: datetime = Field(description="Fecha de la solicitud")
    original_comment: str = Field(description="Comentario original que disparó el análisis")
    
    # Métricas generales del proyecto
    total_tasks: int = Field(description="Número total de tareas generadas")
    total_estimated_hours: float = Field(description="Horas totales estimadas")
    average_complexity: TaskComplexity = Field(description="Complejidad promedio del proyecto")
    highest_priority: TaskPriority = Field(description="Prioridad más alta del proyecto")
    risk_assessment: str = Field(description="Evaluación general de riesgo")
    
    # Distribuciones y categorizaciones
    category_distribution: Dict[TaskCategory, int] = Field(description="Distribución de tareas por categoría")
    priority_distribution: Dict[TaskPriority, int] = Field(description="Distribución de tareas por prioridad")
    complexity_distribution: Dict[TaskComplexity, int] = Field(description="Distribución de tareas por complejidad")
    
    # Lista detallada de tareas
    tasks: List[Dict[str, Any]] = Field(description="Lista de tareas con metadatos completos")
    
    # Habilidades y recursos requeridos
    required_skills: List[str] = Field(description="Habilidades técnicas únicas requeridas")
    skill_frequency: Dict[str, int] = Field(description="Frecuencia de cada habilidad requerida")
    
    # Estado y seguimiento
    status: ProjectStatus = Field(default=ProjectStatus.PENDING, description="Estado actual del proyecto")
    progress_percentage: float = Field(default=0.0, description="Porcentaje de completación (0-100)")
    
    # Fechas importantes
    estimated_start_date: Optional[datetime] = Field(default=None, description="Fecha estimada de inicio")
    estimated_end_date: Optional[datetime] = Field(default=None, description="Fecha estimada de finalización")
    actual_start_date: Optional[datetime] = Field(default=None, description="Fecha real de inicio")
    actual_end_date: Optional[datetime] = Field(default=None, description="Fecha real de finalización")
    
    # Métricas de ejecución
    actual_total_hours: Optional[float] = Field(default=None, description="Horas reales totales trabajadas")
    budget_estimated: Optional[float] = Field(default=None, description="Presupuesto estimado")
    budget_actual: Optional[float] = Field(default=None, description="Presupuesto real")
    
    # Metadatos del sistema
    ai_model_used: str = Field(description="Modelo de IA utilizado para el análisis")
    processing_time: float = Field(description="Tiempo de procesamiento en segundos")
    confidence_score: float = Field(description="Puntuación de confianza del análisis (0-1)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_analysis_update: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        'populate_by_name': True,
        'arbitrary_types_allowed': True,
        'json_encoders': {ObjectId: str},
        'json_schema_extra': {
            "example": {
                "project_id": "proj_2024_001",
                "card_id": "trello_card_abc123",
                "card_title": "Sistema de Carrito de Compras",
                "card_description": "Implementar carrito de compras con React y Node.js",
                "board_id": "board_123",
                "board_name": "Desarrollo Ecommerce",
                "requested_by": "carloschilque",
                "request_date": datetime.utcnow(),
                "original_comment": "@carloschilque necesitamos un carrito de compras funcional",
                "total_tasks": 8,
                "total_estimated_hours": 56.5,
                "average_complexity": TaskComplexity.MODERATE,
                "highest_priority": TaskPriority.HIGH,
                "risk_assessment": "medio",
                "category_distribution": {
                    TaskCategory.FRONTEND: 4,
                    TaskCategory.BACKEND: 3,
                    TaskCategory.DATABASE: 1
                },
                "priority_distribution": {
                    TaskPriority.HIGH: 3,
                    TaskPriority.MEDIUM: 4,
                    TaskPriority.LOW: 1
                },
                "complexity_distribution": {
                    TaskComplexity.MODERATE: 5,
                    TaskComplexity.COMPLEX: 2,
                    TaskComplexity.SIMPLE: 1
                },
                "tasks": [
                    {
                        "description": "Implementar componente Cart en React",
                        "category": TaskCategory.FRONTEND,
                        "priority": TaskPriority.HIGH,
                        "complexity": TaskComplexity.MODERATE,
                        "time_estimate": {
                            "optimistic": 4.0,
                            "realistic": 6.0,
                            "pessimistic": 8.0
                        },
                        "dependencies": [],
                        "required_skills": ["React", "TypeScript", "CSS"],
                        "risk_level": "bajo",
                        "assigned_to": None,
                        "due_date": None,
                        "actual_hours": None,
                        "status": "pending"
                    }
                ],
                "required_skills": ["React", "Node.js", "MongoDB", "TypeScript", "CSS"],
                "skill_frequency": {
                    "React": 4,
                    "Node.js": 3,
                    "TypeScript": 3,
                    "CSS": 2,
                    "MongoDB": 1
                },
                "status": ProjectStatus.PENDING,
                "progress_percentage": 0.0,
                "ai_model_used": "gpt-4-turbo-preview",
                "processing_time": 3.2,
                "confidence_score": 0.87,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_analysis_update": datetime.utcnow()
            }
        }
    }

    @validator('updated_at', pre=True, always=True)
    def update_timestamp(cls, v, values):
        return datetime.utcnow()

    @validator('progress_percentage')
    def validate_progress(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress percentage must be between 0 and 100')
        return v

    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Confidence score must be between 0 and 1')
        return v

# Modelo para métricas agregadas (para el dashboard)
class AggregatedMetrics(BaseModel):
    """Modelo para métricas agregadas para el dashboard"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    
    # Período de análisis
    period_start: datetime = Field(description="Inicio del período de análisis")
    period_end: datetime = Field(description="Fin del período de análisis")
    period_type: str = Field(description="Tipo de período (daily, weekly, monthly)")
    
    # Métricas de proyectos
    total_projects: int = Field(description="Total de proyectos en el período")
    completed_projects: int = Field(description="Proyectos completados")
    in_progress_projects: int = Field(description="Proyectos en progreso")
    pending_projects: int = Field(description="Proyectos pendientes")
    
    # Métricas de tareas
    total_tasks_generated: int = Field(description="Total de tareas generadas")
    completed_tasks: int = Field(description="Tareas completadas")
    average_tasks_per_project: float = Field(description="Promedio de tareas por proyecto")
    
    # Métricas de tiempo
    total_estimated_hours: float = Field(description="Horas totales estimadas")
    total_actual_hours: Optional[float] = Field(default=None, description="Horas reales trabajadas")
    average_estimation_accuracy: Optional[float] = Field(default=None, description="Precisión promedio de estimaciones")
    
    # Distribuciones
    category_totals: Dict[TaskCategory, int] = Field(description="Total por categoría")
    priority_totals: Dict[TaskPriority, int] = Field(description="Total por prioridad")
    complexity_totals: Dict[TaskComplexity, int] = Field(description="Total por complejidad")
    
    # Habilidades más demandadas
    top_skills: List[Dict[str, Any]] = Field(description="Habilidades más requeridas")
    
    # Eficiencia del sistema
    average_processing_time: float = Field(description="Tiempo promedio de procesamiento")
    total_ai_requests: int = Field(description="Total de requests a IA")
    success_rate: float = Field(description="Tasa de éxito del procesamiento")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        'populate_by_name': True,
        'arbitrary_types_allowed': True,
        'json_encoders': {ObjectId: str}
    }

# Modelo para configuración del dashboard
class DashboardConfig(BaseModel):
    """Modelo para configuración del dashboard"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    
    user_id: str = Field(description="ID del usuario")
    chart_configs: Dict[str, Any] = Field(description="Configuraciones de gráficas")
    default_period: str = Field(default="monthly", description="Período por defecto")
    visible_metrics: List[str] = Field(description="Métricas visibles en el dashboard")
    refresh_interval: int = Field(default=300, description="Intervalo de refresco en segundos")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        'populate_by_name': True,
        'arbitrary_types_allowed': True,
        'json_encoders': {ObjectId: str}
    }

# Exportar todos los modelos
__all__ = [
    'PyObjectId',
    'TaskPriority', 
    'TaskComplexity',
    'TaskCategory',
    'ProjectStatus',
    'TimeEstimate',
    'TaskDetail',
    'TrelloCard',
    'AnalyticsData',
    'AggregatedMetrics',
    'DashboardConfig'
]