# src/dashboard/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from collections import Counter
from database.mongo_db import MongoDB
from services.assignment_service import AssignmentService
import json

router = APIRouter()

# Instancia global segura
assignment_service_global = None

def get_assignment_service():
    global assignment_service_global
    if assignment_service_global is None:
        try:
            assignment_service_global = AssignmentService()
        except Exception as e:
            print(f"⚠️ Error servicio asignación: {e}")
            return None
    return assignment_service_global

def get_db():
    return MongoDB()

# --- NORMALIZACIÓN DE DATOS ---
def normalize_priority(val):
    val = str(val).lower().strip()
    if val in ['high', 'alta', 'crítica', 'critical', 'urgent']: return 'Alta'
    if val in ['low', 'baja', 'simple']: return 'Baja'
    return 'Media'

def normalize_complexity(val):
    val = str(val).lower().strip()
    if val in ['simple', 'baja']: return 'Simple'
    if val in ['moderada', 'moderate', 'media']: return 'Moderada'
    if val in ['compleja', 'complex', 'high']: return 'Compleja'
    return 'Moderada'

@router.get("/api/metrics")
async def get_metrics(days: int = 30, db: MongoDB = Depends(get_db)):
    try:
        start = datetime.utcnow() - timedelta(days=days)
        # Traer proyectos
        projects = list(db.analytics_collection.find({"request_date": {"$gte": start}})) or []
        
        total_tasks = sum(p.get('total_tasks', 0) for p in projects)
        total_hours = sum(p.get('total_estimated_hours', 0) for p in projects)
        status_counts = Counter(p.get('status', 'pending') for p in projects)
        completed = status_counts.get('completed', 0)
        total_p = len(projects)
        
        return {
            "total_projects": total_p,
            "total_tasks": total_tasks,
            "total_estimated_hours": round(total_hours, 2),
            "completed_projects": completed,
            "pending_projects": status_counts.get('pending', 0),
            "in_progress_projects": status_counts.get('in_progress', 0),
            "average_tasks_per_project": round(total_tasks / total_p, 1) if total_p else 0,
            "average_hours_per_project": round(total_hours / total_p, 1) if total_p else 0,
            "success_rate": round((completed / total_p) * 100, 1) if total_p else 0
        }
    except Exception as e:
        print(f"Error metrics: {e}")
        return {"total_projects": 0, "error": str(e)}

@router.get("/api/team-metrics")
async def get_team_metrics():
    """Datos para las tarjetas de equipo en Dashboard"""
    srv = get_assignment_service()
    if not srv: return {}
    try:
        return json.loads(srv.get_team_metrics().json())
    except: return {}

@router.get("/api/member-metrics")
async def get_member_metrics():
    srv = get_assignment_service()
    if not srv: return {"members": []}
    try:
        members = []
        for m in srv.team_members.values():
            md = m.dict()
            # Fix Enums
            if hasattr(m.skill_level, 'value'): md['skill_level'] = m.skill_level.value
            else: md['skill_level'] = str(m.skill_level)
            
            if m.weekly_capacity > 0:
                md['utilization'] = (m.current_weekly_hours / m.weekly_capacity) * 100
            else: md['utilization'] = 0
            members.append(md)
        return {"members": members}
    except: return {"members": []}

@router.get("/api/priorities")
async def get_priorities(days: int = 30, db: MongoDB = Depends(get_db)):
    try:
        start = datetime.utcnow() - timedelta(days=days)
        projs = list(db.analytics_collection.find({"request_date": {"$gte": start}}))
        counts = {"Alta": 0, "Media": 0, "Baja": 0}
        for p in projs:
            dist = p.get('priority_distribution')
            if dist:
                for k, v in dist.items(): counts[normalize_priority(k)] += v
            else:
                counts[normalize_priority(p.get('highest_priority', 'Media'))] += 1
        return counts
    except: return {"Alta": 0, "Media": 0, "Baja": 0}

@router.get("/api/categories")
async def get_categories(days: int = 30, db: MongoDB = Depends(get_db)):
    try:
        start = datetime.utcnow() - timedelta(days=days)
        projs = list(db.analytics_collection.find({"request_date": {"$gte": start}}))
        cats = []
        for p in projs:
            for c, v in p.get('category_distribution', {}).items(): cats.extend([c]*v)
        if not cats: return {}
        return dict(Counter(cats).most_common(6))
    except: return {}

@router.get("/api/complexity")
async def get_complexity(days: int = 30, db: MongoDB = Depends(get_db)):
    try:
        start = datetime.utcnow() - timedelta(days=days)
        projs = list(db.analytics_collection.find({"request_date": {"$gte": start}}))
        counts = Counter()
        for p in projs:
            # Preferir detalle de tareas, sino promedio
            tasks = p.get('tasks', [])
            if tasks:
                for t in tasks:
                    c = t.get('complexity', 'moderada')
                    counts[normalize_complexity(c)] += 1
            else:
                avg = p.get('average_complexity')
                if avg: counts[normalize_complexity(avg)] += 1
        return {"complexity_distribution": dict(counts)}
    except: return {"complexity_distribution": {}}

@router.get("/api/timeline")
async def get_timeline(days: int = 30, db: MongoDB = Depends(get_db)):
    start = datetime.utcnow() - timedelta(days=days)
    projs = list(db.analytics_collection.find({"request_date": {"$gte": start}}).sort("request_date", 1))
    return [{"request_date": p['request_date'].isoformat()} for p in projs if p.get('request_date')]

@router.get("/api/skills")
async def get_skills(days: int = 30, db: MongoDB = Depends(get_db)):
    start = datetime.utcnow() - timedelta(days=days)
    projs = list(db.analytics_collection.find({"request_date": {"$gte": start}}))
    skills = []
    for p in projs: skills.extend(p.get('required_skills', []))
    return dict(Counter(skills).most_common(10))

@router.get("/api/project/{project_id}")
async def get_project_data(project_id: str, db: MongoDB = Depends(get_db)):
    p = db.analytics_collection.find_one({"project_id": project_id})
    if p and '_id' in p: p['_id'] = str(p['_id'])
    return p