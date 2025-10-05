"""Servicio para interactuar con Neo4j."""

from __future__ import annotations

import logging
from typing import Any

from neo4j import GraphDatabase, Driver

from app.config import Settings

logger = logging.getLogger(__name__)


class Neo4jService:
    """Servicio para gestionar conexiones y consultas a Neo4j."""

    def __init__(self, settings: Settings):
        """Inicializa la conexión con Neo4j."""
        self.driver: Driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        self.database = settings.neo4j_database

    def close(self):
        """Cierra la conexión con Neo4j."""
        if self.driver:
            self.driver.close()

    def get_graph_data(self, query: str | None = None, limit: int = 100) -> dict[str, Any]:
        """
        Obtiene datos del grafo de Neo4j.

        Args:
            query: Consulta Cypher personalizada (opcional)
            limit: Límite de nodos a retornar

        Returns:
            Diccionario con nodos y relaciones del grafo
        """
        default_query = """
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT $limit
        """

        cypher_query = query if query else default_query

        with self.driver.session(database=self.database) as session:
            result = session.run(cypher_query, limit=limit)

            nodes = []
            relationships = []
            node_ids = set()

            for record in result:
                # Extraer nodos
                for key in record.keys():
                    value = record[key]
                    if hasattr(value, 'id') and hasattr(value, 'labels'):  # Es un nodo
                        if value.id not in node_ids:
                            node_ids.add(value.id)
                            nodes.append({
                                "id": value.id,
                                "labels": list(value.labels),
                                "properties": dict(value.items()),
                            })
                    elif hasattr(value, 'type'):  # Es una relación
                        relationships.append({
                            "id": value.id,
                            "type": value.type,
                            "start_node": value.start_node.id,
                            "end_node": value.end_node.id,
                            "properties": dict(value.items()),
                        })

            return {
                "nodes": nodes,
                "relationships": relationships,
                "count": {
                    "nodes": len(nodes),
                    "relationships": len(relationships),
                }
            }

    def execute_query(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """
        Ejecuta una consulta Cypher personalizada.

        Args:
            query: Consulta Cypher
            parameters: Parámetros para la consulta

        Returns:
            Lista de resultados
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
