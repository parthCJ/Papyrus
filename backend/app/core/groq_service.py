import os
from groq import AsyncGroq
from typing import List, Dict, Any
from app.config import settings
from app.utils.logger import setup_logger
from app.core.prompt_templates import get_prompt_template

logger = setup_logger(__name__)


class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.client = AsyncGroq(api_key=self.api_key)

    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        prompt_template: str = "default",
    ) -> str:
        context_text = self._format_context(context_chunks)
        prompt = self._build_prompt(query, context_text, prompt_template)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research assistant. ONLY answer using the exact information provided in the context. If information is not in the context, say so. NEVER use general knowledge or make assumptions. Cite sources for every claim.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=400,  # Reduced from 500 for faster generation
                top_p=0.9,
            )

            answer = response.choices[0].message.content.strip()
            logger.info(f"Generated answer of length {len(answer)}")

            return answer

        except Exception as e:
            logger.error(f"Error generating answer with Groq: {str(e)}")
            return "I apologize, but I encountered an error generating the answer. Please try again."

    async def generate_answer_stream(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        prompt_template: str = "default",
    ):
        """Stream answer generation chunk by chunk"""
        context_text = self._format_context(context_chunks)
        prompt = self._build_prompt(query, context_text, prompt_template)

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a research assistant. ONLY answer using the exact information provided in the context. If information is not in the context, say so. NEVER use general knowledge or make assumptions. Cite sources for every claim.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=400,  # Reduced from 500 for faster generation
                top_p=0.9,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error streaming answer with Groq: {str(e)}")
            yield "I apologize, but I encountered an error generating the answer. Please try again."

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            # Reduced from 800 to 600 chars for faster processing
            content = chunk.get("content", "")[:600]

            # Include document metadata to prevent mixing papers
            title = chunk.get("title", "Unknown")
            page = chunk.get("page_number", "?")

            context_parts.append(f"[Source {i}] ({title}, p.{page})\n{content}")

        return "\n\n".join(context_parts)

    def _build_prompt(
        self, query: str, context: str, prompt_template: str = "default"
    ) -> str:
        template = get_prompt_template(prompt_template)
        prompt = template.format(context=context, query=query)
        return prompt

    async def close(self):
        # Groq client doesn't need explicit closing
        pass
