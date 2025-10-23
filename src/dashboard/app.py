from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
from datetime import datetime, timedelta
from database.mongo_db import MongoDB

# Configurar templates
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

# Crear router principal del dashboard
router = APIRouter()

def get_db():
    return MongoDB()

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, db: MongoDB = Depends(get_db)):
    """Página principal del dashboard"""
    try:
        # Obtener métricas básicas para la página principal
        metrics = {
            "total_projects": db.analytics_collection.count_documents({}),
            "recent_projects": db.analytics_collection.count_documents({
                "request_date": {"$gte": datetime.utcnow() - timedelta(days=7)}
            }),
            "pending_projects": db.analytics_collection.count_documents({
                "status": "pending"
            }),
            "completed_projects": db.analytics_collection.count_documents({
                "status": "completed"
            })
        }
        
        # Obtener proyectos recientes
        recent_projects = list(db.analytics_collection.find()
                              .sort("request_date", -1)
                              .limit(5))
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "metrics": metrics,
            "recent_projects": recent_projects
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/projects", response_class=HTMLResponse)
async def projects_view(request: Request, db: MongoDB = Depends(get_db)):
    """Vista de todos los proyectos"""
    try:
        projects = list(db.analytics_collection.find().sort("request_date", -1))
        return templates.TemplateResponse("projects.html", {
            "request": request,
            "projects": projects
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_view(request: Request):
    """Vista de analytics con gráficas"""
    return templates.TemplateResponse("analytics.html", {"request": request})

@router.get("/project/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: str, db: MongoDB = Depends(get_db)):
    """Detalle de un proyecto específico"""
    try:
        project = db.analytics_collection.find_one({"project_id": project_id})
        if not project:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Project {project_id} not found"
            })
        
        return templates.TemplateResponse("project_detail.html", {
            "request": request,
            "project": project
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })