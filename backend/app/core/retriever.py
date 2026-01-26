from typing import List, Dict, Any
from app.core.elasticsearch_client import ElasticsearchClient
from app.core.embedding_service import EmbeddingService
from app.utils.helpers import reciprocal_rank_fusion
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class HybridRetriever:
    def __init__(
        self,
        es_client: ElasticsearchClient,
        embedding_service: EmbeddingService,
    ):
        self.es_client = es_client
        self.embedding_service = embedding_service

    # -----------------------------
    # Query intent classification
    # -----------------------------
    def _classify_query(self, query: str) -> str:
        q = query.lower()

        if any(k in q for k in ["what is", "define"]):
            return "definition"

        if any(k in q for k in ["parameter", "parameters", "weights", "matrix"]):
            return "parameters"

        if any(k in q for k in ["evidence", "signatures", "identify", "observational"]):
            return "observation"

        if any(k in q for k in ["compare", "differentiate", "contrast"]):
            return "comparison"

        if any(k in q for k in ["why", "argue", "explain"]):
            return "explanation"

        if any(k in q for k in ["conclude", "overall", "dynamical state"]):
            return "conclusion"

        return "general"

    # -----------------------------
    # Section-based score boosting
    # -----------------------------
    def _section_boost(self, section: str) -> float:
        return {
            "ABSTRACT": 1.4,
            "TABLE": 1.5,
            "FIGURE": 1.3,
            "RESULTS": 1.2,
            "CONCLUSION": 1.2,
            "METHODS": 1.0,
            "DISCUSSION": 0.9,
            "INTRODUCTION": 0.8,
        }.get(section, 1.0)

    # -----------------------------
    # Main retrieval function
    # -----------------------------
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 6,
    ) -> List[Dict[str, Any]]:

        # Ensure services are initialized
        if not self.es_client._initialized:
            await self.es_client.initialize()

        if not self.embedding_service._initialized:
            self.embedding_service.initialize()

        intent = self._classify_query(query)

        # Intent-aware weighting
        if intent in {"parameters", "observation", "comparison"}:
            bm25_weight = 0.65
            vector_weight = 0.35
        else:
            bm25_weight = settings.BM25_WEIGHT
            vector_weight = settings.VECTOR_WEIGHT

        # Slight over-fetch for fusion
        search_k = int(top_k * 1.5)

        # BM25 retrieval
        bm25_results = await self.es_client.bm25_search(
            query,
            top_k=search_k,
        )

        # Vector retrieval
        query_embedding = self.embedding_service.embed_text(query)
        vector_results = await self.es_client.vector_search(
            query_embedding,
            top_k=search_k,
        )

        # Prepare RRF inputs
        bm25_tuples = [(r["chunk_id"], r) for r in bm25_results]
        vector_tuples = [(r["chunk_id"], r) for r in vector_results]

        fused = reciprocal_rank_fusion(
            bm25_results=bm25_tuples,
            vector_results=vector_tuples,
            k=60,
            bm25_weight=bm25_weight,
            vector_weight=vector_weight,
        )

        final_results: List[Dict[str, Any]] = []
        seen_ids = set()

        # Apply section-aware boosting
        for chunk_id, fused_score, chunk_data in fused:
            if not chunk_data or chunk_id in seen_ids:
                continue

            section = chunk_data.get("section", "DISCUSSION")
            boosted_score = fused_score * self._section_boost(section)

            chunk_data["score"] = boosted_score
            final_results.append(chunk_data)
            seen_ids.add(chunk_id)

            if len(final_results) >= top_k:
                break

        # -----------------------------
        # Hard guarantee: include TABLES
        # -----------------------------
        table_chunks = [
            r
            for r in bm25_results
            if r.get("section") == "TABLE" and r["chunk_id"] not in seen_ids
        ]

        for t in table_chunks:
            t["score"] = t.get("score", 0.0) + 10.0
            final_results.append(t)
            seen_ids.add(t["chunk_id"])

        # Final sort by score
        final_results = sorted(
            final_results,
            key=lambda x: x["score"],
            reverse=True,
        )[:top_k]

        logger.info(
            f"Hybrid search returned {len(final_results)} results "
            f"(intent={intent}, bm25={bm25_weight}, vector={vector_weight})"
        )

        return final_results
