# src/utils/slack.py
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from utils.config import slack_app_bot_key

def client(auth_token=slack_app_bot_key):
    """
    Factory del cliente de Slack WebClient.
    Permite usar diferentes tokens según el contexto.
    """
    wc = WebClient(token=auth_token)
    return wc

# Configuración del bot
bot_setting = {
    "username": "Agatha Trunchbull (Asistente de Trello)",
    "profile_img": "https://cdna.artstation.com/p/assets/covers/images/038/161/420/large/edward-anthonio-pratama-edward-anthonio-pratama-0051.jpg"
}

# Verificador de firma para webhooks
signature_verifier = SignatureVerifier(slack_app_bot_key)

# Lista de canales y usuarios permitidos
channels = [
    # Direct Messages (IMs)
    {"channel": "Carlos Chilque", "channel_id": "U09ER0ZG9EH"},
    # Canales públicos
    {"channel": "todo-proyecto-integracion", "channel_id": "C09ER0ZRT61"},
    # ... más canales
]