# src/services/assignment_service.py
from models.team_members import TeamMember, TeamMetrics, AssignmentResult, SkillLevel
from typing import List, Dict
from datetime import datetime
from database.mongo_db import MongoDB
import random

class AssignmentService:
    def __init__(self):
        self.db = MongoDB()
        self.team_members: Dict[str, TeamMember] = {}
        self._load_team_data()
    
    def _load_team_data(self):
        loaded = False
        if self.db.team_collection is not None:
            try:
                if self.db.team_collection.count_documents({}) > 0:
                    stored = list(self.db.team_collection.find())
                    print(f"📂 Cargando {len(stored)} miembros de BD")
                    for doc in stored:
                        if '_id' in doc: del doc['_id']
                        # Restaurar Enum
                        if 'skill_level' in doc and isinstance(doc['skill_level'], str):
                            for sl in SkillLevel:
                                if sl.value == doc['skill_level']:
                                    doc['skill_level'] = sl
                                    break
                        self.team_members[doc['slack_id']] = TeamMember(**doc)
                    loaded = True
            except Exception as e:
                print(f"⚠️ Error leyendo BD: {e}")

        if not loaded:
            print("🚀 Inicializando equipo DEMO")
            self._initialize_sample_team()
            self._save_all_members()

    def _save_all_members(self):
        if self.db.team_collection is None: return
        for m in self.team_members.values(): self._persist_member(m)

    def _persist_member(self, member: TeamMember):
        if self.db.team_collection is None: return
        try:
            data = member.dict()
            if hasattr(data['skill_level'], 'value'):
                data['skill_level'] = data['skill_level'].value
            
            self.db.team_collection.update_one(
                {"slack_id": member.slack_id}, {"$set": data}, upsert=True
            )
        except Exception as e: print(f"❌ Error guardando miembro: {e}")

    def _initialize_sample_team(self):
        sample_team = [
            TeamMember(slack_id="U09ER0ZG9EH", name="Carlos Chilque", email="carlos@test.com", skills=["React", "Python", "FastAPI"], skill_level=SkillLevel.SENIOR, max_tasks=8, weekly_capacity=40, current_tasks=5, current_weekly_hours=28.0, completed_tasks=45, success_rate=98.5, avg_completion_time=3.5),
            TeamMember(slack_id="U09U6KWK21K", name="Daniela Aduviri", email="daniela@test.com", skills=["Figma", "CSS", "React"], skill_level=SkillLevel.MID, max_tasks=6, weekly_capacity=35, current_tasks=2, current_weekly_hours=10.0, completed_tasks=32, success_rate=95.0, avg_completion_time=4.2),
            TeamMember(slack_id="U09UDEDJP60", name="Victor Flores", email="victor@test.com", skills=["AWS", "Docker", "Python"], skill_level=SkillLevel.SENIOR, max_tasks=7, weekly_capacity=38, current_tasks=6, current_weekly_hours=35.0, completed_tasks=58, success_rate=99.1, avg_completion_time=2.8),
            TeamMember(slack_id="U09UE36P6PN", name="Bryan Rodríguez", email="bryan@test.com", skills=["Vue.js", "Testing"], skill_level=SkillLevel.MID, max_tasks=5, weekly_capacity=32, current_tasks=1, current_weekly_hours=4.0, completed_tasks=15, success_rate=88.5, avg_completion_time=5.1)
        ]
        for m in sample_team:
            if (m.current_tasks >= m.max_tasks * 0.9 or m.current_weekly_hours >= m.weekly_capacity * 0.9):
                m.available = False
            self.team_members[m.slack_id] = m

    def assign_batch(self, tasks: List[Dict]) -> AssignmentResult:
        if not self.team_members:
            return AssignmentResult(assigned_to="Unassigned", slack_id="UNKNOWN", member_name="Unassigned", confidence_score=0, reason="No team", estimated_completion_time=0)

        total_hours = 0.0
        all_skills = set()
        max_complex = 0
        comp_map = {'simple': 1, 'moderada': 2, 'compleja': 3, 'muy_compleja': 4}
        high_comp = "moderada"

        for t in tasks:
            h = 4.0
            if 'time_estimate' in t:
                val = t['time_estimate']
                if isinstance(val, (int, float)): h = float(val)
                elif isinstance(val, dict): h = float(val.get('realistic', 4.0))
            total_hours += h
            
            sk = t.get('required_skills', [])
            if isinstance(sk, list): all_skills.update(sk)
            elif isinstance(sk, str): all_skills.add(sk)
            
            c = t.get('complexity', 'moderada')
            if comp_map.get(c, 2) > max_complex:
                max_complex = comp_map.get(c, 2)
                high_comp = c

        available = self._get_available_members()
        if not available:
            fallback = self._get_fallback()
            if fallback and fallback.slack_id in self.team_members:
                self._update_metrics(self.team_members[fallback.slack_id], total_hours, len(tasks))
            return fallback

        scores = []
        req_skills = list(all_skills)
        for m in available:
            score = self._calc_score(m, req_skills, high_comp)
            scores.append((m, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        best, best_score = scores[0]
        self._update_metrics(best, total_hours, len(tasks))

        return AssignmentResult(
            assigned_to=best.name, slack_id=best.slack_id, member_name=best.name,
            confidence_score=best_score, reason=f"Mejor candidato para {len(tasks)} tareas ({total_hours}h)",
            estimated_completion_time=total_hours
        )

    def complete_task(self, slack_id, actual_hours, task_count=1, success=True):
        if slack_id in self.team_members:
            m = self.team_members[slack_id]
            print(f"📉 Liberando {m.name}: -{task_count} tareas")
            
            m.current_tasks = max(0, m.current_tasks - task_count)
            m.current_weekly_hours = max(0, m.current_weekly_hours - actual_hours)
            
            prev_comp = m.completed_tasks
            prev_rate = m.success_rate
            m.completed_tasks += task_count
            
            if success and m.completed_tasks > 0:
                new_points = 100 * task_count
                m.success_rate = ((prev_rate * prev_comp) + new_points) / m.completed_tasks

            if not m.available:
                if m.current_tasks < m.max_tasks * 0.8: m.available = True
            
            m.updated_at = datetime.utcnow()
            self._persist_member(m)

    def _update_metrics(self, member, hours, count):
        member.current_tasks += count
        member.current_weekly_hours += hours
        member.updated_at = datetime.utcnow()
        if (member.current_tasks >= member.max_tasks * 0.9 or member.current_weekly_hours >= member.weekly_capacity * 0.9):
            member.available = False
        self._persist_member(member)

    def _get_available_members(self):
        return [m for m in self.team_members.values() if m.available and m.current_tasks < m.max_tasks]

    def _get_fallback(self):
        if not self.team_members: return None
        candidates = list(self.team_members.values())
        candidates.sort(key=lambda m: m.current_tasks)
        m = candidates[0]
        return AssignmentResult(assigned_to=m.name, slack_id=m.slack_id, member_name=m.name, confidence_score=0.3, reason="Fallback", estimated_completion_time=0)

    def _calc_score(self, member, req_skills, complexity):
        score = 0.0
        if not req_skills: score += 0.2
        else: score += (sum(1 for s in req_skills if s in member.skills)/len(req_skills)) * 0.4
        
        lvl = member.skill_level.value if hasattr(member.skill_level, 'value') else member.skill_level
        if lvl == 'senior': score += 0.25
        elif lvl == 'mid': score += 0.15
        
        score += (1.0 - (member.current_tasks/member.max_tasks)) * 0.2
        return min(score*100, 100)

    def get_team_metrics(self) -> TeamMetrics:
        total = len(self.team_members)
        avail = sum(1 for m in self.team_members.values() if m.available)
        t_tasks = sum(m.current_tasks for m in self.team_members.values())
        t_comp = sum(m.completed_tasks for m in self.team_members.values())
        rate = (t_comp / (t_tasks + t_comp) * 100) if (t_tasks + t_comp) > 0 else 0
        
        workload = {m.slack_id: (m.current_tasks/m.max_tasks)*100 for m in self.team_members.values()}
        skills = {}
        for m in self.team_members.values():
            for s in m.skills: skills[s] = skills.get(s, 0) + 1
            
        busy = [m.slack_id for m in self.team_members.values() if not m.available]
        
        return TeamMetrics(
            total_members=total, available_members=avail,
            total_tasks_assigned=t_tasks, total_tasks_completed=t_comp,
            completion_rate=rate, avg_completion_time=0.0,
            workload_distribution=workload, skill_coverage=skills, busy_members=busy
        )