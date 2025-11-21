# src/services/assignment_service.py
from models.team_members import TeamMember, TeamMetrics, AssignmentResult, SkillLevel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database.mongo_db import MongoDB
import random

class AssignmentService:
    """
    Servicio de asignación inteligente CON CÁLCULO DE MÉTRICAS HISTÓRICAS.
    Actualiza promedios ponderados al completar tareas.
    """
    
    def __init__(self):
        self.db = MongoDB()
        self.team_members: Dict[str, TeamMember] = {}
        self._load_team_data()
    
    def _load_team_data(self):
        """Carga miembros desde BD o inicializa por defecto"""
        loaded = False
        if self.db.team_collection is not None:
            try:
                stored_members = list(self.db.team_collection.find())
                if stored_members:
                    print(f"📂 Cargando {len(stored_members)} miembros desde MongoDB")
                    for doc in stored_members:
                        if '_id' in doc: del doc['_id']
                        if 'skill_level' in doc and isinstance(doc['skill_level'], str):
                            try:
                                for sl in SkillLevel:
                                    if sl.value == doc['skill_level']:
                                        doc['skill_level'] = sl
                                        break
                            except: pass
                        member = TeamMember(**doc)
                        self.team_members[member.slack_id] = member
                    loaded = True
            except Exception as e:
                print(f"⚠️ Error cargando equipo de BD: {e}")
        
        if not loaded:
            print("⚠️ Inicializando equipo por defecto")
            self._initialize_sample_team()
            self._save_all_members()

    def _save_all_members(self):
        if self.db.team_collection is None: return
        for member in self.team_members.values():
            self._persist_member(member)

    def _persist_member(self, member: TeamMember):
        if self.db.team_collection is None: return
        try:
            data = member.dict()
            if isinstance(data.get('skill_level'), (SkillLevel, object)):
                try:
                    if hasattr(data['skill_level'], 'value'):
                        data['skill_level'] = data['skill_level'].value
                except: pass
            
            self.db.team_collection.update_one(
                {"slack_id": member.slack_id},
                {"$set": data},
                upsert=True
            )
        except Exception as e:
            print(f"❌ Error guardando miembro {member.name}: {e}")

    def _initialize_sample_team(self):
        sample_team = [
            TeamMember(slack_id="U09ER0ZG9EH", name="Carlos Chilque", email="carlos@empresa.com", skills=["React", "Node.js", "Python", "MongoDB", "FastAPI", "TypeScript"], skill_level=SkillLevel.SENIOR, max_tasks=8, weekly_capacity=40, current_tasks=5, current_weekly_hours=28.0, completed_tasks=45, success_rate=98.5, avg_completion_time=3.5, specialization=["backend", "fullstack"]),
            TeamMember(slack_id="U09U6KWK21K", name="Daniela Aduviri", email="daniela@outlook.com", skills=["React", "JavaScript", "CSS", "UI/UX", "Figma"], skill_level=SkillLevel.MID, max_tasks=6, weekly_capacity=35, current_tasks=2, current_weekly_hours=10.0, completed_tasks=32, success_rate=95.0, avg_completion_time=4.2, specialization=["frontend", "design"]),
            TeamMember(slack_id="U09UDEDJP60", name="Victor Flores", email="victor@usmp.pe", skills=["Python", "Django", "PostgreSQL", "Docker", "AWS"], skill_level=SkillLevel.SENIOR, max_tasks=7, weekly_capacity=38, current_tasks=6, current_weekly_hours=35.0, completed_tasks=58, success_rate=99.1, avg_completion_time=2.8, specialization=["backend", "devops"]),
            TeamMember(slack_id="U09UE36P6PN", name="Bryan Rodríguez", email="bryan@gmail.com", skills=["JavaScript", "Vue.js", "CSS", "React", "Testing"], skill_level=SkillLevel.MID, max_tasks=5, weekly_capacity=32, current_tasks=1, current_weekly_hours=4.0, completed_tasks=15, success_rate=88.5, avg_completion_time=5.1, specialization=["frontend", "testing"])
        ]
        for member in sample_team:
            if (member.current_tasks >= member.max_tasks * 0.9 or member.current_weekly_hours >= member.weekly_capacity * 0.9):
                member.available = False
            self.team_members[member.slack_id] = member

    # --- MÉTODOS DE ASIGNACIÓN ---
    def assign_batch(self, tasks: List[Dict]) -> AssignmentResult:
        if not self.team_members:
            return AssignmentResult(assigned_to="Unassigned", slack_id="UNKNOWN", member_name="Unassigned", confidence_score=0, reason="No team loaded", estimated_completion_time=0)

        total_hours = 0.0
        all_skills = set()
        max_complexity_val = 0
        complexity_map = {'simple': 1, 'moderada': 2, 'compleja': 3, 'muy_compleja': 4}
        highest_complexity = "moderada"

        for task in tasks:
            hours = 4.0
            if 'time_estimate' in task:
                val = task['time_estimate']
                if isinstance(val, (int, float)): hours = float(val)
                elif isinstance(val, dict): hours = float(val.get('realistic', 4.0))
            total_hours += hours

            task_skills = task.get('required_skills', [])
            if isinstance(task_skills, list): all_skills.update(task_skills)
            elif isinstance(task_skills, str): all_skills.add(task_skills)

            comp = task.get('complexity', 'moderada')
            val = complexity_map.get(comp, 2)
            if val > max_complexity_val:
                max_complexity_val = val
                highest_complexity = comp

        available_members = self._get_available_members()
        if not available_members:
            fallback = self._get_fallback_assignment({"description": "Batch tasks"})
            if fallback and fallback.slack_id in self.team_members:
                member = self.team_members[fallback.slack_id]
                self._update_member_metrics(member, total_hours, count=len(tasks))
            return fallback

        member_scores = []
        required_skills_list = list(all_skills)
        for member in available_members:
            score = self._calculate_assignment_score(member, {"description": "Batch"}, required_skills_list, highest_complexity, total_hours)
            member_scores.append((member, score))

        member_scores.sort(key=lambda x: x[1], reverse=True)
        best_member, best_score = member_scores[0]
        self._update_member_metrics(best_member, total_hours, count=len(tasks))

        return AssignmentResult(
            assigned_to=best_member.name, slack_id=best_member.slack_id, member_name=best_member.name,
            confidence_score=best_score, reason=f"Mejor candidato para {len(tasks)} tareas ({total_hours}h)",
            estimated_completion_time=total_hours
        )
    
    # --- MÉTODO CORREGIDO Y MEJORADO ---
    def complete_task(self, slack_id: str, actual_hours: float, task_count: int = 1, success: bool = True):
        """
        Actualiza métricas históricas (Promedio tiempo, Success Rate) y libera carga.
        Usa promedios ponderados para mayor precisión.
        """
        if slack_id in self.team_members:
            member = self.team_members[slack_id]
            
            print(f"📉 Actualizando métricas de {member.name}: +{task_count} tareas, {actual_hours}h")
            
            # 1. Guardar estado previo para cálculos
            prev_completed = member.completed_tasks
            prev_avg_time = member.avg_completion_time
            prev_success_rate = member.success_rate
            
            # 2. Liberar carga actual
            member.current_tasks = max(0, member.current_tasks - task_count)
            member.current_weekly_hours = max(0, member.current_weekly_hours - actual_hours)
            
            # 3. Actualizar total completadas
            member.completed_tasks += task_count
            total_now = member.completed_tasks
            
            if total_now > 0:
                # 4. Recalcular Tiempo Promedio (Moving Average)
                # (Promedio Anterior * Cantidad Anterior) + Nuevas Horas Totales / Nueva Cantidad
                prev_total_time = prev_avg_time * prev_completed
                # Calculamos el promedio de horas POR TAREA para este lote
                # Nota: avg_completion_time suele ser horas/tarea. 
                new_avg_time = (prev_total_time + actual_hours) / total_now
                member.avg_completion_time = new_avg_time

                # 5. Recalcular Success Rate (Moving Average)
                prev_total_score = prev_success_rate * prev_completed
                # Puntos del lote actual (100 si éxito, 0 si fallo) * cantidad de tareas
                batch_score = (100 * task_count) if success else 0
                new_success_rate = (prev_total_score + batch_score) / total_now
                member.success_rate = new_success_rate
            
            # 6. Verificar disponibilidad
            threshold_tasks = member.max_tasks * 0.8
            threshold_hours = member.weekly_capacity * 0.8
            
            if not member.available:
                if member.current_tasks < threshold_tasks and member.current_weekly_hours < threshold_hours:
                    member.available = True
                    print(f"✅ {member.name} vuelve a estar DISPONIBLE")
            
            member.updated_at = datetime.utcnow()
            self._persist_member(member)

    def _update_member_metrics(self, member: TeamMember, estimated_hours: float, count: int = 1):
        member.current_tasks += count
        member.current_weekly_hours += estimated_hours
        member.updated_at = datetime.utcnow()
        if (member.current_tasks >= member.max_tasks * 0.9 or member.current_weekly_hours >= member.weekly_capacity * 0.9):
            member.available = False
        self._persist_member(member)

    def _get_available_members(self) -> List[TeamMember]:
        if not self.team_members: return []
        available = []
        for member in self.team_members.values():
            if (member.available and member.current_tasks < member.max_tasks and member.current_weekly_hours < member.weekly_capacity * 0.85):
                available.append(member)
        return available

    def _calculate_assignment_score(self, member, task, required_skills, complexity, estimated_hours):
        score = 0.0
        if not required_skills: score += 0.5 * 0.4
        else: score += (sum(1 for s in required_skills if s in member.skills) / len(required_skills)) * 0.4
        
        lvl = member.skill_level.value if hasattr(member.skill_level, 'value') else member.skill_level
        if lvl == 'senior': score += (1.0 if complexity in ['compleja', 'muy_compleja'] else 0.7) * 0.25
        elif lvl == 'mid': score += (1.0 if complexity in ['moderada', 'simple'] else 0.6) * 0.25
        else: score += (1.0 if complexity == 'simple' else 0.4) * 0.25
        
        ratio = ((member.current_tasks / member.max_tasks) + (member.current_weekly_hours / member.weekly_capacity)) / 2
        score += (1.0 - ratio) * 0.2
        score += (member.success_rate / 100.0) * 0.15
        return min(score * 100, 100)

    def _get_fallback_assignment(self, task):
        if not self.team_members: return None
        candidates = list(self.team_members.values())
        candidates.sort(key=lambda m: (m.current_tasks / m.max_tasks))
        m = candidates[0]
        return AssignmentResult(assigned_to=m.name, slack_id=m.slack_id, member_name=m.name, confidence_score=0.3, reason="Asignación de emergencia", estimated_completion_time=0.0)

    def get_team_metrics(self) -> TeamMetrics:
        total_members = len(self.team_members)
        available_members = sum(1 for m in self.team_members.values() if m.available)
        total_tasks = sum(m.current_tasks for m in self.team_members.values())
        total_completed = sum(m.completed_tasks for m in self.team_members.values())
        completion_rate = (total_completed / (total_tasks + total_completed)) * 100 if (total_tasks + total_completed) > 0 else 0
        workload_distribution = {m.slack_id: (m.current_tasks / m.max_tasks) * 100 for m in self.team_members.values()}
        all_skills = set()
        for m in self.team_members.values(): all_skills.update(m.skills)
        skill_coverage = {skill: sum(1 for m in self.team_members.values() if skill in m.skills) for skill in all_skills}
        busy_members = [m.slack_id for m in self.team_members.values() if not m.available]
        
        return TeamMetrics(total_members=total_members, available_members=available_members, total_tasks_assigned=total_tasks, total_tasks_completed=total_completed, completion_rate=completion_rate, avg_completion_time=0.0, workload_distribution=workload_distribution, skill_coverage=skill_coverage, busy_members=busy_members)