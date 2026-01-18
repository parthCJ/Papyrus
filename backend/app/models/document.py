from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    page_number: Optional[int] = None
    section_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    document_id: str
    title: str
    content: str
    filename: str
    source: str
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    publication_date: Optional[str] = None
    num_pages: Optional[int] = None
    file_size: int = 0
    upload_date: datetime = field(default_factory=datetime.utcnow)
    chunks: List[DocumentChunk] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content,
            "filename": self.filename,
            "source": self.source,
            "authors": self.authors,
            "abstract": self.abstract,
            "publication_date": self.publication_date,
            "num_pages": self.num_pages,
            "file_size": self.file_size,
            "upload_date": (
                self.upload_date.isoformat()
                if isinstance(self.upload_date, datetime)
                else self.upload_date
            ),
            "num_chunks": len(self.chunks),
            "metadata": self.metadata,
        }
