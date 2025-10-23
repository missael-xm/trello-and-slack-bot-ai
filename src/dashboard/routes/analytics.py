from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from collections import Counter
import statistics
from database.mongo_db import MongoDB

router = APIRouter()

def get_db():
    return MongoDB()

@router.get("/api/metrics")
async def get_metrics(days: int = 30, db: MongoDB = Depends(get_db)):
    """API para métricas generales del dashboard"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = list(db.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }))

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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")

@router.get("/api/categories")
async def get_categories(days: int = 30, db: MongoDB = Depends(get_db)):
    """API para distribución de tareas por categoría"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = list(db.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }))

        categories = []
        for project in projects:
            category_dist = project.get('category_distribution', {})
            for category, count in category_dist.items():
                categories.extend([category] * count)

        distribution = dict(Counter(categories))
        return distribution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.get("/api/priorities")
async def get_priorities(days: int = 30, db: MongoDB = Depends(get_db)):
    """API para distribución de tareas por prioridad"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = list(db.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }))

        priorities = []
        for project in projects:
            priority_dist = project.get('priority_distribution', {})
            for priority, count in priority_dist.items():
                priorities.extend([priority] * count)

        distribution = dict(Counter(priorities))
        return distribution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching priorities: {str(e)}")

@router.get("/api/complexity")
async def get_complexity(days: int = 30, db: MongoDB = Depends(get_db)):
    """API para análisis de complejidad"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = list(db.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }))

        complexities = []
        hours_by_complexity = {}
        
        for project in projects:
            # Complejidad promedio del proyecto
            avg_complexity = project.get('average_complexity')
            if avg_complexity:
                complexities.append(avg_complexity)
            
            # Horas por complejidad de tareas individuales
            tasks = project.get('tasks', [])
            for task in tasks:
                if isinstance(task, dict):
                    complexity = task.get('complexity', 'simple')
                    time_est = task.get('time_estimate', {})
                    hours = time_est.get('realistic', 0) if isinstance(time_est, dict) else 0
                    
                    if complexity not in hours_by_complexity:
                        hours_by_complexity[complexity] = 0
                    hours_by_complexity[complexity] += hours

        return {
            "complexity_distribution": dict(Counter(complexities)),
            "hours_by_complexity": hours_by_complexity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching complexity data: {str(e)}")

@router.get("/api/timeline")
async def get_timeline(days: int = 30, db: MongoDB = Depends(get_db)):
    """API para datos de línea de tiempo"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = list(db.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }).sort("request_date", 1))

        timeline_data = []
        for project in projects:
            timeline_data.append({
                "card_title": project.get('card_title', 'Unknown'),
                "request_date": project.get('request_date').isoformat() if project.get('request_date') else None,
                "total_tasks": project.get('total_tasks', 0),
                "total_hours": project.get('total_estimated_hours', 0),
                "status": project.get('status', 'pending'),
                "priority": project.get('highest_priority', 'media'),
                "project_id": project.get('project_id')
            })

        return timeline_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching timeline data: {str(e)}")

@router.get("/api/skills")
async def get_skills(days: int = 30, db: MongoDB = Depends(get_db)):
    """API para habilidades técnicas más requeridas"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        projects = list(db.analytics_collection.find({
            "request_date": {"$gte": start_date}
        }))

        all_skills = []
        for project in projects:
            skills = project.get('required_skills', [])
            if isinstance(skills, list):
                all_skills.extend(skills)

        skill_counts = Counter(all_skills)
        top_skills = dict(skill_counts.most_common(10))
        
        return top_skills
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching skills data: {str(e)}")

@router.get("/api/project/{project_id}")
async def get_project_data(project_id: str, db: MongoDB = Depends(get_db)):
    """API para obtener datos de un proyecto específico"""
    try:
        project = db.analytics_collection.find_one({"project_id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Convertir ObjectId a string para JSON serialization
        if '_id' in project:
            project['_id'] = str(project['_id'])
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project data: {str(e)}")