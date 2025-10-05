"""Servicio para generar insights de papers usando OpenAI."""

from __future__ import annotations

import logging
from typing import Optional

from openai import OpenAI

from app.models import DocumentHit, Reference

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
    ) -> tuple[str, list[Reference]]:
        """
        Genera un insight consolidado basado en los papers con mayor coincidencia.

        Args:
            query: La búsqueda original del usuario
            papers: Lista de papers ordenados por relevancia
            max_papers: Número máximo de papers a considerar

        Returns:
            Tupla con (insight_text, lista_de_referencias)
        """
        if not self._client:
            return self._generate_fallback_insight(query, papers, max_papers)

        # Seleccionar los papers más relevantes
        top_papers = papers[:max_papers]

        if not top_papers:
            return "No se encontraron papers relevantes para generar un insight.", []

        # Crear lista de referencias
        references = self._build_references(top_papers)

        # Construir el prompt con información de los papers
        papers_context = self._build_papers_context_with_numbers(top_papers)

        prompt = f"""You are a scientific expert analyzing academic literature.

User search query: "{query}"

Below are the {len(top_papers)} most relevant papers found:

{papers_context}

Your task is to generate a consolidated insight that:
1. Identifies the main themes and findings common among these papers
2. Highlights emerging trends or patterns
3. Points out areas of convergence or divergence in the research
4. Is concise but informative (maximum 250 words)
5. Uses an academic but accessible tone
6. **IMPORTANT**: Use numbered references [1], [2], [3], etc. when mentioning specific information from a paper

Example: "Recent studies show that... [1]. Additionally, it has been observed... [2][3]."

Generate the insight with references:"""

        try:
            response = self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a scientific expert who synthesizes information from multiple academic papers using numbered references.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=600,
            )

            if response.choices and response.choices[0].message.content:
                insight_text = response.choices[0].message.content.strip()
                return insight_text, references
            else:
                logger.warning("OpenAI no devolvió contenido válido")
                return self._generate_fallback_insight(query, top_papers, max_papers)

        except Exception as exc:
            logger.exception("Error generando insight con OpenAI: %s", exc)
            return self._generate_fallback_insight(query, top_papers, max_papers)

    @staticmethod
    def _build_references(papers: list[DocumentHit]) -> list[Reference]:
        """Construye la lista de referencias numeradas."""
        references = []
        for idx, paper in enumerate(papers, 1):
            references.append(
                Reference(
                    id=idx,
                    title=paper.title,
                    link=paper.link,
                    certainty=paper.certainty,
                )
            )
        return references

    @staticmethod
    def _build_papers_context_with_numbers(papers: list[DocumentHit]) -> str:
        """Construye el contexto de papers con numeración para el prompt."""
        context_parts = []

        for idx, paper in enumerate(papers, 1):
            certainty_str = f"{paper.certainty:.2%}" if paper.certainty else "N/A"

            # Usar abstract si está disponible, sino content_preview
            content = paper.full_abstract if paper.full_abstract else paper.content_preview

            paper_text = f"""[{idx}] {paper.title}
Relevancia: {certainty_str}
Resumen: {content[:500]}...
"""
            context_parts.append(paper_text)

        return "\n".join(context_parts)

    @staticmethod
    def _build_papers_context(papers: list[DocumentHit]) -> str:
        """Construye el contexto de papers para el prompt (legacy)."""
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
    ) -> tuple[str, list[Reference]]:
        """Genera un insight básico sin usar OpenAI."""
        top_papers = papers[:max_papers]

        if not top_papers:
            return "No se encontraron papers relevantes para la búsqueda.", []

        # Crear referencias
        references = []
        for idx, paper in enumerate(top_papers, 1):
            references.append(
                Reference(
                    id=idx,
                    title=paper.title,
                    link=paper.link,
                    certainty=paper.certainty,
                )
            )

        # Generar insight con referencias
        insight = f"Se encontraron {len(top_papers)} papers relevantes para '{query}'.\n\n"
        insight += "Principales trabajos:\n"

        for idx, paper in enumerate(top_papers, 1):
            certainty_str = f" (relevancia: {paper.certainty:.2%})" if paper.certainty else ""
            insight += f"[{idx}] {paper.title}{certainty_str}\n"

        return insight, references
