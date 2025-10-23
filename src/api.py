import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Importar componentes existentes
from trello.trello_action_events import TrelloActionEvents
from common.slack.slack_event_callback import event_callback
from models.trello import TrelloEvent
from utils.thread_manager import ThreadManager

# 🆕 Importar dashboard
from dashboard.app import router as dashboard_router
from dashboard.routes.analytics import router as analytics_router
from dashboard.routes.projects import router as projects_router

load_dotenv()

# Configuración de FastAPI
app = FastAPI(
    title="Trello-Slack AI Bot + Dashboard",
    description="Sistema de automatización con IA y dashboard de analytics",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🆕 Montar dashboard
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(analytics_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(projects_router, prefix="/dashboard", tags=["dashboard"])

# 🆕 Servir archivos estáticos del dashboard
static_path = os.path.join(os.path.dirname(__file__), "dashboard", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Endpoints existentes (se mantienen igual)
@app.options("/", status_code=status.HTTP_200_OK)
def server_options():
    """Endpoint de options para CORS"""
    return JSONResponse(content={
        "endpoint_list": ["/trello-events", "/slack-events", "/dashboard"],
        "allowed_methods": "GET, POST"
    })

@app.head("/trello-events", status_code=status.HTTP_200_OK)
@app.get("/trello-events", status_code=status.HTTP_200_OK)
def return_status_code():
    """Health check para webhooks de Trello"""
    return JSONResponse(content={"msg": "sent event"})

@app.post("/trello-events", status_code=status.HTTP_200_OK)
async def controller_trello_events(trello_event: TrelloEvent):
    """
    Webhook principal de Trello. Recibe eventos y los procesa en background.
    Responde inmediatamente mientras el procesamiento ocurre en hilos.
    """
    response = {"msg": "Event received"}
    tm = ThreadManager()
    tae = TrelloActionEvents(trello_event=trello_event)

    try:
        # Decision making basado en el tipo de evento
        if tae.main_data.action_type == 'commentCard':
            tm.add_thread(target=tae.comment_card_action)
            tm.start_threads()
            print(f'card commented by "{tae.main_data.username}"')
        
        elif tae.main_data.action_type == 'updateComment':
            tm.add_thread(target=tae.comment_update_action)
            tm.start_threads()
            print(f'Comment updated by "{tae.main_data.username}"')
        
        elif tae.main_data.action_type == 'updateCard':
            tm.add_thread(target=tae.update_card_action)
            tm.start_threads()
            print(f'card updated by "{tae.main_data.username}"')
        
        elif trello_event.action['type'] == 'createCard':
            tm.add_thread(target=tae.create_card_action)
            tm.start_threads()
            print(f'card created by "{tae.main_data.username}"')
        
        else:
            print(f'type action event: "{trello_event.action["type"]}"')
    
    except Exception as e:
        response["msg"] = str(e)

    return JSONResponse(content=response)

@app.post("/slack-events", status_code=status.HTTP_200_OK)
async def controller_slack_events(request: dict):
    """Webhook para eventos de Slack (en desarrollo)"""
    data = {}
    event_type = request["type"]
    
    if event_type == "url_verification":
        data = {"challenge": request["challenge"]}
    elif event_type == 'event_callback':
        data = event_callback(response=request)
        data = {"data": data}
    else:
        raise Exception(f"unable to handle event type: {event_type}")

    return JSONResponse(content=data)

# 🆕 Ruta principal redirige al dashboard
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trello-Slack AI Bot</title>
        <meta http-equiv="refresh" content="0; url=/dashboard" />
        <style>
            body { 
                font-family: Arial, sans-serif; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container { 
                text-align: center; 
                background: rgba(255,255,255,0.1); 
                padding: 2rem; 
                border-radius: 10px; 
                backdrop-filter: blur(10px);
            }
            h1 { margin-bottom: 1rem; }
            a { 
                color: #fff; 
                text-decoration: none; 
                font-weight: bold;
                padding: 0.5rem 1rem;
                border: 2px solid white;
                border-radius: 5px;
                transition: all 0.3s;
            }
            a:hover { 
                background: white; 
                color: #667eea; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Trello-Slack AI Bot</h1>
            <p>Sistema de automatización con IA y dashboard de analytics</p>
            <p>Redirigiendo al dashboard...</p>
            <p><a href="/dashboard">Ir al Dashboard Manualmente</a></p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "trello_webhook": "active",
            "slack_webhook": "active", 
            "dashboard": "active",
            "ai_processing": "active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050)