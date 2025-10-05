# NASA 2025 Backend API

API backend para el proyecto NASA Bioscience 2025. Proporciona endpoints para búsqueda semántica de documentos científicos, generación de títulos con IA y consultas a grafos de conocimiento en Neo4j.

[![Deploy to Cloud Run](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

## Características

- 🔍 **Búsqueda semántica** de papers científicos usando Weaviate
- 🤖 **Generación de títulos** con OpenAI/Anthropic
- 📊 **Consultas a grafos** de conocimiento con Neo4j
- 🐳 **Docker** listo para despliegue
- ☁️ **Google Cloud Run** compatible
- 📚 **OpenAPI/Swagger** documentación interactiva
- 🔐 **Secret Manager** para credenciales seguras

## Endpoints

### `GET /health`
Verifica el estado del servicio

### `POST /search`
Búsqueda semántica de documentos científicos
```json
{
  "query": "Mars exploration",
  "limit": 5,
  "only_full_content": true
}
```

### `POST /title`
Genera un título editorial basado en texto
```json
{
  "text": "Your text here..."
}
```

### `POST /graph`
Obtiene datos del grafo de Neo4j
```json
{
  "query": "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100",
  "limit": 100
}
```

## 🚀 Inicio Rápido

### Opción 1: Script Automático
```bash
git clone git@github.com:KevinFernandez21/nasa2025_backend.git
cd nasa2025_backend
./setup.sh
```

### Opción 2: Manual

#### Requisitos
- Python 3.12+
- Docker (opcional)

#### Configuración

1. Clonar el repositorio:
```bash
git clone git@github.com:KevinFernandez21/nasa2025_backend.git
cd nasa2025_backend
```

2. Crear archivo `.env` basado en `.env.example`:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

3. Ejecutar localmente

**Con Python:**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

**Con Docker:**
```bash
docker-compose up --build
```

La API estará disponible en:
- **API:** `http://localhost:8080`
- **Docs (Swagger):** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`

## Despliegue en Google Cloud Run

### Prerequisitos
- Cuenta de Google Cloud
- `gcloud` CLI instalado y configurado
- Proyecto de GCP creado

### Pasos de despliegue

1. **Autenticar con Google Cloud:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. **Crear secretos en Secret Manager:**
```bash
# Neo4j password
echo -n "gOdJf1bLT5yvLk2akFL69vwc7E0yBzZ7uNwXbbvuxlY" | gcloud secrets create neo4j-password --data-file=-

# Weaviate API Key
echo -n "YOUR_WEAVIATE_KEY" | gcloud secrets create weaviate-api-key --data-file=-

# OpenAI API Key
echo -n "YOUR_OPENAI_KEY" | gcloud secrets create openai-api-key --data-file=-
```

3. **Desplegar con Cloud Build:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

**O despliegue manual:**
```bash
# Build y push de imagen
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/nasa-backend

# Deploy a Cloud Run
gcloud run deploy nasa-backend \
  --image gcr.io/YOUR_PROJECT_ID/nasa-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars NEO4J_URI=neo4j+s://e8421c26.databases.neo4j.io,NEO4J_USERNAME=neo4j,NEO4J_DATABASE=neo4j \
  --set-secrets NEO4J_PASSWORD=neo4j-password:latest,WEAVIATE_API_KEY=weaviate-api-key:latest,OPENAI_API_KEY=openai-api-key:latest
```

4. **Verificar despliegue:**
```bash
# Obtener URL del servicio
gcloud run services describe nasa-backend --region us-central1 --format='value(status.url)'

# Probar health check
curl https://YOUR_SERVICE_URL/health
```

## Configuración de Variables de Entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `WEAVIATE_URL` | URL de Weaviate | Sí |
| `WEAVIATE_API_KEY` | API Key de Weaviate | Sí |
| `COLLECTION_NAME` | Nombre de la colección | No (default: ScientificPapersFullContent) |
| `USE_CLOUD` | Usar Weaviate Cloud | No (default: true) |
| `NEO4J_URI` | URI de Neo4j | Sí |
| `NEO4J_USERNAME` | Usuario de Neo4j | Sí |
| `NEO4J_PASSWORD` | Contraseña de Neo4j | Sí |
| `NEO4J_DATABASE` | Base de datos Neo4j | No (default: neo4j) |
| `OPENAI_API_KEY` | API Key de OpenAI | Sí |

## Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app y endpoints
│   ├── config.py            # Configuración y settings
│   ├── dependencies.py      # Dependency injection
│   ├── models.py            # Modelos Pydantic
│   ├── services/
│   │   ├── document_service.py
│   │   ├── neo4j_service.py
│   │   ├── pubmed_extractor.py
│   │   └── weaviate_client.py
│   └── workflows/
│       └── ingestion.py
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
├── cloudbuild.yaml
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

```bash
pytest tests/
```

## Monitoreo y Logs

Ver logs en Cloud Run:
```bash
gcloud run services logs read nasa-backend --region us-central1
```

## 📚 Documentación Completa

- **[API_REFERENCE.md](API_REFERENCE.md)** - Documentación detallada de todos los endpoints
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guía completa de despliegue en Google Cloud
- **[COMMANDS.md](COMMANDS.md)** - Referencia rápida de comandos útiles

## Troubleshooting

### Error de conexión a Neo4j
- Verificar que las credenciales sean correctas
- Asegurarse que la instancia de Neo4j Aura esté activa
- Esperar 60 segundos después de crear la instancia

### Error de permisos en Secret Manager
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

MIT

## 🔗 Enlaces Útiles

- [Repositorio GitHub](https://github.com/KevinFernandez21/nasa2025_backend)
- [Neo4j Aura Console](https://console.neo4j.io)
- [Google Cloud Console](https://console.cloud.google.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
