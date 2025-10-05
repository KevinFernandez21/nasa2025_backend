# API Reference - NASA 2025 Backend

Documentación completa de los endpoints de la API.

## Base URL

**Local:** `http://localhost:8080`
**Producción:** `https://nasa-backend-[HASH]-uc.a.run.app`

## Autenticación

Actualmente la API es pública. Para producción se recomienda implementar autenticación.

---

## Endpoints

### 🔍 Health Check

**GET** `/health`

Verifica el estado del servicio y la configuración.

#### Response
```json
{
  "status": "ok",
  "collection": "ScientificPapersFullContent",
  "use_cloud": true
}
```

#### Códigos de estado
- `200 OK`: Servicio funcionando correctamente

---

### 📚 Búsqueda de Documentos

**POST** `/search`

Búsqueda semántica de documentos científicos en Weaviate.

#### Request Body
```json
{
  "query": "Mars exploration and habitability",
  "limit": 5,
  "only_full_content": true
}
```

| Campo | Tipo | Requerido | Default | Descripción |
|-------|------|-----------|---------|-------------|
| `query` | string | ✅ | - | Consulta en lenguaje natural (mín. 3 caracteres) |
| `limit` | integer | ❌ | 5 | Número de resultados (1-50) |
| `only_full_content` | boolean | ❌ | true | Filtrar solo documentos con contenido completo |

#### Response
```json
{
  "items": [
    {
      "title": "Mars Exploration Program",
      "abstract": "Study of Mars surface...",
      "content_preview": "Mars has been a subject of...",
      "link": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
      "certainty": 0.89,
      "full_abstract": "Complete abstract text...",
      "full_content": "Full document content..."
    }
  ]
}
```

#### DocumentHit Schema
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `title` | string | Título del documento |
| `abstract` | string | Resumen del documento |
| `content_preview` | string | Vista previa del contenido |
| `link` | string\|null | URL al documento original |
| `certainty` | float\|null | Nivel de confianza (0-1) |
| `full_abstract` | string | Abstract completo |
| `full_content` | string | Contenido completo |

#### Códigos de estado
- `200 OK`: Búsqueda exitosa
- `400 Bad Request`: Parámetros inválidos
- `502 Bad Gateway`: Error en Weaviate

#### Ejemplo cURL
```bash
curl -X POST http://localhost:8080/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "microbial life in extreme environments",
    "limit": 3,
    "only_full_content": true
  }'
```

---

### 📝 Generación de Títulos

**POST** `/title`

Genera un título editorial basado en texto usando IA (OpenAI/Anthropic).

#### Request Body
```json
{
  "text": "This research explores the potential for microbial life on Mars by analyzing extremophile bacteria on Earth..."
}
```

| Campo | Tipo | Requerido | Límites | Descripción |
|-------|------|-----------|---------|-------------|
| `text` | string | ✅ | 3-5000 caracteres | Texto base para generar el título |

#### Response
```json
{
  "title": "Exploring Martian Habitability Through Extremophile Research",
  "source": "openai"
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `title` | string | Título generado |
| `source` | string | Motor utilizado (openai/anthropic) |

#### Códigos de estado
- `200 OK`: Título generado exitosamente
- `400 Bad Request`: Texto inválido (muy corto/largo)
- `502 Bad Gateway`: Error en el proveedor de IA

#### Ejemplo cURL
```bash
curl -X POST http://localhost:8080/title \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Analysis of soil samples from Mars rovers suggests the presence of organic compounds that could indicate past microbial activity"
  }'
