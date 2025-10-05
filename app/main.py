"""Punto de entrada de la API FastAPI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.dependencies import get_document_service, shutdown_document_service
from app.models import (
    GraphRequest,
    GraphResponse,
    InsightRequest,
    InsightResponse,
    SearchRequest,
    SearchResponse,
    TitleRequest,
    TitleResponse,
)
from app.services.document_service import DocumentService
from app.services.insights_service import InsightsService
from app.services.neo4j_service import Neo4jService

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        shutdown_document_service()


app = FastAPI(
    title="Scientific Papers API",
    version="0.1.0",
    description="API para buscar papers en Weaviate y generar títulos sugeridos",
    lifespan=lifespan,
)

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=dict)
async def health(settings: Settings = Depends(get_settings)) -> dict:
    """Estado mínimo del servicio y configuración visible."""

    return {
        "status": "ok",
        "collection": settings.collection_name,
        "use_cloud": settings.use_cloud,
    }


@app.post("/search", response_model=SearchResponse)
async def search_documents(
    payload: SearchRequest,
    service: DocumentService = Depends(get_document_service),
) -> SearchResponse:
    """Busca documentos similares al texto proporcionado."""

    try:
        hits = service.search_documents(
            query=payload.query,
            limit=payload.limit,
            only_full_content=payload.only_full_content,
        )
    except Exception as exc:  # pragma: no cover - análisis de errores real depende de Weaviate
        logger.exception("Error durante la búsqueda")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return SearchResponse(items=hits)


@app.post("/title", response_model=TitleResponse)
async def generate_title(
    payload: TitleRequest,
    service: DocumentService = Depends(get_document_service),
) -> TitleResponse:
    """Genera un título editorial basado en el texto del usuario."""

    try:
        title, source = service.generate_title(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - proveedores externos
        logger.exception("Error generando título")
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TitleResponse(title=title, source=source)


@app.post("/graph", response_model=GraphResponse)
async def get_graph(
    payload: GraphRequest,
    settings: Settings = Depends(get_settings),
) -> GraphResponse:
    """Obtiene datos del grafo de Neo4j."""

    neo4j_service = None
    try:
        neo4j_service = Neo4jService(settings)
        graph_data = neo4j_service.get_graph_data(
            query=payload.query,
            limit=payload.limit,
        )
        return GraphResponse(**graph_data)
    except Exception as exc:
        logger.exception("Error obteniendo datos del grafo")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        if neo4j_service:
            neo4j_service.close()


@app.post("/search/insights", response_model=InsightResponse)
async def generate_insights(
    payload: InsightRequest,
    document_service: DocumentService = Depends(get_document_service),
    settings: Settings = Depends(get_settings),
) -> InsightResponse:
    """Genera un insight consolidado de los papers más relevantes para una búsqueda."""

    try:
        # Primero, buscar los papers más relevantes
        papers = document_service.search_documents(
            query=payload.query,
            limit=payload.limit,
            only_full_content=payload.only_full_content,
        )

        if not papers:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron papers relevantes para la búsqueda",
            )

        # Crear el servicio de insights
        insights_service = InsightsService(openai_api_key=settings.openai_api_key)

        # Generar el insight
        insight_text = insights_service.generate_insight(
            query=payload.query,
            papers=papers,
            max_papers=payload.limit,
        )

        # Determinar qué modelo se usó
        source = "openai" if settings.openai_api_key else "fallback"

        return InsightResponse(
            insight=insight_text,
            papers_analyzed=len(papers),
            source=source,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error generando insights")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
