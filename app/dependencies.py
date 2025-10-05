"""Dependencias reutilizables para FastAPI."""

from __future__ import annotations

import threading

from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings
from app.services.document_service import DocumentService
from app.services.weaviate_client import close_client, get_weaviate_client

_document_service: DocumentService | None = None
_service_lock = threading.Lock()


def get_document_service(settings: Settings = Depends(get_settings)) -> DocumentService:
    """Retorna una instancia singleton de DocumentService."""

    global _document_service
    if _document_service is not None:
        return _document_service

    with _service_lock:
        if _document_service is not None:
            return _document_service

        try:
            client = get_weaviate_client(settings)
        except Exception as exc:  # pragma: no cover - inicialización externa
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar a Weaviate: {exc}",
            ) from exc

        _document_service = DocumentService(
            client=client,
            collection_name=settings.collection_name,
            cohere_api_key=settings.cohere_api_key,
            anthropic_api_key=settings.anthropic_api_key,
        )
        return _document_service


def shutdown_document_service() -> None:
    """Libera recursos mantenidos por los servicios."""

    global _document_service
    with _service_lock:
        _document_service = None
        close_client()
