# Dockerfile optimizado para Google Cloud Run
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno para optimización
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY ./app /app/app

# Exponer puerto (Cloud Run usa PORT env var)
ENV PORT=8080
EXPOSE 8080

# Comando para ejecutar la aplicación
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
