"""Esquemas Pydantic para solicitudes y respuestas de la API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Consulta en lenguaje natural")
    limit: int = Field(default=5, ge=1, le=50, description="Número máximo de resultados")
    only_full_content: bool = Field(
        default=True,
        description="Filtrar únicamente documentos con contenido completo",
    )


class DocumentHit(BaseModel):
    title: str
    abstract: str
    content_preview: str
    link: Optional[str]
    certainty: Optional[float]
    full_abstract: str
    full_content: str


class SearchResponse(BaseModel):
    items: list[DocumentHit]


class TitleRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000, description="Texto base para generar título")


class TitleResponse(BaseModel):
    title: str
    source: str = Field(description="Motor utilizado para generar el título")


class GraphRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Consulta Cypher personalizada (opcional)")
    limit: int = Field(default=100, ge=1, le=1000, description="Límite de nodos a retornar")


class GraphNode(BaseModel):
    id: int
    labels: list[str]
    properties: dict


class GraphRelationship(BaseModel):
    id: int
    type: str
    start_node: int
    end_node: int
    properties: dict


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    relationships: list[GraphRelationship]
    count: dict[str, int]


class InsightRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Consulta original de búsqueda")
    limit: int = Field(default=5, ge=1, le=20, description="Número máximo de papers a analizar")
    only_full_content: bool = Field(
        default=True,
        description="Filtrar únicamente documentos con contenido completo",
    )


class Reference(BaseModel):
    id: int = Field(description="Número de referencia en el texto")
    title: str = Field(description="Título del paper")
    link: Optional[str] = Field(description="URL del paper")
    certainty: Optional[float] = Field(description="Relevancia del paper (0-1)")


class InsightResponse(BaseModel):
    insight: str = Field(description="Insight consolidado con referencias numeradas [1], [2], etc.")
    references: list[Reference] = Field(description="Lista de referencias citadas en el insight")
    papers_analyzed: int = Field(description="Número de papers analizados")
    source: str = Field(description="Modelo usado para generar el insight")
