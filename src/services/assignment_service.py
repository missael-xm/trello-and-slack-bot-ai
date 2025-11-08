# src/services/assignment_service.py
from models.team_members import TeamMember, TeamMetrics, AssignmentResult, SkillLevel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random

class AssignmentService:
    """
    Servicio para asignación inteligente de tareas basado en:
    - Disponibilidad actual
    - Habilidades requeridas
    - Complejidad de tarea
    - Historial de desempeño
    - Carga de trabajo equitativa
    """
    
    def __init__(self):
        self.team_members: Dict[str, TeamMember] = {}
        self._initialize_sample_team()
    
    def _initialize_sample_team(self):
        """Inicializar equipo de ejemplo"""
        sample_team = [
            TeamMember(
                slack_id="U09ER0ZG9EH",  # Carlos
                name="Carlos Chilque",
                email="carlos@empresa.com",
                skills=["React", "Node.js", "Python", "MongoDB", "FastAPI", "TypeScript"],
                skill_level=SkillLevel.SENIOR,
                max_tasks=8,
                weekly_capacity=40,
                specialization=["backend", "fullstack"]
            ),
            TeamMember(
                slack_id="U1234567890",
                name="Ana García", 
                email="ana@empresa.com",
                skills=["React", "JavaScript", "CSS", "UI/UX", "Figma"],
                skill_level=SkillLevel.MID,
                max_tasks=6,
                weekly_capacity=35,
                specialization=["frontend", "design"]
            ),
            TeamMember(
                slack_id="U2345678901",
                name="Luis Martínez",
                email="luis@empresa.com",
                skills=["Python", "Django", "PostgreSQL", "Docker", "AWS"],
                skill_level=SkillLevel.SENIOR,
                max_tasks=7,
                weekly_capacity=38,
                specialization=["backend", "devops"]
            ),
            TeamMember(
                slack_id="U3456789012", 
                name="Maria Lopez",
                email="maria@empresa.com",
                skills=["JavaScript", "Vue.js", "CSS", "React", "Testing"],
                skill_level=SkillLevel.MID,
                max_tasks=5,
                weekly_capacity=32,
                specialization=["frontend", "testing"]
            )
        ]
        
        for member in sample_team:
            self.team_members[member.slack_id] = member
    
    def assign_task(self, task: Dict, required_skills: List[str], complexity: str, estimated_hours: float) -> AssignmentResult:
        """
        Asigna una tarea al miembro más adecuado del equipo
        """
        available_members = self._get_available_members()
        
        if not available_members:
            return self._get_fallback_assignment(task)
        
        # Calcular score para cada miembro disponible
        member_scores = []
        for member in available_members:
            score = self._calculate_assignment_score(member, task, required_skills, complexity, estimated_hours)
            member_scores.append((member, score))
        
        # Ordenar por score descendente
        member_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Seleccionar el mejor candidato
        best_member, best_score = member_scores[0]
        
        # Actualizar métricas del miembro
        self._update_member_metrics(best_member, estimated_hours)
        
        return AssignmentResult(
            assigned_to=best_member.name,
            slack_id=best_member.slack_id,
            member_name=best_member.name,
            confidence_score=best_score,
            reason=self._get_assignment_reason(best_member, best_score, required_skills),
            estimated_completion_time=estimated_hours
        )
    
    def _get_available_members(self) -> List[TeamMember]:
        """Obtener miembros disponibles (no exceden su capacidad)"""
        available = []
        for member in self.team_members.values():
            if (member.available and 
                member.current_tasks < member.max_tasks and
                member.current_weekly_hours < member.weekly_capacity * 0.8):  # 80% de capacidad máxima
                available.append(member)
        return available
    
    def _calculate_assignment_score(self, member: TeamMember, task: Dict, 
                                  required_skills: List[str], complexity: str, 
                                  estimated_hours: float) -> float:
        """Calcular score de asignación (0-100)"""
        score = 0.0
        
        # 1. Coincidencia de habilidades (40%)
        skill_match = self._calculate_skill_match(member.skills, required_skills)
        score += skill_match * 0.4
        
        # 2. Nivel vs complejidad (25%)
        level_match = self._calculate_level_match(member.skill_level, complexity)
        score += level_match * 0.25
        
        # 3. Carga de trabajo (20%)
        workload_score = self._calculate_workload_score(member)
        score += workload_score * 0.2
        
        # 4. Desempeño histórico (15%)
        performance_score = self._calculate_performance_score(member)
        score += performance_score * 0.15
        
        return min(score * 100, 100)  # Convertir a porcentaje
    
    def _calculate_skill_match(self, member_skills: List[str], required_skills: List[str]) -> float:
        """Calcular coincidencia de habilidades"""
        if not required_skills:
            return 0.5  # Valor neutral si no hay habilidades requeridas
        
        matches = sum(1 for skill in required_skills if skill in member_skills)
        return matches / len(required_skills)
    
    def _calculate_level_match(self, member_level: SkillLevel, complexity: str) -> float:
        """Calcular coincidencia de nivel vs complejidad"""
        level_weights = {
            SkillLevel.JUNIOR: {"simple": 1.0, "moderada": 0.6, "compleja": 0.2, "muy_compleja": 0.0},
            SkillLevel.MID: {"simple": 0.8, "moderada": 1.0, "compleja": 0.7, "muy_compleja": 0.3},
            SkillLevel.SENIOR: {"simple": 0.6, "moderada": 0.8, "compleja": 1.0, "muy_compleja": 0.8},
            SkillLevel.EXPERT: {"simple": 0.4, "moderada": 0.6, "compleja": 0.8, "muy_compleja": 1.0}
        }
        
        complexity_map = {
            "simple": "simple",
            "moderada": "moderada", 
            "compleja": "compleja",
            "muy_compleja": "muy_compleja"
        }
        
        return level_weights.get(member_level, {}).get(complexity_map.get(complexity, "moderada"), 0.5)
    
    def _calculate_workload_score(self, member: TeamMember) -> float:
        """Calcular score basado en carga de trabajo"""
        # Menos carga = mejor score
        task_ratio = member.current_tasks / member.max_tasks
        hours_ratio = member.current_weekly_hours / member.weekly_capacity
        
        # Promedio de ambos ratios
        avg_ratio = (task_ratio + hours_ratio) / 2
        return 1.0 - avg_ratio  # Invertir: menos carga = score más alto
    
    def _calculate_performance_score(self, member: TeamMember) -> float:
        """Calcular score basado en desempeño histórico"""
        base_score = member.success_rate / 100.0  # Convertir porcentaje a decimal
        
        # Ajustar por tiempo de completación (menos tiempo = mejor)
        time_bonus = 0.0
        if member.avg_completion_time > 0:
            # Normalizar: menos de 10 horas = bonus, más de 40 horas = penalización
            if member.avg_completion_time <= 10:
                time_bonus = 0.2
            elif member.avg_completion_time <= 20:
                time_bonus = 0.1
            elif member.avg_completion_time > 40:
                time_bonus = -0.1
        
        return min(base_score + time_bonus, 1.0)
    
    def _update_member_metrics(self, member: TeamMember, estimated_hours: float):
        """Actualizar métricas del miembro después de asignación"""
        member.current_tasks += 1
        member.current_weekly_hours += estimated_hours
        member.updated_at = datetime.utcnow()
        
        # Si excede ciertos límites, marcar como muy ocupado temporalmente
        if (member.current_tasks >= member.max_tasks * 0.9 or 
            member.current_weekly_hours >= member.weekly_capacity * 0.9):
            member.available = False
    
    def _get_assignment_reason(self, member: TeamMember, score: float, required_skills: List[str]) -> str:
        """Generar razón de asignación"""
        reasons = []
        
        if score >= 80:
            reasons.append("alta compatibilidad de habilidades")
        elif score >= 60:
            reasons.append("buen balance de habilidades y disponibilidad")
        else:
            reasons.append("asignación por disponibilidad")
        
        matching_skills = [skill for skill in required_skills if skill in member.skills]
        if matching_skills:
            reasons.append(f"coincide en: {', '.join(matching_skills[:3])}")
        
        if member.current_tasks < member.max_tasks * 0.5:
            reasons.append("buena disponibilidad actual")
        
        return "; ".join(reasons)
    
    def _get_fallback_assignment(self, task: Dict) -> AssignmentResult:
        """Asignación de fallback cuando no hay miembros disponibles"""
        # Buscar el miembro con menor carga
        least_loaded = min(self.team_members.values(), 
                          key=lambda m: m.current_tasks + m.current_weekly_hours)
        
        return AssignmentResult(
            assigned_to=least_loaded.name,
            slack_id=least_loaded.slack_id,
            member_name=least_loaded.name,
            confidence_score=0.3,
            reason="asignación de emergencia - todos los miembros están muy ocupados",
            estimated_completion_time=0.0
        )
    
    def get_team_metrics(self) -> TeamMetrics:
        """Obtener métricas del equipo"""
        total_members = len(self.team_members)
        available_members = len(self._get_available_members())
        
        total_tasks = sum(m.current_tasks for m in self.team_members.values())
        total_completed = sum(m.completed_tasks for m in self.team_members.values())
        
        completion_rate = (total_completed / (total_tasks + total_completed)) * 100 if (total_tasks + total_completed) > 0 else 0
        
        # Distribución de carga
        workload_distribution = {}
        for member in self.team_members.values():
            workload_pct = (member.current_tasks / member.max_tasks) * 100
            workload_distribution[member.slack_id] = workload_pct
        
        # Cobertura de habilidades
        skill_coverage = {}
        all_skills = set()
        for member in self.team_members.values():
            all_skills.update(member.skills)
        
        for skill in all_skills:
            count = sum(1 for member in self.team_members.values() if skill in member.skills)
            skill_coverage[skill] = count
        
        # Miembros muy ocupados
        busy_members = [
            member.slack_id for member in self.team_members.values()
            if member.current_tasks >= member.max_tasks * 0.8
        ]
        
        return TeamMetrics(
            total_members=total_members,
            available_members=available_members,
            total_tasks_assigned=total_tasks,
            total_tasks_completed=total_completed,
            completion_rate=completion_rate,
            avg_completion_time=0.0,  # Se calcularía con datos reales
            workload_distribution=workload_distribution,
            skill_coverage=skill_coverage,
            busy_members=busy_members
        )
    
    def complete_task(self, slack_id: str, actual_hours: float, success: bool = True):
        """Marcar tarea como completada"""
        if slack_id in self.team_members:
            member = self.team_members[slack_id]
            member.current_tasks = max(0, member.current_tasks - 1)
            member.current_weekly_hours = max(0, member.current_weekly_hours - actual_hours)
            member.completed_tasks += 1
            
            # Actualizar métricas de desempeño
            if success:
                # Actualizar tiempo promedio de completación
                if member.avg_completion_time == 0:
                    member.avg_completion_time = actual_hours
                else:
                    member.avg_completion_time = (member.avg_completion_time + actual_hours) / 2
                
                # Actualizar tasa de éxito
                total_attempts = member.completed_tasks
                member.success_rate = (member.success_rate * (total_attempts - 1) + 100) / total_attempts
            
            # Reactivar disponibilidad si estaba marcado como no disponible
            if not member.available and member.current_tasks < member.max_tasks * 0.8:
                member.available = True
            
            member.updated_at = datetime.utcnow()