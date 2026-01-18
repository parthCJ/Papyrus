import fitz
import arxiv
import os
from typing import List, Optional
from app.models.document import Document, DocumentChunk
from app.core.embedding_service import EmbeddingService
from app.utils.helpers import generate_document_id, generate_chunk_id
from app.config import settings
from app.utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


class DocumentProcessor:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP

    async def process_pdf(self, file_path: str, filename: str) -> Document:
        logger.info(f"Processing PDF: {filename}")

        text, metadata = self._extract_pdf_text(file_path)

        document_id = generate_document_id(filename)

        chunks = self._create_chunks(text, document_id)

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        document = Document(
            document_id=document_id,
            title=metadata.get("title", filename.replace(".pdf", "")),
            content=text,
            filename=filename,
            source="pdf",
            authors=metadata.get("authors"),
            abstract=metadata.get("abstract"),
            num_pages=metadata.get("num_pages"),
            file_size=os.path.getsize(file_path),
            upload_date=datetime.utcnow(),
            chunks=chunks,
            metadata=metadata,
        )

        logger.info(f"Processed PDF: {filename} - {len(chunks)} chunks created")

        return document

    async def process_arxiv(self, arxiv_id: str) -> Document:
        logger.info(f"Processing ArXiv paper: {arxiv_id}")

        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        pdf_path = os.path.join(settings.UPLOAD_DIR, f"{arxiv_id}.pdf")
        paper.download_pdf(filename=pdf_path)

        text, pdf_metadata = self._extract_pdf_text(pdf_path)

        document_id = generate_document_id(f"{arxiv_id}.pdf")

        chunks = self._create_chunks(text, document_id)

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        authors = [author.name for author in paper.authors]

        document = Document(
            document_id=document_id,
            title=paper.title,
            content=text,
            filename=f"{arxiv_id}.pdf",
            source="arxiv",
            authors=authors,
            abstract=paper.summary,
            publication_date=(
                paper.published.strftime("%Y-%m-%d") if paper.published else None
            ),
            num_pages=pdf_metadata.get("num_pages"),
            file_size=os.path.getsize(pdf_path),
            upload_date=datetime.utcnow(),
            chunks=chunks,
            metadata={
                "arxiv_id": arxiv_id,
                "arxiv_url": paper.entry_id,
                "categories": paper.categories,
            },
        )

        logger.info(f"Processed ArXiv paper: {arxiv_id} - {len(chunks)} chunks created")

        return document

    def _extract_pdf_text(self, file_path: str) -> tuple[str, dict]:
        doc = fitz.open(file_path)

        text_parts = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            text_parts.append(text)

        full_text = "\n".join(text_parts)

        metadata = {
            "num_pages": len(doc),
            "title": doc.metadata.get("title", ""),
            "authors": (
                [doc.metadata.get("author", "")] if doc.metadata.get("author") else None
            ),
            "creation_date": doc.metadata.get("creationDate", ""),
        }

        doc.close()

        return full_text, metadata

    def _create_chunks(self, text: str, document_id: str) -> List[DocumentChunk]:
        words = text.split()
        chunks = []
        chunk_index = 0

        i = 0
        while i < len(words):
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)

            chunk = DocumentChunk(
                chunk_id=generate_chunk_id(document_id, chunk_index),
                document_id=document_id,
                content=chunk_text,
                metadata={"chunk_index": chunk_index},
            )

            chunks.append(chunk)
            chunk_index += 1

            i += self.chunk_size - self.chunk_overlap

        return chunks
