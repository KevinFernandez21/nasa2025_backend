# Comandos Útiles - NASA 2025 Backend

Referencia rápida de comandos para desarrollo y despliegue.

## 🐳 Docker

### Desarrollo Local
```bash
# Build imagen
docker build -t nasa-backend .

# Ejecutar contenedor
docker run -p 8080:8080 --env-file .env nasa-backend

# Con docker-compose
docker-compose up -d
docker-compose logs -f
docker-compose down

# Rebuild
docker-compose up --build
```

### Limpieza
```bash
# Eliminar contenedores
docker-compose down -v

# Eliminar imágenes no usadas
docker image prune -a

# Limpiar todo
docker system prune -a --volumes
```

---

## ☁️ Google Cloud

### Autenticación y Configuración
```bash
# Login
gcloud auth login

# Configurar proyecto
gcloud config set project YOUR_PROJECT_ID

# Ver configuración actual
gcloud config list

# Listar proyectos
gcloud projects list
```

### Cloud Run

#### Deploy
```bash
# Deploy con Cloud Build
gcloud builds submit --config cloudbuild.yaml

# Deploy manual
gcloud run deploy nasa-backend \
  --image gcr.io/PROJECT_ID/nasa-backend \
  --region us-central1

# Deploy desde código fuente (buildpack)
gcloud run deploy nasa-backend \
  --source . \
  --region us-central1
```

#### Gestión
```bash
# Listar servicios
gcloud run services list

# Describir servicio
gcloud run services describe nasa-backend --region us-central1

# Obtener URL
gcloud run services describe nasa-backend \
  --region us-central1 \
  --format='value(status.url)'

# Eliminar servicio
gcloud run services delete nasa-backend --region us-central1
```

#### Logs y Monitoreo
```bash
# Ver logs en tiempo real
gcloud run services logs read nasa-backend \
  --region us-central1 \
  --follow

# Logs recientes
gcloud run services logs read nasa-backend \
  --region us-central1 \
  --limit 100

# Logs con filtro
gcloud run services logs read nasa-backend \
  --region us-central1 \
  --log-filter='severity>=ERROR'
```

#### Configuración
```bash
# Actualizar variables de entorno
gcloud run services update nasa-backend \
  --region us-central1 \
  --update-env-vars KEY1=value1,KEY2=value2

# Eliminar variable
gcloud run services update nasa-backend \
  --region us-central1 \
  --remove-env-vars KEY1

# Actualizar recursos
gcloud run services update nasa-backend \
  --region us-central1 \
  --memory 1Gi \
  --cpu 2 \
  --timeout 600 \
  --max-instances 10

# Rollback a revisión anterior
gcloud run services update-traffic nasa-backend \
  --to-revisions REVISION-001=100 \
  --region us-central1
```

### Secret Manager
```bash
# Listar secretos
gcloud secrets list

# Ver versiones de secreto
gcloud secrets versions list SECRET_NAME

# Crear secreto
echo -n "secret-value" | gcloud secrets create SECRET_NAME --data-file=-

# Actualizar secreto (nueva versión)
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Ver valor de secreto
gcloud secrets versions access latest --secret="SECRET_NAME"

# Eliminar secreto
gcloud secrets delete SECRET_NAME
```

### Container Registry
```bash
# Listar imágenes
gcloud container images list

# Ver tags de imagen
gcloud container images list-tags gcr.io/PROJECT_ID/nasa-backend

# Eliminar imagen
gcloud container images delete gcr.io/PROJECT_ID/nasa-backend:TAG
```

### Cloud Build
```bash
# Listar builds
gcloud builds list --limit=10

# Ver detalles de build
gcloud builds describe BUILD_ID

# Ver logs de build
gcloud builds log BUILD_ID

# Cancelar build
gcloud builds cancel BUILD_ID
```

---

## 🔍 Testing y Debugging

### Local
```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/

# Test específico
pytest tests/test_api.py::test_health_endpoint

# Modo verbose
pytest -v

# Debug con breakpoint
pytest --pdb
```

### Pruebas de API con cURL
```bash
# Health check
curl http://localhost:8080/health

# Búsqueda
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Mars", "limit": 3}'

# Título
curl -X POST http://localhost:8080/title \
  -H "Content-Type: application/json" \
  -d '{"text": "Research about Mars exploration"}'

# Grafo
curl -X POST http://localhost:8080/graph \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

### HTTPie (alternativa a cURL)
```bash
# Instalar: pip install httpie

# Health check
http GET http://localhost:8080/health

# Búsqueda
http POST http://localhost:8080/search \
  query="Mars exploration" \
  limit:=5 \
  only_full_content:=true

# Título
http POST http://localhost:8080/title \
  text="Research text here"
```

---

## 🗄️ Neo4j

### Cypher Queries
```bash
# Conectar a Neo4j (local)
cypher-shell -a neo4j://localhost:7687 -u neo4j -p password

