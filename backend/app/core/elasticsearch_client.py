from elasticsearch import AsyncElasticsearch
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.document import Document, DocumentChunk
from app.models.schemas import DocumentMetadata, DocumentDetail
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class ElasticsearchClient:
    def __init__(self):
        self.client = None
        self.index_name = settings.ELASTICSEARCH_INDEX
        self.chunk_index_name = f"{self.index_name}_chunks"
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return

        self.client = AsyncElasticsearch(
            hosts=[
                f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
            ],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )

        await self._create_indices()
        self._initialized = True
        logger.info("Elasticsearch client initialized")

    async def _create_indices(self):
        document_mapping = {
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "content": {"type": "text", "analyzer": "english"},
                    "filename": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "authors": {"type": "keyword"},
                    "abstract": {"type": "text", "analyzer": "english"},
                    "publication_date": {
                        "type": "date",
                        "format": "yyyy-MM-dd||yyyy||epoch_millis",
                        "ignore_malformed": True,
                    },
                    "num_pages": {"type": "integer"},
                    "file_size": {"type": "long"},
                    "upload_date": {"type": "date"},
                    "num_chunks": {"type": "integer"},
                    "metadata": {"type": "object", "enabled": False},
                }
            }
        }

        chunk_mapping = {
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "content": {"type": "text", "analyzer": "english"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": settings.EMBEDDING_DIMENSION,
                        "index": True,
                        "similarity": "cosine",
                    },
                    "page_number": {"type": "integer"},
                    "section_type": {"type": "keyword"},
                    "metadata": {"type": "object", "enabled": False},
                }
            }
        }

        if not await self.client.indices.exists(index=self.index_name):
            await self.client.indices.create(
                index=self.index_name, body=document_mapping
            )
            logger.info(f"Created index: {self.index_name}")

        if not await self.client.indices.exists(index=self.chunk_index_name):
            await self.client.indices.create(
                index=self.chunk_index_name, body=chunk_mapping
            )
            logger.info(f"Created index: {self.chunk_index_name}")

    async def index_document(self, document: Document):
        if not self._initialized:
            await self.initialize()

        doc_data = document.to_dict()

        await self.client.index(
            index=self.index_name, id=document.document_id, document=doc_data
        )

        for chunk in document.chunks:
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "title": document.title,
                "content": chunk.content,
                "embedding": chunk.embedding,
                "page_number": chunk.page_number,
                "section_type": chunk.section_type,
                "metadata": chunk.metadata,
            }

            await self.client.index(
                index=self.chunk_index_name, id=chunk.chunk_id, document=chunk_data
            )

        await self.client.indices.refresh(index=self.index_name)
        await self.client.indices.refresh(index=self.chunk_index_name)

        logger.info(
            f"Indexed document {document.document_id} with {len(document.chunks)} chunks"
        )

    async def bm25_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._initialized:
            await self.initialize()

        search_query = {
            "query": {"match": {"content": {"query": query, "operator": "or"}}},
            "size": top_k,
            "_source": [
                "chunk_id",
                "document_id",
                "title",
                "content",
                "page_number",
                "section_type",
            ],
        }

        response = await self.client.search(
            index=self.chunk_index_name, body=search_query
        )

        results = []
        for hit in response["hits"]["hits"]:
            result = hit["_source"]
            result["score"] = hit["_score"]
            results.append(result)

        return results

    async def vector_search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        if not self._initialized:
            await self.initialize()

        search_query = {
            "knn": {
                "field": "embedding",
                "query_vector": query_embedding,
                "k": top_k,
                "num_candidates": top_k * 2,
            },
            "_source": [
                "chunk_id",
                "document_id",
                "title",
                "content",
                "page_number",
                "section_type",
            ],
        }

        response = await self.client.search(
            index=self.chunk_index_name, body=search_query
        )

        results = []
        for hit in response["hits"]["hits"]:
            result = hit["_source"]
            result["score"] = hit["_score"]
            results.append(result)

        return results

    async def list_documents(
        self, limit: int = 10, offset: int = 0
    ) -> List[DocumentMetadata]:
        if not self._initialized:
            await self.initialize()

        search_query = {
            "query": {"match_all": {}},
            "size": limit,
            "from": offset,
            "sort": [{"upload_date": {"order": "desc"}}],
        }

        response = await self.client.search(index=self.index_name, body=search_query)

        documents = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            documents.append(
                DocumentMetadata(
                    document_id=source["document_id"],
                    title=source["title"],
                    authors=source.get("authors"),
                    abstract=source.get("abstract"),
                    publication_date=source.get("publication_date"),
                    source=source["source"],
                    filename=source["filename"],
                    num_pages=source.get("num_pages"),
                    num_chunks=source["num_chunks"],
                    upload_date=source["upload_date"],
                    file_size=source["file_size"],
                )
            )

        return documents

    async def get_document(self, document_id: str) -> Optional[DocumentDetail]:
        if not self._initialized:
            await self.initialize()

        try:
            response = await self.client.get(index=self.index_name, id=document_id)
            source = response["_source"]

            content_preview = source.get("content", "")[:500]

            return DocumentDetail(
                document_id=source["document_id"],
                title=source["title"],
                authors=source.get("authors"),
                abstract=source.get("abstract"),
                publication_date=source.get("publication_date"),
                source=source["source"],
                filename=source["filename"],
                num_pages=source.get("num_pages"),
                num_chunks=source["num_chunks"],
                upload_date=source["upload_date"],
                file_size=source["file_size"],
                content_preview=content_preview,
                tags=None,
            )
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            return None

    async def delete_document(self, document_id: str) -> bool:
        if not self._initialized:
            await self.initialize()

        try:
            # Delete the main document
            doc_response = await self.client.delete(
                index=self.index_name, id=document_id
            )
            logger.info(f"Deleted document {document_id}: {doc_response}")

            # Delete all associated chunks
            delete_chunks_query = {"query": {"term": {"document_id": document_id}}}

            chunk_response = await self.client.delete_by_query(
                index=self.chunk_index_name, body=delete_chunks_query
            )
            logger.info(
                f"Deleted {chunk_response['deleted']} chunks for document {document_id}"
            )

            # Refresh indices
            await self.client.indices.refresh(index=self.index_name)
            await self.client.indices.refresh(index=self.chunk_index_name)

            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch client closed")
