import os
import requests
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pymongo import MongoClient
from openai import OpenAI

# Cargar variables del .env
load_dotenv()

def test_openai():
    print("🔹 Probando OpenAI...")
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL"),
            messages=[{"role": "user", "content": "Hola, ¿estás funcionando?"}],
            max_tokens=10
        )
        print("✅ OpenAI OK:", response.choices[0].message.content)
    except Exception as e:
        print("❌ OpenAI ERROR:", e)

def test_slack():
    print("\n🔹 Probando Slack...")
    try:
        slack_client = WebClient(token=os.getenv("SLACK_APP_BOT_KEY"))
        slack_client.chat_postMessage(
            channel=os.getenv("SLACK_BOT_CHANNEL"),
            text="✅ Bot conectado correctamente desde el script de prueba (Python)."
        )
        print("✅ Slack OK: Mensaje enviado a", os.getenv("SLACK_BOT_CHANNEL"))
    except SlackApiError as e:
        print("❌ Slack ERROR:", e.response["error"])
    except Exception as e:
        print("❌ Slack ERROR:", e)

def test_trello():
    print("\n🔹 Probando Trello...")
    try:
        url = f"https://api.trello.com/1/members/me/boards?key={os.getenv('TRELLO_API_KEY')}&token={os.getenv('TRELLO_API_TOKEN')}"
        res = requests.get(url)
        data = res.json()
        if isinstance(data, list):
            print("✅ Trello OK: Tableros encontrados =", len(data))
        else:
            print("❌ Trello ERROR:", data)
    except Exception as e:
        print("❌ Trello ERROR:", e)

def test_mongo():
    print("\n🔹 Probando MongoDB...")
    try:
        client = MongoClient(os.getenv("MONGODB_URI"))
        db_name = os.getenv("MONGODB_URI").split("/")[-1].split("?")[0]
        db = client[db_name]
        collections = db.list_collection_names()
        print("✅ MongoDB OK: Colecciones encontradas =", len(collections))
        client.close()
    except Exception as e:
        print("❌ MongoDB ERROR:", e)

if __name__ == "__main__":
    test_openai()
    test_slack()
    test_trello()
    test_mongo()
    print("\n🎉 Todas las pruebas finalizaron.")
