"""
ChromaDB Vector Store wrapper for embedding and searching research findings and sources.
Supports optional session/metadata filtering for multi-tenant and session isolation.
"""
import logging
import os

from app.core.config import settings

logger = logging.getLogger("research_agent.vector_store")


class VectorStore:
    def __init__(self, chroma_path: str | None = None):
        path = chroma_path or settings.CHROMA_PATH
        self.client = None
        self.collection = None
        try:
            import chromadb

            os.makedirs(path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=path)
            self.collection = self.client.get_or_create_collection(
                name="research_findings",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB persistent client initialized at %s", path)
        except Exception as exc:
            logger.warning("ChromaDB initialization failed: %s (vector search will degrade gracefully)", exc)
            self.client = None
            self.collection = None

    def add_finding(self, finding_id: str, text: str, metadata: dict | None = None) -> bool:
        """Add finding text and metadata to vector collection."""
        if not self.collection or not text or not text.strip():
            return False
        try:
            meta = metadata or {}
            # ChromaDB metadata values must be str, int, float, or bool
            clean_meta = {k: str(v) for k, v in meta.items() if v is not None}
            self.collection.upsert(
                ids=[finding_id],
                documents=[text.strip()],
                metadatas=[clean_meta],
            )
            return True
        except Exception as exc:
            logger.warning("Failed to add finding %s to vector store: %s", finding_id, exc)
            return False

    def search_findings(
        self,
        query: str,
        n_results: int = 10,
        session_id: str | None = None,
    ) -> list[dict]:
        """
        Semantic search across stored findings.
        If session_id is provided, filters results to that session (tenant/session isolation).
        """
        if not self.collection or not query or not query.strip():
            return []

        try:
            where_clause = {"session_id": session_id} if session_id else None
            kwargs = {
                "query_texts": [query.strip()],
                "n_results": min(n_results, 50),
            }
            if where_clause:
                kwargs["where"] = where_clause

            res = self.collection.query(**kwargs)
            if not res or not res.get("ids") or not res["ids"][0]:
                return []

            results = []
            for i in range(len(res["ids"][0])):
                results.append({
                    "id": res["ids"][0][i],
                    "text": res["documents"][0][i] if res.get("documents") else "",
                    "metadata": res["metadatas"][0][i] if res.get("metadatas") else {},
                    "distance": res["distances"][0][i] if res.get("distances") else 0.0,
                })
            return results
        except Exception as exc:
            logger.warning("Vector search failed for query '%s': %s", query, exc)
            return []
