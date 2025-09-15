# Usar imagen oficial de Python 3.10 (más estable para producción)
FROM python:3.10-slim

# Evitar que Python genere archivos .pyc en el contenedor
ENV PYTHONDONTWRITEBYTECODE=1

# Desactivar buffering para logs en tiempo real
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar pipenv y dependencias del sistema
RUN pip install -U pipenv

# Copiar archivos de dependencias primero (optimiza caché de Docker)
COPY Pipfile Pipfile.lock ./

# Instalar dependencias del proyecto
RUN pipenv install --system --deploy --ignore-pipfile

# Copiar todo el código del proyecto
COPY . /app

# Exponer el puerto que usa FastAPI
EXPOSE 8050

# Comando por defecto para producción
CMD ["python", "src/api.py"]

# Comando alternativo para desarrollo con hot reload:
# CMD ["watchmedo", "auto-restart", "-p", "*.py", "-R", "python", "src/api.py"]