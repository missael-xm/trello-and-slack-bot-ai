# setup_webhook.py
import requests
import os
import subprocess
import time
from dotenv import load_dotenv

class TrelloWebhookSetup:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.token = os.getenv('TRELLO_API_TOKEN')
        self.board_id = "4j4pQa4q"  # Tu board ID de Trello
        self.ngrok_process = None
        
    def start_ngrok(self):
        """Inicia ngrok en segundo plano"""
        try:
            print("🔧 Iniciando ngrok...")
            self.ngrok_process = subprocess.Popen(
                ["ngrok", "http", "8050"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3)  # Esperar que ngrok inicie
            return True
        except Exception as e:
            print(f"❌ Error iniciando ngrok: {e}")
            return False
    
    def get_ngrok_url(self):
        """Obtiene la URL pública de ngrok"""
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            tunnels = response.json()['tunnels']
            for tunnel in tunnels:
                if tunnel['proto'] == 'https':
                    return tunnel['public_url']
            return None
        except:
            return None
    
    def create_webhook(self, ngrok_url):
        """Crea el webhook en Trello"""
        callback_url = f"{ngrok_url}/trello-events"
        
        print(f"🌐 URL de webhook: {callback_url}")
        print(f"📋 Board ID: {self.board_id}")
        
        url = f"https://api.trello.com/1/tokens/{self.token}/webhooks/?key={self.api_key}"
        
        payload = {
            "description": "Trello-Slack AI Bot",
            "callbackURL": callback_url,
            "idModel": self.board_id
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                webhook_id = response.json().get('id')
                print(f"✅ Webhook creado exitosamente!")
                print(f"📋 ID del webhook: {webhook_id}")
                return True
            else:
                print(f"❌ Error de Trello: {response.json()}")
                return False
                
        except Exception as e:
            print(f"❌ Error creando webhook: {e}")
            return False
    
    def check_existing_webhooks(self):
        """Verifica webhooks existentes"""
        try:
            url = f"https://api.trello.com/1/tokens/{self.token}/webhooks?key={self.api_key}"
            response = requests.get(url, timeout=10)
            webhooks = response.json()
            
            if webhooks:
                print("\n📋 Webhooks existentes:")
                for webhook in webhooks:
                    print(f"   - {webhook['description']}: {webhook['callbackURL']}")
            return webhooks
        except:
            return []
    
    def delete_old_webhooks(self):
        """Elimina webhooks viejos"""
        try:
            webhooks = self.check_existing_webhooks()
            for webhook in webhooks:
                url = f"https://api.trello.com/1/webhooks/{webhook['id']}?key={self.api_key}&token={self.token}"
                requests.delete(url)
                print(f"🗑️ Eliminado webhook: {webhook['id']}")
        except Exception as e:
            print(f"⚠️ Error eliminando webhooks viejos: {e}")
    
    def run(self):
        """Ejecuta la configuración completa"""
        print("=" * 60)
        print("🚀 CONFIGURADOR AUTOMÁTICO DE WEBHOOK TRELLO")
        print("=" * 60)
        
        # Verificar credenciales
        if not self.api_key or not self.token:
            print("❌ ERROR: Faltan API_KEY o TOKEN en el archivo .env")
            print("   Asegúrate de tener:")
            print("   TRELLO_API_KEY=2e50cd24fe018e571f0fbaca332377d1")
            print("   TRELLO_API_TOKEN=tu_token_generado")
            return
        
        # Eliminar webhooks viejos
        print("\n1. 🗑️ Limpiando webhooks antiguos...")
        self.delete_old_webhooks()
        
        # Iniciar ngrok
        print("\n2. 🔄 Iniciando ngrok...")
        if not self.start_ngrok():
            print("❌ Ngrok no está instalado. Instala con: npm install -g ngrok")
            return
        
        # Obtener URL de ngrok
        print("\n3. 🌐 Obteniendo URL pública...")
        ngrok_url = None
        for _ in range(10):  # Intentar por 10 segundos
            ngrok_url = self.get_ngrok_url()
            if ngrok_url:
                break
            time.sleep(1)
        
        if not ngrok_url:
            print("❌ No se pudo obtener URL de ngrok. Verifica que ngrok esté instalado.")
            return
        
        print(f"   ✅ URL obtenida: {ngrok_url}")
        
        # Crear webhook
        print("\n4. ⚙️ Creando webhook en Trello...")
        if self.create_webhook(ngrok_url):
            print("\n" + "=" * 60)
            print("🎉 ¡CONFIGURACIÓN COMPLETADA!")
            print("=" * 60)
            print("📋 Ahora puedes:")
            print("   1. Dejar esta terminal con ngrok ejecutando")
            print("   2. En otra terminal, ejecutar: python src/api.py")
            print("   3. Usar Trello normalmente ¡y el bot funcionará!")
            print(f"   4. Webhook URL: {ngrok_url}/trello-events")
        else:
            print("❌ No se pudo crear el webhook")

if __name__ == "__main__":
    setup = TrelloWebhookSetup()
    setup.run()