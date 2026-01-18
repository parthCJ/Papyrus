from functools import lru_cache
from fastapi import Depends
from app.config import settings
from app.core.elasticsearch_client import ElasticsearchClient
from app.core.embedding_service import EmbeddingService
from app.core.llm_service import LLMService
from app.core.groq_service import GroqService
from app.core.retriever import HybridRetriever


@lru_cache()
def get_elasticsearch_client() -> ElasticsearchClient:
    return ElasticsearchClient()


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@lru_cache()
def get_llm_service():
    """Returns the appropriate LLM service based on LLM_PROVIDER setting"""
    if settings.LLM_PROVIDER == "groq":
        return GroqService()
    else:
        return LLMService()


def get_hybrid_retriever(
    es_client: ElasticsearchClient = Depends(get_elasticsearch_client),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> HybridRetriever:
    return HybridRetriever(es_client=es_client, embedding_service=embedding_service)
