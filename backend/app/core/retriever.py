from typing import List, Dict, Any
from app.core.elasticsearch_client import ElasticsearchClient
from app.core.embedding_service import EmbeddingService
from app.utils.helpers import reciprocal_rank_fusion
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class HybridRetriever:
    def __init__(
        self, es_client: ElasticsearchClient, embedding_service: EmbeddingService
    ):
        self.es_client = es_client
        self.embedding_service = embedding_service

    async def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.es_client._initialized:
            await self.es_client.initialize()

        if not self.embedding_service._initialized:
            self.embedding_service.initialize()

        bm25_results = await self.es_client.bm25_search(query, top_k=top_k * 2)

        query_embedding = self.embedding_service.embed_text(query)
        vector_results = await self.es_client.vector_search(
            query_embedding, top_k=top_k * 2
        )

        bm25_tuples = [(result["chunk_id"], result) for result in bm25_results]
        vector_tuples = [(result["chunk_id"], result) for result in vector_results]

        fused_results = reciprocal_rank_fusion(
            bm25_results=bm25_tuples,
            vector_results=vector_tuples,
            k=60,
            bm25_weight=settings.BM25_WEIGHT,
            vector_weight=settings.VECTOR_WEIGHT,
        )

        final_results = []
        for chunk_id, fused_score, chunk_data in fused_results[:top_k]:
            if chunk_data:
                chunk_data["score"] = fused_score
                final_results.append(chunk_data)

        logger.info(f"Hybrid search returned {len(final_results)} results")

        return final_results
