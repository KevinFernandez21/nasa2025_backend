"""Servicio para generar insights de papers usando OpenAI."""

from __future__ import annotations

import logging
from typing import Optional

from openai import OpenAI

from app.models import DocumentHit

logger = logging.getLogger(__name__)


class InsightsService:
    """Genera insights de múltiples papers usando OpenAI."""

    def __init__(self, *, openai_api_key: str | None = None) -> None:
        self._client = self._build_openai_client(openai_api_key)

    @staticmethod
    def _build_openai_client(api_key: Optional[str]):
        if not api_key:
            return None
        try:
            return OpenAI(api_key=api_key)
        except Exception as exc:
            logger.warning("No se pudo inicializar OpenAI: %s", exc)
            return None

    def generate_insight(
        self,
        *,
        query: str,
        papers: list[DocumentHit],
        max_papers: int = 5,
    ) -> str:
        """
        Genera un insight consolidado basado en los papers con mayor coincidencia.

        Args:
            query: La búsqueda original del usuario
            papers: Lista de papers ordenados por relevancia
            max_papers: Número máximo de papers a considerar

        Returns:
            Un insight consolidado como string
        """
        if not self._client:
            return self._generate_fallback_insight(query, papers, max_papers)

        # Seleccionar los papers más relevantes
        top_papers = papers[:max_papers]

        if not top_papers:
            return "No se encontraron papers relevantes para generar un insight."

        # Construir el prompt con información de los papers
        papers_context = self._build_papers_context(top_papers)

        prompt = f"""Eres un experto científico analizando literatura académica.

Búsqueda del usuario: "{query}"

A continuación se presentan los {len(top_papers)} papers más relevantes encontrados:

{papers_context}

Tu tarea es generar un insight consolidado que:
1. Identifique los temas y hallazgos principales comunes entre estos papers
2. Destaque las tendencias o patrones emergentes
3. Señale las áreas de convergencia o divergencia en la investigación
4. Sea conciso pero informativo (máximo 250 palabras)
5. Use un tono académico pero accesible

Genera el insight:"""

        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto científico que sintetiza información de múltiples papers académicos.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=500,
            )

            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                logger.warning("OpenAI no devolvió contenido válido")
                return self._generate_fallback_insight(query, top_papers, max_papers)

        except Exception as exc:
            logger.exception("Error generando insight con OpenAI: %s", exc)
            return self._generate_fallback_insight(query, top_papers, max_papers)

    @staticmethod
    def _build_papers_context(papers: list[DocumentHit]) -> str:
        """Construye el contexto de papers para el prompt."""
        context_parts = []

        for idx, paper in enumerate(papers, 1):
            certainty_str = f"{paper.certainty:.2%}" if paper.certainty else "N/A"

            # Usar abstract si está disponible, sino content_preview
            content = paper.full_abstract if paper.full_abstract else paper.content_preview

            paper_text = f"""Paper {idx}:
Título: {paper.title}
Relevancia: {certainty_str}
Resumen: {content[:500]}...
"""
            context_parts.append(paper_text)

        return "\n".join(context_parts)

    @staticmethod
    def _generate_fallback_insight(
        query: str,
        papers: list[DocumentHit],
        max_papers: int,
    ) -> str:
        """Genera un insight básico sin usar OpenAI."""
        top_papers = papers[:max_papers]

        if not top_papers:
            return "No se encontraron papers relevantes para la búsqueda."

        # Extraer títulos
        titles = [p.title for p in top_papers if p.title]

        insight = f"Se encontraron {len(top_papers)} papers relevantes para '{query}'.\n\n"
        insight += "Principales trabajos:\n"

        for idx, paper in enumerate(top_papers, 1):
            certainty_str = f" (relevancia: {paper.certainty:.2%})" if paper.certainty else ""
            insight += f"{idx}. {paper.title}{certainty_str}\n"

        return insight
