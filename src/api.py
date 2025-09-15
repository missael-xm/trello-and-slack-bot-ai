# src/api.py
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from trello.trello_action_events import TrelloActionEvents
from common.slack.slack_event_callback import event_callback
from models.trello import TrelloEvent
from utils.thread_manager import ThreadManager

load_dotenv()

# Configuración de FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.options("/", status_code=status.HTTP_200_OK)
def server_options():
    """Endpoint de options para CORS"""
    return JSONResponse(content={
        "endpoint_list": ["/trello-events", "/slack-events"],
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
        response["msg"] = e

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

@app.get("/", status_code=status.HTTP_200_OK)
async def init():
    """Health check principal"""
    return JSONResponse(content="welcome to trello/slack assistant")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8050)