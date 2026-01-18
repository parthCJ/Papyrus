from sentence_transformers import SentenceTransformer
from typing import List
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return

        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self._initialized = True
        logger.info("Embedding model loaded successfully")

    def embed_text(self, text: str) -> List[float]:
        if not self._initialized:
            self.initialize()

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        if not self._initialized:
            self.initialize()

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.tolist()
