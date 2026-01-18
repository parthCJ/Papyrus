# ResearchRAG

RAG system for research papers with hybrid search (BM25 + Vector) and fast LLM generation.

## Features

- Hybrid retrieval (BM25 + semantic search)
- Groq API integration (2s responses) or local Ollama
- Web UI with adjustable search settings
- PDF upload and document management
- FastAPI backend with Elasticsearch

## Quick Start

```bash
docker-compose up -d
docker exec -it research-rag-ollama ollama pull llama3.2
```

**Groq Setup** (recommended for speed):

1. Get API key: https://console.groq.com
2. Edit `backend/.env`: `GROQ_API_KEY=gsk_...`
3. Restart: `docker compose restart backend`

**Access**:

- Web UI: http://localhost:3000
- API docs: http://localhost:8000/docs

## Tech Stack

FastAPI • Elasticsearch • Groq/Ollama • sentence-transformers

## Configuration

Edit `backend/.env`:

```env
LLM_PROVIDER=groq              # or 'ollama' for local
GROQ_API_KEY=your_key_here
TOP_K_RETRIEVAL=5
BM25_WEIGHT=0.3
VECTOR_WEIGHT=0.7
CHUNK_SIZE=300
```

## API Usage

```bash
# Upload
curl -X POST http://localhost:8000/api/v1/upload/pdf -F "file=@paper.pdf"

# Query
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "What are transformers?", "top_k": 5}'
```

## Fine-tune Embeddings (Optional)

```bash
cd backend
pip install -r requirements-finetune.txt
python scripts/generate_training_data.py
python scripts/finetune_embeddings_new.py --epochs 3
```

See [FINETUNING_GUIDE.md](FINETUNING_GUIDE.md) for details.

## License

MIT
