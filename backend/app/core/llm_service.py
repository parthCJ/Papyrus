import httpx
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import setup_logger
from app.core.prompt_templates import get_prompt_template
import re

logger = setup_logger(__name__)


class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        prompt_template: str = "default",
    ) -> str:

        intent = self._classify_query(query)
        context_text = self._format_context(context_chunks, query)

        prompt = self._build_prompt(query, context_text, prompt_template)

        max_tokens = self._max_tokens_by_intent(intent)

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": max_tokens,
                        "num_ctx": 3072,
                        "num_thread": 8,
                        "stop": [
                            "\n\n\n",
                            "Question:",
                            "Context:",
                            "[Source",
                        ],
                    },
                },
            )

            response.raise_for_status()
            result = response.json()

            answer = result.get("response", "").strip()

            while answer.startswith("\n"):
                answer = answer[1:]

            logger.info(f"Generated answer | intent={intent} | length={len(answer)}")

            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I encountered an error generating the answer."

    # -----------------------------
    # Context compression
    # -----------------------------
    def _format_context(
        self,
        chunks: List[Dict[str, Any]],
        query: str,
    ) -> str:
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            text = chunk.get("content", "")
            compressed = self._compress_text(text, query)
            context_parts.append(f"[Source {i}] {compressed}")

        return "\n\n".join(context_parts)

    def _compress_text(self, text: str, query: str, max_sentences: int = 4) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return " ".join(sentences[:max_sentences])

    # -----------------------------
    # Intent detection
    # -----------------------------
    def _classify_query(self, query: str) -> str:
        q = query.lower()

        if any(k in q for k in ["what is", "define"]):
            return "definition"
        if any(k in q for k in ["parameter", "parameters", "weights", "matrix"]):
            return "parameters"
        if any(k in q for k in ["true or false", "is it true", "verify"]):
            return "verification"
        if any(k in q for k in ["evidence", "signatures", "identify"]):
            return "observation"
        if any(k in q for k in ["why", "argue", "explain"]):
            return "explanation"

        return "general"

    # -----------------------------
    # Output length control
    # -----------------------------
    def _max_tokens_by_intent(self, intent: str) -> int:
        return {
            "definition": 80,
            "parameters": 60,
            "verification": 40,
            "observation": 120,
            "explanation": 150,
            "general": 150,
        }.get(intent, 150)

    def _build_prompt(
        self, query: str, context: str, prompt_template: str = "default"
    ) -> str:
        template = get_prompt_template(prompt_template)
        return template.format(context=context, query=query)

    async def close(self):
        await self.client.aclose()
