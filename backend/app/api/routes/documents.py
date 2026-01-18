from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.models.schemas import DocumentListResponse, DocumentDetail, DocumentMetadata
from app.api.dependencies import get_elasticsearch_client
from app.core.elasticsearch_client import ElasticsearchClient
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    es_client: ElasticsearchClient = Depends(get_elasticsearch_client),
):
    try:
        documents = await es_client.list_documents(limit=limit, offset=offset)

        return DocumentListResponse(total=len(documents), documents=documents)

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error listing documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str, es_client: ElasticsearchClient = Depends(get_elasticsearch_client)
):
    try:
        document = await es_client.get_document(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str, es_client: ElasticsearchClient = Depends(get_elasticsearch_client)
):
    try:
        success = await es_client.delete_document(document_id)

        if not success:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info(f"Document deleted: {document_id}")

        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error deleting document: {str(e)}"
        )
