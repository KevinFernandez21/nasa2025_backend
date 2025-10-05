"""Configuración centralizada del servicio."""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno para conectarse a proveedores externos."""

    weaviate_url: str = Field(..., alias="WEAVIATE_URL")
    weaviate_api_key: str = Field(..., alias="WEAVIATE_API_KEY")
    cohere_api_key: str | None = Field(default=None, alias="COHERE_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    collection_name: str = Field(default="ScientificPapersFullContent", alias="COLLECTION_NAME")
    use_cloud: bool = Field(default=True, alias="USE_CLOUD")
    request_timeout_seconds: int = Field(default=30, alias="REQUEST_TIMEOUT_SECONDS")

    # Neo4j Configuration
    neo4j_uri: str = Field(..., alias="NEO4J_URI")
    neo4j_username: str = Field(..., alias="NEO4J_USERNAME")
    neo4j_password: str = Field(..., alias="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", alias="NEO4J_DATABASE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Devuelve las settings cacheadas para evitar releer variables."""

    return Settings()
