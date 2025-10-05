"""Funciones para extraer contenido de artículos en PubMed Central."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PaperContent:
    title: str
    abstract: str
    content: str
    full_text: str
    success: bool
    error: str | None = None


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
MIN_PARAGRAPH_LENGTH = 50
MAX_ABSTRACT_CHARS = 2_000
MAX_CONTENT_CHARS = 8_000
MAX_FULL_TEXT_CHARS = 10_000


def extract_pubmed_content(url: str, timeout_seconds: int = 30) -> PaperContent:
    """Descarga y limpia el contenido principal de un artículo de PubMed Central."""

    logger.info("Descargando artículo: %s", url)
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - requests ya probado externamente
        logger.exception("Error recuperando artículo de PubMed")
        return PaperContent("", "", "", "", False, str(exc))

    soup = BeautifulSoup(response.content, "html.parser")

    title = _extract_title(soup)
    abstract = _extract_abstract(soup)
    content = _extract_body_content(soup)

    full_text_parts = [title, ""]
    if abstract:
        full_text_parts.append("ABSTRACT:\n" + abstract)
        full_text_parts.append("")
    if content:
        full_text_parts.append("CONTENT:\n" + content)

    full_text = "\n".join(full_text_parts).strip()
    if len(full_text) > MAX_FULL_TEXT_CHARS:
        full_text = full_text[:MAX_FULL_TEXT_CHARS] + "..."

    success = bool(title and abstract)

    result = PaperContent(
        title=title,
        abstract=abstract[:MAX_ABSTRACT_CHARS],
        content=content[:MAX_CONTENT_CHARS],
        full_text=full_text,
        success=success,
    )

    logger.debug("Artículo procesado | título='%s' | éxito=%s", result.title[:80], success)
    return result


def process_papers_with_content(
    dataframe: pd.DataFrame,
    *,
    max_papers: int | None = None,
    delay_seconds: float = 2.0,
    timeout_seconds: int = 30,
) -> pd.DataFrame:
    """Procesa un conjunto de artículos descargando su contenido completo."""

    working_df = dataframe.copy()
    if max_papers is not None:
        working_df = working_df.head(max_papers)

    logger.info("Procesando %s papers", len(working_df))
    registros: list[Dict[str, object]] = []

    for idx, row in working_df.iterrows():
        link = row.get("Link")
        title = row.get("Title", "")
        logger.info("Procesando paper %s/%s", len(registros) + 1, len(working_df))

        content = extract_pubmed_content(link, timeout_seconds=timeout_seconds)
        registros.append(
            {
                "original_title": title,
                "link": link,
                "extracted_title": content.title,
                "abstract": content.abstract,
                "content": content.content,
                "full_text": content.full_text,
                "success": content.success,
                "paperIndex": int(idx),
                "error": content.error,
            }
        )

        time.sleep(delay_seconds)

    enriched_df = pd.DataFrame(registros)
    logger.info(
        "Proceso finalizado | éxitos=%s | errores=%s",
        int(enriched_df["success"].sum()),
        int((~enriched_df["success"]).sum()),
    )
    return enriched_df


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------

def _extract_title(soup: BeautifulSoup) -> str:
    meta_title = soup.find("meta", {"name": "citation_title"})
    if meta_title and meta_title.get("content"):
        return meta_title["content"].strip()

    heading = soup.find("h1", class_="content-title")
    if heading:
        return heading.get_text(strip=True)

    return ""


def _extract_abstract(soup: BeautifulSoup) -> str:
    abstract_sections = [
        soup.find("div", {"id": lambda x: x and "abstract" in x.lower()}),
        soup.find("meta", {"name": "citation_abstract"}),
        soup.find("section", class_="abstract"),
    ]

    abstract_texts: list[str] = []
    for section in abstract_sections:
        if section is None:
            continue

        if isinstance(section, Tag):
            paragraphs = section.find_all("p")
            for paragraph in paragraphs:
                text = paragraph.get_text(strip=True)
                if _is_valid_paragraph(text):
                    abstract_texts.append(text)
        elif section and section.get("content"):
            return section["content"].strip()

    return " ".join(abstract_texts)


def _extract_body_content(soup: BeautifulSoup) -> str:
    article = soup.find("article") or soup.find("div", class_="article")
    if not article:
        return ""

    texts: list[str] = []
    for paragraph in article.find_all("p"):
        text = paragraph.get_text(strip=True)
        if _is_valid_paragraph(text):
            texts.append(text)

    if not texts:
        return ""

    return " ".join(texts[:100])


def _is_valid_paragraph(text: str | None) -> bool:
    if not text:
        return False

    lowered = text.lower()
    if len(text) < MIN_PARAGRAPH_LENGTH:
        return False

    blacklisted_terms = ("government", "website", ".gov")
    return not any(term in lowered for term in blacklisted_terms)
