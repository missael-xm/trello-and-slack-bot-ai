# start_bot_no_npm.py - VERSIÓN OPTIMIZADA
import os
import requests
import subprocess
import time
import sys
from dotenv import load_dotenv

def ensure_ngrok_authtoken():
    """Verifica si el authtoken está en .env y lo configura si es necesario."""
    load_dotenv()
    ngrok_token = os.getenv('NGROK_AUTHTOKEN')
    
    if not ngrok_token:
        # Si el token no está en .env, no podemos hacer nada.
        return

    # Comprobar si el token ya está configurado para no hacerlo siempre.
    # Esta parte es compleja, por eso es mejor hacerlo manual.
    # Una forma simple (pero no perfecta) es simplemente ejecutar el comando.
    try:
        print("⚙️ Detectado NGROK_AUTHTOKEN, intentando configurar...")
        # Usamos 'ngrok.exe' para que coincida con tu script
        subprocess.run(
            ["ngrok.exe", "config", "add-authtoken", ngrok_token],
            capture_output=True,
            check=True # Lanza un error si el comando falla
        )
        print("✅ Authtoken de ngrok configurado desde el archivo .env")
    except Exception as e:
        # El comando puede fallar si ngrok no existe o por otros motivos
        print(f"⚠️ No se pudo auto-configurar el authtoken de ngrok: {e}")

