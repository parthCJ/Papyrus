from fastapi import APIRouter, HTTPException, Depends
from time import time
from app.models.schemas import QueryRequest, QueryResponse, Source
from app.api.dependencies import get_hybrid_retriever, get_llm_service
from app.core.retriever import HybridRetriever
from app.core.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.post("/", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    llm_service: LLMService = Depends(get_llm_service),
):
    try:
        start_time = time()

        retrieval_start = time()
        retrieved_chunks = await retriever.hybrid_search(
            query=request.query, top_k=request.top_k
        )
        retrieval_time = time() - retrieval_start

        logger.info(
            f"Retrieved {len(retrieved_chunks)} chunks in {retrieval_time:.2f}s"
        )

        if not retrieved_chunks:
            return QueryResponse(
                query=request.query,
                answer="No relevant documents found for your query.",
                sources=[],
                retrieval_time=retrieval_time,
                generation_time=0,
                total_time=time() - start_time,
            )

        generation_start = time()
        answer = await llm_service.generate_answer(
            query=request.query,
            context_chunks=retrieved_chunks,
            prompt_template=request.prompt_template,
        )
        generation_time = time() - generation_start

        sources = []
        if request.include_sources:
            for chunk_data in retrieved_chunks:
                sources.append(
                    Source(
                        document_id=chunk_data.get("document_id", "unknown"),
                        title=chunk_data.get("title", "Unknown"),
                        chunk_id=chunk_data.get("chunk_id", "unknown"),
                        content=chunk_data.get("content", ""),
                        page_number=chunk_data.get("page_number"),
                        section_type=chunk_data.get("section_type"),
                        score=chunk_data.get("score", 0.0),
                    )
                )

        total_time = time() - start_time

        logger.info(
            f"Query completed in {total_time:.2f}s (retrieval: {retrieval_time:.2f}s, generation: {generation_time:.2f}s)"
        )

        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=sources,
            retrieval_time=retrieval_time,
            generation_time=generation_time,
            total_time=total_time,
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
