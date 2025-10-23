from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from database.mongo_db import MongoDB

router = APIRouter()

def get_db():
    return MongoDB()

@router.get("/api/projects")
async def get_all_projects(db: MongoDB = Depends(get_db)):
    """API para obtener todos los proyectos"""
    try:
        projects = list(db.analytics_collection.find().sort("request_date", -1))
        
        # Convertir ObjectIds a strings para JSON serialization
        for project in projects:
            if '_id' in project:
                project['_id'] = str(project['_id'])
            # Convertir datetime a string ISO format
            if 'request_date' in project and isinstance(project['request_date'], datetime):
                project['request_date'] = project['request_date'].isoformat()
            if 'created_at' in project and isinstance(project['created_at'], datetime):
                project['created_at'] = project['created_at'].isoformat()
        
        return projects
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")

@router.put("/api/project/{project_id}/status")
async def update_project_status(project_id: str, status: str, actual_hours: float = None, db: MongoDB = Depends(get_db)):
    """API para actualizar el estado de un proyecto"""
    try:
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if status == 'completed':
            update_data["progress_percentage"] = 100.0
            update_data["actual_end_date"] = datetime.utcnow()
        elif status == 'in_progress':
            update_data["progress_percentage"] = 50.0
            update_data["actual_start_date"] = datetime.utcnow()
        
        if actual_hours is not None:
            update_data["actual_total_hours"] = actual_hours
        
        result = db.analytics_collection.update_one(
            {"project_id": project_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Project not found or no changes made")
        
        return {"message": f"Project status updated to {status}", "project_id": project_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating project status: {str(e)}")

@router.delete("/api/project/{project_id}")
async def delete_project(project_id: str, db: MongoDB = Depends(get_db)):
    """API para eliminar un proyecto"""
    try:
        result = db.analytics_collection.delete_one({"project_id": project_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"message": "Project deleted successfully", "project_id": project_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")