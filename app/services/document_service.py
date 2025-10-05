"""Servicios de dominio para búsquedas y generación de títulos."""

from __future__ import annotations

import logging
import math
import re
from typing import Optional

from weaviate.classes.query import Filter, MetadataQuery
from weaviate.client import WeaviateClient

from app.models import DocumentHit

logger = logging.getLogger(__name__)


def _sanitize_title(text: str) -> str:
    sanitized = text.strip().strip('"').strip("'")
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized


class DocumentService:
    """Encapsula la interacción con Weaviate y motores generativos."""

    def __init__(
        self,
        *,
        client: WeaviateClient,
        collection_name: str,
        cohere_api_key: str | None = None,
        anthropic_api_key: str | None = None,
    ) -> None:
        self._client = client
        self._collection = client.collections.get(collection_name)
        self._cohere = self._build_cohere_client(cohere_api_key)
        self._anthropic = self._build_anthropic_client(anthropic_api_key)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def search_documents(
        self,
        *,
        query: str,
        limit: int = 5,
        only_full_content: bool = True,
    ) -> list[DocumentHit]:
        filters = None
        if only_full_content:
            filters = Filter.by_property("hasFullContent").equal(True)

        response = self._collection.query.near_text(
            query=query,
            limit=limit,
            filters=filters,
            return_metadata=MetadataQuery(certainty=True),
        )

        results: list[DocumentHit] = []
        for obj in response.objects:
            properties = obj.properties
            certainty = getattr(obj.metadata, "certainty", None)
            abstract = properties.get("abstract") or ""
            content = properties.get("content") or ""

            results.append(
                DocumentHit(
                    title=properties.get("title", ""),
                    abstract=_make_preview(abstract, 300),
                    content_preview=_make_preview(content, 500),
                    link=properties.get("link"),
                    certainty=float(certainty) if certainty is not None else None,
                    full_abstract=abstract,
                    full_content=content,
                )
            )

        return results

    # ------------------------------------------------------------------
    # Generación de títulos
    # ------------------------------------------------------------------
    def generate_title(self, text: str) -> tuple[str, str]:
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("El texto no puede estar vacío")

        if self._cohere is not None:
            title = self._generate_with_cohere(cleaned)
            if title:
                return title, "cohere"

        if self._anthropic is not None:
            title = self._generate_with_anthropic(cleaned)
            if title:
                return title, "anthropic"

        return self._generate_with_fallback(cleaned), "heuristic"

    # ------------------------------------------------------------------
    # Motores auxiliares
    # ------------------------------------------------------------------
    @staticmethod
    def _build_cohere_client(api_key: Optional[str]):
        if not api_key:
            return None
        try:
            import cohere

            return cohere.Client(api_key)
        except Exception as exc:  # pragma: no cover - sólo en entorno sin cohere
            logger.warning("No se pudo inicializar Cohere: %s", exc)
            return None

    @staticmethod
    def _build_anthropic_client(api_key: Optional[str]):
        if not api_key:
            return None
        try:
            from anthropic import Anthropic

            return Anthropic(api_key=api_key)
        except Exception as exc:  # pragma: no cover - dependencias opcionales
            logger.warning("No se pudo inicializar Anthropic: %s", exc)
            return None

    def _generate_with_cohere(self, prompt: str) -> Optional[str]:
        if self._cohere is None:
            return None
        try:
            response = self._cohere.generate(
                prompt=(
                    "Generate a concise, publication-style title (max 12 words) "
                    "for the following text:\n\n"
                    f"{prompt}\n\nTitle:"
                ),
                temperature=0.3,
                max_tokens=40,
            )
            generations = getattr(response, "generations", None)
            if generations:
                text = generations[0].text if generations[0].text else ""
                if text:
                    return _sanitize_title(text)
        except Exception as exc:  # pragma: no cover - API externa
            logger.warning("Error generando título con Cohere: %s", exc)
        return None

    def _generate_with_anthropic(self, prompt: str) -> Optional[str]:
        if self._anthropic is None:
            return None
        try:
            response = self._anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=50,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "You are an expert scientific editor. Generate a short title (max 12 words) "
                            "for the following summary:\n\n" + prompt
                        ),
                    }
                ],
            )
            if response and response.content:
                text = "".join(block.text for block in response.content if hasattr(block, "text"))
                if text:
                    return _sanitize_title(text)
        except Exception as exc:  # pragma: no cover - API externa
            logger.warning("Error generando título con Anthropic: %s", exc)
        return None

    @staticmethod
    def _generate_with_fallback(prompt: str) -> str:
        first_sentence = re.split(r"(?<=[.!?])\s+", prompt.strip())[0]
        words = first_sentence.split()
        top_words = words[:12]
        title = " ".join(top_words)
        title = title.capitalize()
        return title


def _make_preview(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
