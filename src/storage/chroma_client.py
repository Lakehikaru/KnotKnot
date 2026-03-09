"""Chroma vector database client wrapper."""

from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChromaClient:
    """Wrapper for Chroma vector database."""

    def __init__(self):
        """Initialize Chroma client."""
        self.client = chromadb.PersistentClient(
            path=settings.chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(
            "chroma_initialized",
            path=settings.chroma_path,
            collection=settings.chroma_collection_name
        )

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the collection.

        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
        """
        if ids is None:
            import uuid
            ids = [str(uuid.uuid4()) for _ in documents]

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(
            "documents_added",
            count=len(documents)
        )

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query the collection.

        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Query results
        """
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where
        )

        logger.info(
            "query_executed",
            n_results=n_results,
            returned=len(results["ids"][0]) if results["ids"] else 0
        )

        return results

    def delete_collection(self):
        """Delete the collection."""
        self.client.delete_collection(settings.chroma_collection_name)
        logger.info("collection_deleted")

    def get_stats(self) -> Dict:
        """Get collection statistics."""
        count = self.collection.count()
        return {
            "collection_name": settings.chroma_collection_name,
            "document_count": count
        }