def check_ngrok():
    """Verifica si ngrok está disponible y funcionando"""
    try:
        # Verificar si ngrok.exe existe en el directorio actual
        if not os.path.exists("ngrok.exe"):
            print("❌ ngrok.exe no encontrado en la carpeta raíz")
            print("💡 Asegúrate de que ngrok.exe esté en la misma carpeta que este script")
            return False
        
        # Verificar la versión sin mostrar output
        result = subprocess.run(
            ["ngrok.exe", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10,
            cwd=os.getcwd(),
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            print("✅ Ngrok encontrado y funcionando")
            return True
        else:
            print(f"❌ Ngrok no responde: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando ngrok: {e}")
        return False

def run_ngrok(port=8050):
    """Inicia ngrok de manera confiable"""
    try:
        print(f"🚀 Iniciando ngrok en puerto {port}...")
        print("⏳ Esto puede tomar 5-10 segundos...")
        
        # Iniciar ngrok en una nueva ventana (funciona mejor en Windows)
        process = subprocess.Popen(
            ["ngrok.exe", "http", str(port), "--log=stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Dar tiempo suficiente para que ngrok inicie
        time.sleep(8)
        
        # Verificar si el proceso sigue activo
        if process.poll() is not None:
            print("❌ Ngrok se cerró inmediatamente")
            # Leer el error
            stdout, stderr = process.communicate()
            if stderr:
                print(f"📋 Error: {stderr}")
            elif stdout:
                print(f"📋 Output: {stdout}")
            return None
        
        print("✅ Ngrok iniciado correctamente")
        return process
        
    except Exception as e:
        print(f"❌ Error iniciando ngrok: {e}")
        return None

def get_ngrok_url():
    """Obtiene la URL de ngrok con múltiples intentos"""
    print("🔍 Obteniendo URL de ngrok...")
    
    max_attempts = 12
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])
                
                for tunnel in tunnels:
                    if tunnel.get('proto') == 'https':
                        url = tunnel.get('public_url')
                        if url:
                            print(f"✅ URL obtenida después de {attempt + 1} intentos")
                            return url
            
            time.sleep(1)
            
        except requests.exceptions.ConnectionError:
            # Esperar progresivamente más
            wait_time = min(1.5 * (attempt + 1), 3)
            if attempt % 3 == 0:  # No spammear mensajes
                print(f"⏳ Esperando que ngrok esté listo... ({attempt + 1}/{max_attempts})")
            time.sleep(wait_time)
            
        except Exception as e:
            if attempt % 4 == 0:  # No spammear mensajes de error
                print(f"⚠️ Intento {attempt + 1}: {type(e).__name__}")
            time.sleep(2)
    
    print("❌ No se pudo conectar con ngrok después de 12 intentos")
    return None

def setup_webhook_auto():
    """Configuración automática del webhook"""
    print("\n🌐 CONFIGURACIÓN AUTOMÁTICA DEL WEBHOOK")
    print("=" * 50)
    
    # Iniciar ngrok
    ngrok_process = run_ngrok(8050)
    if not ngrok_process:
        print("❌ Falló el inicio automático de ngrok")
        return False
    
    # Obtener URL
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ No se pudo obtener la URL automáticamente")
        ngrok_process.terminate()
        return False
    
    print(f"✅ URL de ngrok: {ngrok_url}")
    
    # Configurar webhook en Trello
    load_dotenv()
    api_key = os.getenv('TRELLO_API_KEY')
    token = os.getenv('TRELLO_API_TOKEN')
    board_id = "68c366e3edf05392b3ce4c7d"
    
    if not api_key or not token:
        print("❌ Faltan API_KEY o TOKEN en el archivo .env")
        return False
    
    url = f"https://api.trello.com/1/tokens/{token}/webhooks/?key={api_key}"
    payload = {
        "description": "Trello-Slack Bot Windows",
        "callbackURL": f"{ngrok_url}/trello-events",
        "idModel": board_id
    }
    
    try:
        print("⚙️ Creando webhook en Trello...")
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            webhook_id = response.json().get('id')
            print("✅ Webhook creado exitosamente!")
            print(f"📋 ID: {webhook_id}")
            print(f"🌐 URL: {ngrok_url}/trello-events")
            return True
        else:
            print(f"❌ Error de Trello: {response.status_code}")
            print(f"📋 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creando webhook: {e}")
        return False

def setup_webhook_manual():
    """Configuración manual del webhook"""
    print("\n🌐 CONFIGURACIÓN MANUAL DEL WEBHOOK")
    print("=" * 50)
    
    print("💡 Para obtener la URL de ngrok:")
    print("1. Abre una NUEVA terminal como Administrador")
    print("2. Navega a esta carpeta:")
    print(f"   cd {os.getcwd()}")
    print("3. Ejecuta: ngrok.exe http 8050")
    print("4. Copia la URL HTTPS que aparece (ej: https://abcd-1234.ngrok-free.app)")
    print()
    
    ngrok_url = input("Pega la URL de ngrok aquí: ").strip()
    
    # Asegurar que la URL tenga el formato correcto
    if not ngrok_url.startswith(('http://', 'https://')):
        ngrok_url = 'https://' + ngrok_url
    
    if not ngrok_url.startswith("https://"):
        print("❌ URL debe empezar con https://")
        return
    
    # Configurar webhook
    load_dotenv()
    api_key = os.getenv('TRELLO_API_KEY')
    token = os.getenv('TRELLO_API_TOKEN')
    board_id = "68c366e3edf05392b3ce4c7d"
    
    if not api_key or not token:
        print("❌ Faltan API_KEY o TOKEN en el archivo .env")
        return
    
    url = f"https://api.trello.com/1/tokens/{token}/webhooks/?key={api_key}"
    payload = {
        "description": "Trello-Slack Bot Windows",
        "callbackURL": f"{ngrok_url}/trello-events",
        "idModel": board_id
    }
    
    try:
        print("⚙️ Creando webhook en Trello...")
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print("✅ Webhook creado exitosamente!")
            print(f"🌐 URL: {ngrok_url}/trello-events")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_connections():
    """Verifica todas las conexiones"""
    load_dotenv()
    
    print("\n🔍 VERIFICANDO CONEXIONES")
    print("=" * 50)
    
    # Verificar Trello
    try:
        api_key = os.getenv('TRELLO_API_KEY')
        token = os.getenv('TRELLO_API_TOKEN')
        
        if not api_key or not token:
            print("❌ Trello: Faltan API_KEY o TOKEN")
        else:
            response = requests.get(
                f"https://api.trello.com/1/members/me?key={api_key}&token={token}",
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Trello: Conectado correctamente")
            else:
                print(f"❌ Trello: Error {response.status_code}")
    except Exception as e:
        print(f"❌ Trello: Error de conexión - {e}")
    
    # Verificar otras APIs
    openai_key = os.getenv('OPENAI_API_KEY')
    slack_key = os.getenv('SLACK_APP_BOT_KEY')
    
    print(f"✅ OpenAI: {'Configurado' if openai_key else 'No configurado'}")
    print(f"✅ Slack: {'Configurado' if slack_key else 'No configurado'}")
    print(f"✅ Ngrok: {'Disponible' if check_ngrok() else 'No disponible'}")

def main():
    print("🤖 INICIADOR DEL BOT TRELLO-SLACK")
    print("=" * 50)
    print(f"📂 Directorio actual: {os.getcwd()}")
    
    # Verificar ngrok
    if not check_ngrok():
        print("\n❌ Ngrok no está disponible")
        print("💡 Asegúrate de que:")
        print("   1. ngrok.exe esté en la misma carpeta que este script")
        print("   2. Hayas ejecutado: ngrok config add-authtoken TU_TOKEN")
        return
    
    # Mostrar opciones
    print("\n🎯 OPCIONES DISPONIBLES:")
    print("1. Configuración automática completa")
    print("2. Configuración manual del webhook")
    print("3. Solo verificar conexiones")
    print("4. Solo iniciar ngrok (para testing)")
    
    choice = input("\nSelecciona una opción (1-4): ").strip()
    
    if choice == "1":
        if setup_webhook_auto():
            print("\n🎉 ¡Configuración automática exitosa!")
        else:
            print("\n❌ Falló la configuración automática")
            retry = input("¿Intentar configuración manual? (s/n): ").lower()
            if retry == 's':
                setup_webhook_manual()
    
    elif choice == "2":
        setup_webhook_manual()
    
    elif choice == "3":
        check_connections()
    
    elif choice == "4":
        print("🚀 Iniciando solo ngrok...")
        process = run_ngrok(8050)
        if process:
            print("✅ Ngrok ejecutándose. Presiona Ctrl+C para detenerlo.")
            try:
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                print("⏹️ Ngrok detenido")
    
    print("\n" + "=" * 50)
    print("📋 INSTRUCCIONES FINALES:")
    print("1. Deja ngrok ejecutándose")
    print("2. En otra terminal, ejecuta: python src/api.py")
    print("3. ¡Tu bot debería estar funcionando!")
    print("=" * 50)

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import requests
    except ImportError:
        print("❌ Faltan dependencias. Instala con:")
        print("   pip install requests python-dotenv")
        sys.exit(1)
    
    ensure_ngrok_authtoken()
    main()