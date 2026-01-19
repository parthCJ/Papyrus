from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from time import time
import json
from app.models.schemas import QueryRequest, QueryResponse, Source
from app.api.dependencies import get_hybrid_retriever, get_llm_service
from app.core.retriever import HybridRetriever
from app.core.llm_service import LLMService
from app.utils.logger import setup_logger
from app.utils.intent_detector import detect_intent

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

        # Auto-detect intent if using default template
        template = request.prompt_template
        if template == "default":
            template = detect_intent(request.query)
            logger.info(f"Auto-detected intent: {template}")

        generation_start = time()
        answer = await llm_service.generate_answer(
            query=request.query,
            context_chunks=retrieved_chunks,
            prompt_template=template,
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


@router.post("/stream")
async def query_documents_stream(
    request: QueryRequest,
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    llm_service: LLMService = Depends(get_llm_service),
):
    """Stream query response with real-time answer generation"""

    async def generate():
        try:
            start_time = time()

            # Retrieve chunks
            retrieval_start = time()
            retrieved_chunks = await retriever.hybrid_search(
                query=request.query, top_k=request.top_k
            )
            retrieval_time = time() - retrieval_start

            # Send retrieval metadata
            yield f"data: {json.dumps({'type': 'metadata', 'retrieval_time': retrieval_time, 'chunks': len(retrieved_chunks)})}\n\n"

            if not retrieved_chunks:
                yield f"data: {json.dumps({'type': 'answer', 'content': 'No relevant documents found for your query.'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            # Auto-detect intent if using default template
            template = request.prompt_template
            if template == "default":
                template = detect_intent(request.query)
                logger.info(f"Auto-detected intent for stream: {template}")

            # Check if LLM service supports streaming
            if hasattr(llm_service, "generate_answer_stream"):
                # Stream answer
                generation_start = time()
                full_answer = ""

                async for chunk in llm_service.generate_answer_stream(
                    query=request.query,
                    context_chunks=retrieved_chunks,
                    prompt_template=template,
                ):
                    full_answer += chunk
                    yield f"data: {json.dumps({'type': 'answer', 'content': chunk})}\n\n"

                generation_time = time() - generation_start
            else:
                # Fallback to non-streaming
                generation_start = time()
                full_answer = await llm_service.generate_answer(
                    query=request.query,
                    context_chunks=retrieved_chunks,
                    prompt_template=template,
                )
                generation_time = time() - generation_start
                yield f"data: {json.dumps({'type': 'answer', 'content': full_answer})}\n\n"

            # Send sources if requested
            if request.include_sources:
                sources = []
                for chunk_data in retrieved_chunks:
                    sources.append(
                        {
                            "document_id": chunk_data.get("document_id", "unknown"),
                            "title": chunk_data.get("title", "Unknown"),
                            "chunk_id": chunk_data.get("chunk_id", "unknown"),
                            "content": chunk_data.get("content", ""),
                            "page_number": chunk_data.get("page_number"),
                            "section_type": chunk_data.get("section_type"),
                            "score": chunk_data.get("score", 0.0),
                        }
                    )
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

            # Send completion metadata
            total_time = time() - start_time
            yield f"data: {json.dumps({'type': 'timing', 'generation_time': generation_time, 'total_time': total_time})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Error streaming query: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
