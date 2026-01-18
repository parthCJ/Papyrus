import pytest
from app.utils.helpers import (
    reciprocal_rank_fusion,
    generate_document_id,
    generate_chunk_id,
)


def test_generate_document_id():
    doc_id = generate_document_id("test.pdf")
    assert isinstance(doc_id, str)
    assert len(doc_id) == 32


def test_generate_chunk_id():
    chunk_id = generate_chunk_id("doc123", 0)
    assert chunk_id == "doc123_chunk_0"


def test_reciprocal_rank_fusion():
    bm25_results = [("doc1", {"content": "test1"}), ("doc2", {"content": "test2"})]
    vector_results = [("doc2", {"content": "test2"}), ("doc3", {"content": "test3"})]

    fused = reciprocal_rank_fusion(
        bm25_results=bm25_results,
        vector_results=vector_results,
        k=60,
        bm25_weight=0.4,
        vector_weight=0.6,
    )

    assert len(fused) == 3
    assert all(len(item) == 3 for item in fused)


def test_reciprocal_rank_fusion_empty():
    fused = reciprocal_rank_fusion(
        bm25_results=[], vector_results=[], k=60, bm25_weight=0.4, vector_weight=0.6
    )

    assert len(fused) == 0
