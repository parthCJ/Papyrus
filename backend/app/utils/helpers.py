import hashlib
import uuid
from typing import List, Any
from datetime import datetime


def generate_document_id(filename: str) -> str:
    timestamp = datetime.utcnow().isoformat()
    unique_string = f"{filename}_{timestamp}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def generate_chunk_id(document_id: str, chunk_index: int) -> str:
    return f"{document_id}_chunk_{chunk_index}"


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def reciprocal_rank_fusion(
    bm25_results: List[tuple],
    vector_results: List[tuple],
    k: int = 60,
    bm25_weight: float = 0.4,
    vector_weight: float = 0.6,
) -> List[tuple]:
    scores = {}

    for rank, (doc_id, score) in enumerate(bm25_results, 1):
        if doc_id not in scores:
            scores[doc_id] = {"bm25": 0, "vector": 0, "doc": None}
        scores[doc_id]["bm25"] = bm25_weight / (k + rank)
        scores[doc_id]["doc"] = score

    for rank, (doc_id, score) in enumerate(vector_results, 1):
        if doc_id not in scores:
            scores[doc_id] = {"bm25": 0, "vector": 0, "doc": None}
        scores[doc_id]["vector"] = vector_weight / (k + rank)
        if scores[doc_id]["doc"] is None:
            scores[doc_id]["doc"] = score

    final_scores = [
        (doc_id, data["bm25"] + data["vector"], data["doc"])
        for doc_id, data in scores.items()
    ]

    final_scores.sort(key=lambda x: x[1], reverse=True)

    return final_scores
