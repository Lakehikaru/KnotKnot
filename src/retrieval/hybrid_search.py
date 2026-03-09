"""Hybrid search using BGE-M3 embeddings and Chroma."""

from typing import List, Dict, Optional
from FlagEmbedding import BGEM3FlagModel

from src.storage.chroma_client import ChromaClient
from src.utils.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HybridSearcher:
    """Hybrid search with dense and sparse retrieval."""

    def __init__(self):
        """Initialize hybrid searcher."""
        logger.info("initializing_bge_m3_model")

        # Initialize BGE-M3 model (supports dense + sparse)
        self.model = BGEM3FlagModel(
            'BAAI/bge-m3',
            use_fp16=False  # CPU mode
        )

        # Initialize Chroma client
        self.chroma = ChromaClient()

        logger.info("hybrid_searcher_initialized")

    def encode(self, texts: List[str]) -> Dict:
        """
        Encode texts to embeddings.

        Args:
            texts: List of texts to encode

        Returns:
            Dict with dense and sparse embeddings
        """
        embeddings = self.model.encode(
            texts,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False
        )

        return embeddings

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the index.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for each document
        """
        logger.info("encoding_documents", count=len(documents))

        # Encode documents
        embeddings = self.encode(documents)

        # Add to Chroma (dense vectors only for now)
        self.chroma.add_documents(
            documents=documents,
            embeddings=embeddings['dense_vecs'].tolist(),
            metadatas=metadatas,
            ids=ids
        )

        logger.info("documents_indexed", count=len(documents))

    def search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Hybrid search for query.

        Args:
            query: Query text
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of search results with scores
        """
        if top_k is None:
            top_k = settings.top_k

        logger.info("executing_search", query=query[:50], top_k=top_k)

        # Encode query
        query_embeddings = self.encode([query])

        # Dense search using Chroma
        results = self.chroma.query(
            query_embeddings=query_embeddings['dense_vecs'].tolist(),
            n_results=top_k,
            where=filters
        )

        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0.0
                })

        logger.info("search_completed", results_count=len(formatted_results))

        return formatted_results

    def get_stats(self) -> Dict:
        """Get searcher statistics."""
        return self.chroma.get_stats()
