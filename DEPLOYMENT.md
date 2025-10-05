# Guía de Despliegue - NASA 2025 Backend

Esta guía detalla paso a paso cómo desplegar el backend en Google Cloud Run.

## 📋 Prerequisitos

### 1. Cuenta y Proyecto de Google Cloud
- Cuenta de Google Cloud activa
- Proyecto creado en GCP
- Facturación habilitada

### 2. Herramientas instaladas
```bash
# Instalar Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Verificar instalación
gcloud --version
```

### 3. APIs de Google Cloud habilitadas
```bash
# Habilitar APIs necesarias
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## 🔐 Configuración de Secretos

### Crear secretos en Google Secret Manager:

```bash
# 1. Neo4j Password
echo -n "gOdJf1bLT5yvLk2akFL69vwc7E0yBzZ7uNwXbbvuxlY" | \
  gcloud secrets create neo4j-password \
  --data-file=- \
  --replication-policy="automatic"

# 2. Weaviate API Key
echo -n "YOUR_WEAVIATE_API_KEY" | \
  gcloud secrets create weaviate-api-key \
  --data-file=- \
  --replication-policy="automatic"

# 3. OpenAI API Key
echo -n "YOUR_OPENAI_API_KEY" | \
  gcloud secrets create openai-api-key \
  --data-file=- \
  --replication-policy="automatic"

# 4. Anthropic API Key (opcional)
echo -n "YOUR_ANTHROPIC_API_KEY" | \
  gcloud secrets create anthropic-api-key \
  --data-file=- \
  --replication-policy="automatic"
```

### Verificar secretos creados:
```bash
gcloud secrets list
```

## 🚀 Despliegue

### Opción 1: Despliegue con Cloud Build (Recomendado)

```bash
# Desde la carpeta backend/
gcloud builds submit --config cloudbuild.yaml
```

### Opción 2: Despliegue Manual

#### Paso 1: Build de la imagen
```bash
# Establecer PROJECT_ID
export PROJECT_ID=$(gcloud config get-value project)

# Build de la imagen
gcloud builds submit --tag gcr.io/$PROJECT_ID/nasa-backend
```

#### Paso 2: Deploy a Cloud Run
```bash
gcloud run deploy nasa-backend \
  --image gcr.io/$PROJECT_ID/nasa-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars \
NEO4J_URI=neo4j+s://e8421c26.databases.neo4j.io,\
NEO4J_USERNAME=neo4j,\
NEO4J_DATABASE=neo4j,\
WEAVIATE_URL=YOUR_WEAVIATE_URL,\
COLLECTION_NAME=ScientificPapersFullContent,\
USE_CLOUD=true \
  --set-secrets \
NEO4J_PASSWORD=neo4j-password:latest,\
WEAVIATE_API_KEY=weaviate-api-key:latest,\
OPENAI_API_KEY=openai-api-key:latest,\
ANTHROPIC_API_KEY=anthropic-api-key:latest
```

## 🔍 Verificación del Despliegue

### 1. Obtener URL del servicio
```bash
export SERVICE_URL=$(gcloud run services describe nasa-backend \
  --region us-central1 \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 2. Probar endpoints

#### Health Check
```bash
curl $SERVICE_URL/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "collection": "ScientificPapersFullContent",
  "use_cloud": true
}
```

#### Búsqueda de documentos
```bash
curl -X POST $SERVICE_URL/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Mars exploration",
    "limit": 3,
    "only_full_content": true
  }'
```

#### Consulta al grafo Neo4j
```bash
curl -X POST $SERVICE_URL/graph \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10
  }'
```

#### Generación de título
```bash
curl -X POST $SERVICE_URL/title \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a research about space exploration and Mars missions"
  }'
```

## 📊 Monitoreo y Logs

### Ver logs en tiempo real
```bash
gcloud run services logs read nasa-backend \
  --region us-central1 \
  --follow
```

### Ver logs recientes
```bash
gcloud run services logs read nasa-backend \
  --region us-central1 \
  --limit 50
```

### Métricas en Cloud Console
https://console.cloud.google.com/run/detail/us-central1/nasa-backend

## 🔄 Actualización del Servicio

### Actualizar código y redesplegar
```bash
# Opción 1: Con Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Opción 2: Manual
gcloud builds submit --tag gcr.io/$PROJECT_ID/nasa-backend
gcloud run deploy nasa-backend \
  --image gcr.io/$PROJECT_ID/nasa-backend \
  --region us-central1
```

### Actualizar variables de entorno
```bash
gcloud run services update nasa-backend \
  --region us-central1 \
  --update-env-vars KEY=VALUE
```

### Actualizar secretos
```bash
# Crear nueva versión del secreto
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# El servicio usará automáticamente :latest
```

## 🛡️ Seguridad y Permisos

### Service Account para Cloud Run
```bash
# Crear service account
gcloud iam service-accounts create nasa-backend-sa \
  --display-name="NASA Backend Service Account"

# Otorgar permisos para acceder a secretos
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:nasa-backend-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Usar el service account en el despliegue
gcloud run deploy nasa-backend \
  --service-account nasa-backend-sa@$PROJECT_ID.iam.gserviceaccount.com \
  [... otros parámetros ...]
```

### Restringir acceso (opcional)
```bash
# Requiere autenticación
gcloud run services update nasa-backend \
  --region us-central1 \
  --no-allow-unauthenticated
```

## 🌐 Configuración de Dominio Personalizado

### Mapear dominio
```bash
# Verificar dominio en GCP
gcloud domains verify DOMAIN.com

# Mapear a Cloud Run
gcloud run domain-mappings create \
  --service nasa-backend \
  --domain api.DOMAIN.com \
  --region us-central1
```

## 🐛 Troubleshooting

### Error: "Service account does not have permission"
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Error: "Container failed to start"
```bash
# Revisar logs
gcloud run services logs read nasa-backend --region us-central1 --limit 100

# Verificar variables de entorno
gcloud run services describe nasa-backend --region us-central1
```

### Error: "Neo4j connection timeout"
- Verificar que la instancia Neo4j Aura esté activa
- Esperar 60 segundos después de crear la instancia
- Verificar credenciales en Secret Manager

### Error de memoria/timeout
```bash
# Aumentar recursos
gcloud run services update nasa-backend \
  --region us-central1 \
  --memory 1Gi \
  --timeout 600
```

## 💰 Estimación de Costos

Cloud Run cobra por:
- **Tiempo de ejecución**: ~$0.00002400/vCPU-segundo
- **Memoria**: ~$0.00000250/GiB-segundo
- **Requests**: Primeros 2M gratis/mes

Estimación mensual (uso moderado):
- ~100K requests/mes
- ~500Mi memoria
- ~1 vCPU
- **Costo aproximado**: $5-15/mes

## 📝 Checklist de Despliegue

- [ ] Proyecto GCP creado y configurado
- [ ] APIs habilitadas (Cloud Run, Cloud Build, Secret Manager)
- [ ] Secretos creados en Secret Manager
- [ ] Código subido al repositorio
- [ ] Imagen Docker construida
- [ ] Servicio desplegado en Cloud Run
- [ ] Health check verificado
- [ ] Endpoints probados
- [ ] Logs revisados
- [ ] Documentación actualizada

## 🔗 Enlaces Útiles

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Neo4j Aura Console](https://console.neo4j.io)
- [Repositorio GitHub](https://github.com/KevinFernandez21/nasa2025_backend)
