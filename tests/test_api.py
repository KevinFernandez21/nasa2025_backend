from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.models import DocumentHit
from app.dependencies import get_document_service


class FakeDocumentService:
    def search_documents(self, *, query: str, limit: int, only_full_content: bool):
        return [
            DocumentHit(
                title=f"{query.title()} Result",
                abstract="Resumen breve",
                content_preview="Contenido recortado",
                link="https://example.org/paper",
                certainty=0.75,
                full_abstract="Resumen completo",
                full_content="Contenido completo",
            )
            for _ in range(limit)
        ]

    def generate_title(self, text: str) -> tuple[str, str]:
        return text.title(), "heuristic"


def override_document_service():
    return FakeDocumentService()


app.dependency_overrides[get_document_service] = override_document_service

client = TestClient(app)


def test_search_documents_returns_hits():
    response = client.post(
        "/search",
        json={"query": "quantum", "limit": 2, "only_full_content": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert len(payload["items"]) == 2
    assert payload["items"][0]["title"].startswith("Quantum")


def test_generate_title_returns_title():
    response = client.post("/title", json={"text": "an innovative approach to ai"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "An Innovative Approach To Ai"
    assert payload["source"] == "heuristic"
