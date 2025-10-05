"""Flujos de ingestión y carga de papers a Weaviate."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from weaviate.classes.config import Configure, DataType, Property
from weaviate.client import WeaviateClient

from app.services.pubmed_extractor import process_papers_with_content

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lectura y almacenamiento
# ---------------------------------------------------------------------------

def load_publications_csv(path: str | Path) -> pd.DataFrame:
    """Carga un archivo CSV con columnas `Title` y `Link`."""

    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"No se encontró el archivo {resolved}")

    logger.info("Cargando publicaciones desde %s", resolved)
    return pd.read_csv(resolved)


def enrich_publications(
    dataframe: pd.DataFrame,
    *,
    max_papers: int | None = None,
    delay_seconds: float = 2.0,
    timeout_seconds: int = 30,
) -> pd.DataFrame:
    """Devuelve un dataframe enriquecido con contenido completo."""

    return process_papers_with_content(
        dataframe,
        max_papers=max_papers,
        delay_seconds=delay_seconds,
        timeout_seconds=timeout_seconds,
    )


def save_enriched_publications(dataframe: pd.DataFrame, path: str | Path) -> Path:
    """Guarda el dataframe enriquecido en disco."""

    resolved = Path(path)
    dataframe.to_csv(resolved, index=False)
    logger.info("Datos enriquecidos guardados en %s", resolved)
    return resolved


# ---------------------------------------------------------------------------
# Weaviate helpers
# ---------------------------------------------------------------------------

def recreate_collection(client: WeaviateClient, collection_name: str) -> None:
    """Elimina y reconstruye la colección objetivo."""

    try:
        client.collections.delete(collection_name)
        logger.info("Colección %s eliminada", collection_name)
    except Exception:  # pragma: no cover - errores de API
        logger.debug("Colección %s no existía", collection_name)

    client.collections.create(
        name=collection_name,
        vectorizer_config=Configure.Vectorizer.text2vec_cohere(
            model="embed-multilingual-v3.0",
            vectorize_collection_name=False,
        ),
        properties=[
            Property(
                name="title",
                data_type=DataType.TEXT,
                description="Título del paper",
            ),
            Property(
                name="abstract",
                data_type=DataType.TEXT,
                description="Abstract del paper",
            ),
            Property(
                name="content",
                data_type=DataType.TEXT,
                description="Contenido completo del paper",
            ),
            Property(
                name="link",
                data_type=DataType.TEXT,
                description="URL del paper",
                skip_vectorization=True,
            ),
            Property(
                name="paperIndex",
                data_type=DataType.INT,
                skip_vectorization=True,
            ),
            Property(
                name="hasFullContent",
                data_type=DataType.BOOL,
                description="Si se pudo extraer contenido completo",
                skip_vectorization=True,
            ),
        ],
    )

    logger.info("Colección %s creada", collection_name)


def upsert_papers(
    dataframe: pd.DataFrame,
    client: WeaviateClient,
    collection_name: str,
) -> tuple[int, int]:
    """Inserta los registros en batch usando la colección especificada."""

    collection = client.collections.get(collection_name)

    inserted = 0
    errors = 0

    with collection.batch.dynamic() as batch:
        for idx, row in dataframe.iterrows():
            paper = {
                "title": row["extracted_title"] if row.get("success") else row.get("original_title"),
                "abstract": row["abstract"] if row.get("success") else "",
                "content": row["content"] if row.get("success") else "",
                "link": row.get("link"),
                "paperIndex": int(row.get("paperIndex", idx)),
                "hasFullContent": bool(row.get("success")),
            }

            try:
                batch.add_object(properties=paper)
                inserted += 1
            except Exception as exc:  # pragma: no cover - API externa
                errors += 1
                logger.exception("Error insertando paper %s: %s", idx, exc)

    logger.info("Inserción completada | insertados=%s | errores=%s", inserted, errors)
    return inserted, errors


def count_papers(client: WeaviateClient, collection_name: str) -> int:
    """Devuelve el total de objetos almacenados en la colección."""

    collection = client.collections.get(collection_name)
    total = collection.aggregate.over_all(total_count=True)
    return int(total.total_count)
