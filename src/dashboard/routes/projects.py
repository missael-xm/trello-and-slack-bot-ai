# src/dashboard/routes/projects.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database.mongo_db import MongoDB

# IMPORTANTE: Importar el servicio de asignación
from services.assignment_service import AssignmentService

router = APIRouter()

def get_db():
    return MongoDB()

# Instancia global del servicio
assignment_service = AssignmentService()

@router.get("/api/projects")
async def get_all_projects(db: MongoDB = Depends(get_db)):
    """API para obtener todos los proyectos"""
    try:
        projects = list(db.analytics_collection.find().sort("request_date", -1))
        for project in projects:
            if '_id' in project: project['_id'] = str(project['_id'])
            if 'request_date' in project and isinstance(project['request_date'], datetime):
                project['request_date'] = project['request_date'].isoformat()
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@router.put("/api/project/{project_id}/status")
async def update_project_status(project_id: str, status: str, actual_hours: float = None, db: MongoDB = Depends(get_db)):
    """
    API para actualizar estado. 
    Si pasa a 'completed', libera la carga del miembro asignado.
    """
    try:
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be: {valid_statuses}")
        
        # Obtener proyecto ANTES de actualizar para ver quién estaba asignado
        project = db.analytics_collection.find_one({"project_id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        # Lógica de completado
        if status == 'completed':
            update_data["progress_percentage"] = 100.0
            update_data["actual_end_date"] = datetime.utcnow()
            
            # --- LÓGICA DE LIBERACIÓN DE CARGA ---
            # Verificar que no haya sido completado ya para no restar doble
            if project.get('status') != 'completed':
                assigned_id = project.get('assigned_lead_id')
                
                # Si es formato nuevo (assigned_lead_id)
                if assigned_id:
                    tasks_count = project.get('total_tasks', 1)
                    estimated = project.get('total_estimated_hours', 4.0)
                    hours_to_release = actual_hours if actual_hours else estimated
                    
                    print(f"🎉 Proyecto {project_id} completado. Liberando a {assigned_id}...")
                    assignment_service.complete_task(
                        slack_id=assigned_id, 
                        actual_hours=hours_to_release, 
                        task_count=tasks_count,
                        success=True
                    )
                
                # Soporte legacy (si no tiene assigned_lead_id, buscar en assignment_details)
                elif project.get('assignment_details'):
                    details = project.get('assignment_details')
                    if isinstance(details, list) and len(details) > 0:
                        first_assign = details[0]
                        slack_id = first_assign.get('slack_id')
                        if slack_id:
                            tasks_count = project.get('total_tasks', 1)
                            estimated = project.get('total_estimated_hours', 4.0)
                            assignment_service.complete_task(slack_id, estimated, tasks_count)

        elif status == 'in_progress':
            update_data["progress_percentage"] = 50.0
            update_data["actual_start_date"] = datetime.utcnow()
        
        if actual_hours is not None:
            update_data["actual_total_hours"] = actual_hours
        
        result = db.analytics_collection.update_one(
            {"project_id": project_id},
            {"$set": update_data}
        )
        
        return {"message": f"Project updated to {status}", "project_id": project_id}
        
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")

@router.delete("/api/project/{project_id}")
async def delete_project(project_id: str, db: MongoDB = Depends(get_db)):
    """API para eliminar un proyecto"""
    try:
        result = db.analytics_collection.delete_one({"project_id": project_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"message": "Project deleted", "project_id": project_id}
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")

@router.get("/api/project/{project_id}")
async def get_project_data(project_id: str, db: MongoDB = Depends(get_db)):
    try:
        project = db.analytics_collection.find_one({"project_id": project_id})
        if not project: raise HTTPException(status_code=404, detail="Project not found")
        if '_id' in project: project['_id'] = str(project['_id'])
        return project
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")