# Conectar a Aura
cypher-shell -a neo4j+s://e8421c26.databases.neo4j.io -u neo4j -p PASSWORD
```

### Queries Útiles
```cypher
// Ver todos los nodos (limitado)
MATCH (n) RETURN n LIMIT 25;

// Contar nodos por tipo
MATCH (n) RETURN labels(n) as Type, count(*) as Count;

// Ver todas las relaciones
MATCH ()-[r]->() RETURN type(r) as RelationType, count(*) as Count;

// Buscar por propiedad
MATCH (n) WHERE n.name CONTAINS "Mars" RETURN n;

// Ver schema
CALL db.schema.visualization();

// Limpiar base de datos (¡CUIDADO!)
MATCH (n) DETACH DELETE n;
```

---

## 🐍 Python/FastAPI

### Servidor de Desarrollo
```bash
# Con uvicorn
uvicorn app.main:app --reload --port 8080

# Con logs detallados
uvicorn app.main:app --reload --log-level debug

# Múltiples workers (producción)
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Dependencias
```bash
# Instalar
pip install -r requirements.txt

# Actualizar
pip install --upgrade -r requirements.txt

# Generar requirements
pip freeze > requirements.txt

# Instalar en modo desarrollo
pip install -e .
```

### Formateo y Linting
```bash
# Black (formateo)
black app/

# isort (ordenar imports)
isort app/

# flake8 (linting)
flake8 app/

# mypy (type checking)
mypy app/
```

---

## 📝 Git

### Workflow Básico
```bash
# Status
git status

# Add cambios
git add .
git add archivo.py

# Commit
git commit -m "Descripción del cambio"

# Push
git push origin main

# Pull
git pull origin main
```

### Branches
```bash
# Crear branch
git checkout -b feature/nueva-funcionalidad

# Cambiar branch
git checkout main

# Listar branches
git branch -a

# Merge
git checkout main
git merge feature/nueva-funcionalidad

# Eliminar branch
git branch -d feature/nueva-funcionalidad
```

### Histórico y Debug
```bash
# Ver log
git log --oneline --graph

# Ver cambios
git diff

# Ver archivo en commit específico
git show COMMIT_HASH:path/to/file

# Revertir cambios
git checkout -- archivo.py

# Reset (¡CUIDADO!)
git reset --hard HEAD~1
```

---

## 🔧 Variables de Entorno

### Local
```bash
# Crear .env desde ejemplo
cp .env.example .env

# Editar
nano .env
# o
code .env
```

### Cloud Run
```bash
# Ver variables actuales
gcloud run services describe nasa-backend \
  --region us-central1 \
  --format='value(spec.template.spec.containers[0].env)'

# Actualizar
gcloud run services update nasa-backend \
  --region us-central1 \
  --set-env-vars VAR1=value1,VAR2=value2

# Desde archivo
gcloud run services update nasa-backend \
  --region us-central1 \
  --env-vars-file .env.prod
```

---

## 📊 Utilidades

### Performance
```bash
# Benchmark con ab (Apache Bench)
ab -n 1000 -c 10 http://localhost:8080/health

# Benchmark con wrk
wrk -t12 -c400 -d30s http://localhost:8080/health

# Load testing con locust
locust -f locustfile.py
```

### Networking
```bash
# Ver puertos en uso
lsof -i :8080

# Kill proceso en puerto
kill -9 $(lsof -ti:8080)

# Test conectividad
nc -zv localhost 8080
telnet localhost 8080
```

### Monitoreo de Recursos
```bash
# CPU/Memoria del contenedor
docker stats

# Logs del sistema
journalctl -u docker -f

# Disk usage
du -sh backend/
df -h
```

---

## 🚀 CI/CD

### Trigger manual de Cloud Build
```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=BRANCH_NAME=main
```

### GitHub Actions (ejemplo)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: google-github-actions/setup-gcloud@v0
        with:
          project_id: ${{ secrets.GCP_PROJECT }}
          service_account_key: ${{ secrets.GCP_SA_KEY }}
      - run: gcloud builds submit --config cloudbuild.yaml
```

---

## 📚 Documentación

### Ver docs interactivas
```bash
# Swagger UI
open http://localhost:8080/docs

# ReDoc
open http://localhost:8080/redoc

# OpenAPI JSON
curl http://localhost:8080/openapi.json | jq
```

---

## 🆘 Troubleshooting Rápido

```bash
# Verificar servicio corriendo
curl http://localhost:8080/health

# Ver logs en tiempo real
docker-compose logs -f

# Restart servicio
docker-compose restart

# Rebuild completo
docker-compose down && docker-compose up --build

# Verificar conectividad Neo4j
cypher-shell -a $NEO4J_URI -u $NEO4J_USERNAME -p $NEO4J_PASSWORD "RETURN 1"

# Test variables de entorno
python -c "from app.config import get_settings; print(get_settings())"
```
