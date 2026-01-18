import httpx
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import setup_logger
from app.core.prompt_templates import get_prompt_template

logger = setup_logger(__name__)


class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        prompt_template: str = "default",
    ) -> str:
        context_text = self._format_context(context_chunks)

        prompt = self._build_prompt(query, context_text, prompt_template)

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "top_p": 0.9,
                        "num_predict": 200,
                        "num_ctx": 1024,
                        "num_thread": 8,
                        "stop": ["\n\n\n", "Question:", "Context:"],
                    },
                },
            )

            response.raise_for_status()
            result = response.json()

            answer = result.get("response", "").strip()

            logger.info(f"Generated answer of length {len(answer)}")

            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I apologize, but I encountered an error generating the answer. Please try again."

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "")[
                :200
            ]  # Limit to 200 chars per chunk for speed

            context_parts.append(f"[{i}] {content}")

        return "\n".join(context_parts)

    def _build_prompt(
        self, query: str, context: str, prompt_template: str = "default"
    ) -> str:
        template = get_prompt_template(prompt_template)
        prompt = template.format(context=context, query=query)
        return prompt

    async def close(self):
        await self.client.aclose()