```

---

### 🕸️ Consulta de Grafos Neo4j

**POST** `/graph`

Obtiene datos del grafo de conocimiento desde Neo4j.

#### Request Body

**Consulta básica (sin query personalizada):**
```json
{
  "limit": 100
}
```

**Consulta personalizada (Cypher):**
```json
{
  "query": "MATCH (n:Organism)-[r:LIVES_IN]->(e:Environment) RETURN n, r, e LIMIT 50",
  "limit": 50
}
```

| Campo | Tipo | Requerido | Default | Límites | Descripción |
|-------|------|-----------|---------|---------|-------------|
| `query` | string\|null | ❌ | null | - | Consulta Cypher personalizada |
| `limit` | integer | ❌ | 100 | 1-1000 | Límite de nodos a retornar |

#### Response
```json
{
  "nodes": [
    {
      "id": 123,
      "labels": ["Organism", "Bacteria"],
      "properties": {
        "name": "Deinococcus radiodurans",
        "type": "extremophile",
        "discovered": 1956
      }
    },
    {
      "id": 456,
      "labels": ["Environment"],
      "properties": {
        "name": "Radiation-rich",
        "intensity": "high"
      }
    }
  ],
  "relationships": [
    {
      "id": 789,
      "type": "LIVES_IN",
      "start_node": 123,
      "end_node": 456,
      "properties": {
        "since": 1956,
        "confirmed": true
      }
    }
  ],
  "count": {
    "nodes": 2,
    "relationships": 1
  }
}
```

#### GraphNode Schema
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | integer | ID único del nodo en Neo4j |
| `labels` | array[string] | Etiquetas del nodo |
| `properties` | object | Propiedades del nodo |

#### GraphRelationship Schema
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | integer | ID único de la relación |
| `type` | string | Tipo de relación |
| `start_node` | integer | ID del nodo origen |
| `end_node` | integer | ID del nodo destino |
| `properties` | object | Propiedades de la relación |

#### Códigos de estado
- `200 OK`: Consulta exitosa
- `400 Bad Request`: Query Cypher inválida
- `502 Bad Gateway`: Error en Neo4j

#### Ejemplos cURL

**Consulta básica:**
```bash
curl -X POST http://localhost:8080/graph \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 20
  }'
```

**Consulta Cypher personalizada:**
```bash
curl -X POST http://localhost:8080/graph \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (o:Organism)-[r]->(e:Environment) WHERE e.type = \"extreme\" RETURN o, r, e",
    "limit": 50
  }'
```

---

## Manejo de Errores

Todos los errores siguen el formato estándar de FastAPI:

```json
{
  "detail": "Error message description"
}
```

### Códigos de Error Comunes

| Código | Significado | Posibles Causas |
|--------|-------------|-----------------|
| 400 | Bad Request | Parámetros inválidos, validación fallida |
| 404 | Not Found | Endpoint no existe |
| 422 | Unprocessable Entity | Error de validación de Pydantic |
| 502 | Bad Gateway | Error en servicios externos (Weaviate, Neo4j, OpenAI) |
| 500 | Internal Server Error | Error del servidor |

---

## Límites y Cuotas

| Recurso | Límite | Nota |
|---------|--------|------|
| Tamaño de request | 10 MB | - |
| Timeout | 300s | Configurable en Cloud Run |
| Límite de búsqueda | 50 documentos | Por request |
| Límite de grafo | 1000 nodos | Por request |
| Longitud de texto (title) | 5000 caracteres | - |
| Query mínima (search) | 3 caracteres | - |

---

## Ejemplos de Integración

### Python
```python
import requests

# Búsqueda de documentos
response = requests.post(
    "http://localhost:8080/search",
    json={
        "query": "Mars exploration",
        "limit": 5,
        "only_full_content": True
    }
)
results = response.json()

# Generar título
response = requests.post(
    "http://localhost:8080/title",
    json={"text": "Your research text here..."}
)
title_data = response.json()

# Consultar grafo
response = requests.post(
    "http://localhost:8080/graph",
    json={"limit": 100}
)
graph_data = response.json()
```

### JavaScript/TypeScript
```typescript
// Búsqueda de documentos
const searchResponse = await fetch('http://localhost:8080/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Mars exploration',
    limit: 5,
    only_full_content: true
  })
});
const results = await searchResponse.json();

// Generar título
const titleResponse = await fetch('http://localhost:8080/title', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Your research text here...'
  })
});
const titleData = await titleResponse.json();

// Consultar grafo
const graphResponse = await fetch('http://localhost:8080/graph', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ limit: 100 })
});
const graphData = await graphResponse.json();
```

---

## OpenAPI/Swagger

La documentación interactiva está disponible en:

- **Swagger UI:** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`
- **OpenAPI JSON:** `http://localhost:8080/openapi.json`
