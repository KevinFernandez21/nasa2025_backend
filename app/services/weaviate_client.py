"""Utilidades para crear y reutilizar clientes de Weaviate."""

from __future__ import annotations

import threading
from urllib.parse import urlparse

import weaviate
from weaviate import connect_to_weaviate_cloud, connect_to_local
from weaviate.util import generate_uuid5

from app.config import Settings

_client_lock = threading.Lock()
_client_instance: weaviate.WeaviateClient | None = None


def _normalize_cluster_url(raw_url: str) -> str:
    """Asegura que la URL incluya un esquema."""

    parsed = urlparse(raw_url)
    if not parsed.scheme:
        return f"https://{raw_url}"
    return raw_url


def get_weaviate_client(settings: Settings) -> weaviate.WeaviateClient:
    """Crea (o reutiliza) un cliente de Weaviate seguro para threads."""

    global _client_instance
    if _client_instance is not None:
        return _client_instance

    with _client_lock:
        if _client_instance is not None:
            return _client_instance

        headers: dict[str, str] = {}
        if settings.cohere_api_key:
            headers["X-Cohere-Api-Key"] = settings.cohere_api_key

        if settings.use_cloud:
            cluster_url = _normalize_cluster_url(settings.weaviate_url)
            _client_instance = connect_to_weaviate_cloud(
                cluster_url=cluster_url,
                auth_credentials=weaviate.auth.AuthApiKey(settings.weaviate_api_key),
                headers=headers or None,
            )
        else:
            parsed = urlparse(settings.weaviate_url)
            host = parsed.hostname or settings.weaviate_url
            port = parsed.port or 8080
            _client_instance = connect_to_local(
                host=host,
                port=port,
                headers=headers or None,
            )

        return _client_instance


def close_client() -> None:
    """Cierra la conexión compartida."""

    global _client_instance
    with _client_lock:
        if _client_instance is not None:
            _client_instance.close()
            _client_instance = None


__all__ = ["get_weaviate_client", "close_client", "generate_uuid5"]
