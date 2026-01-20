from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "ResearchRAG"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX: str = "research_papers"

    # LLM Provider (ollama or groq)
    LLM_PROVIDER: str = "groq"  # Change to "ollama" to use local Ollama

    # Ollama settings (for local LLM)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Groq settings (for cloud LLM)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384

    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    BM25_WEIGHT: float = 0.4
    VECTOR_WEIGHT: float = 0.6

    # Reduced from 5 to 3 for faster retrieval
    TOP_K_RETRIEVAL: int = 3

    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    UPLOAD_DIR: str = "data/raw"
    PROCESSED_DIR: str = "data/processed"

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
