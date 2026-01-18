from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional
import os
import shutil
from app.models.schemas import UploadResponse, ArxivUploadRequest, ErrorResponse
from app.api.dependencies import get_elasticsearch_client, get_embedding_service
from app.core.elasticsearch_client import ElasticsearchClient
from app.core.embedding_service import EmbeddingService
from app.core.document_processor import DocumentProcessor
from app.config import settings
from app.utils.logger import setup_logger
from app.utils.helpers import generate_document_id

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/pdf", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    es_client: ElasticsearchClient = Depends(get_elasticsearch_client),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
        )

    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"PDF uploaded: {file.filename}")

        processor = DocumentProcessor(embedding_service)
        document = await processor.process_pdf(file_path, file.filename)

        await es_client.index_document(document)

        logger.info(
            f"Document indexed: {document.document_id} with {len(document.chunks)} chunks"
        )

        return UploadResponse(
            document_id=document.document_id,
            filename=file.filename,
            status="success",
            chunks_created=len(document.chunks),
            message="PDF uploaded and indexed successfully",
        )

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.post("/arxiv", response_model=UploadResponse)
async def upload_arxiv(
    request: ArxivUploadRequest,
    es_client: ElasticsearchClient = Depends(get_elasticsearch_client),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
):
    try:
        processor = DocumentProcessor(embedding_service)
        document = await processor.process_arxiv(request.arxiv_id)

        await es_client.index_document(document)

        logger.info(f"ArXiv paper indexed: {document.document_id} ({request.arxiv_id})")

        return UploadResponse(
            document_id=document.document_id,
            filename=f"{request.arxiv_id}.pdf",
            status="success",
            chunks_created=len(document.chunks),
            message="ArXiv paper downloaded and indexed successfully",
        )

    except Exception as e:
        logger.error(f"Error processing ArXiv paper: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error processing ArXiv paper: {str(e)}"
        )
