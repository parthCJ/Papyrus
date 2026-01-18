from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    ARXIV = "arxiv"
    TEXT = "text"


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_created: int
    message: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    include_sources: Optional[bool] = True
    prompt_template: Optional[str] = Field(
        default="default",
        description="Prompt template: default, academic, detailed, comparative, summary",
    )


class Source(BaseModel):
    document_id: str
    title: str
    chunk_id: str
    content: str
    page_number: Optional[int]
    section_type: Optional[str]
    score: float


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]
    retrieval_time: float
    generation_time: float
    total_time: float


class DocumentMetadata(BaseModel):
    document_id: str
    title: str
    authors: Optional[List[str]]
    abstract: Optional[str]
    publication_date: Optional[str]
    source: DocumentType
    filename: str
    num_pages: Optional[int]
    num_chunks: int
    upload_date: datetime
    file_size: int


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentMetadata]


class DocumentDetail(DocumentMetadata):
    content_preview: Optional[str]
    tags: Optional[List[str]]


class ArxivUploadRequest(BaseModel):
    arxiv_id: str = Field(..., pattern=r"^\d{4}\.\d{4,5}(v\d+)?$")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
