"""
Layer 3: LLM-as-a-Judge
Uses another LLM call to validate answer quality
"""

from typing import Dict, List
from app.core.groq_service import GroqService
from app.utils.logger import setup_logger
from app.utils.validators import ValidationResult

logger = setup_logger(__name__)


class LLMJudge:
    """LLM-based answer validation"""

    def __init__(self):
        self.llm = GroqService()

    def get_judge_prompt(self, question: str, answer: str, context: str) -> str:
        """Create prompt for LLM judge"""
        return f"""You are a strict research paper validator. Your job is to find problems, not praise.

QUESTION: {question}

RETRIEVED CONTEXT:
{context}

GENERATED ANSWER:
{answer}

VALIDATION TASKS:
1. List any claims in the answer NOT supported by the context
2. Identify if the answer substitutes interpretation for direct observation
3. Check if tables, equations, or figures mentioned in context were ignored
4. Check if the answer answers the actual question asked

Respond in this format:
VERDICT: [PASS or FAIL]
ISSUES:
- [issue 1]
- [issue 2]
...

Be harsh. If you find ANY unsupported claim or hallucination, mark as FAIL."""

    async def validate_answer(
        self, question: str, answer: str, context_chunks: List[str]
    ) -> ValidationResult:
        """Use LLM to validate answer quality"""
        try:
            # Combine context
            context = "\n\n".join(context_chunks[:3])  # Use top 3 chunks

            # Get judge prompt
            prompt = self.get_judge_prompt(question, answer, context)

            # Call LLM (using Groq for fast inference)
            judgment = await self.llm.generate_response(
                prompt=prompt,
                temperature=0.1,  # Low temp for consistent judging
                max_tokens=300,
            )

            # Parse judgment
            is_pass = "VERDICT: PASS" in judgment.upper()

            # Extract issues
            issues = []
            if "ISSUES:" in judgment:
                issues_section = judgment.split("ISSUES:")[1].strip()
                issues = [
                    line.strip("- ").strip()
                    for line in issues_section.split("\n")
                    if line.strip().startswith("-")
                ]

            if is_pass:
                return ValidationResult(True, "LLM judge approved answer")
            else:
                issue_summary = (
                    "; ".join(issues[:2]) if issues else "Multiple issues found"
                )
                return ValidationResult(False, f"LLM judge rejected: {issue_summary}")

        except Exception as e:
            logger.error(f"LLM judge failed: {e}")
            return ValidationResult(
                True, "LLM judge unavailable (skipped)", severity="warning"
            )

    def validate_answer_sync(
        self, question: str, answer: str, context_chunks: List[str]
    ) -> ValidationResult:
        """Synchronous version for non-async contexts"""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.validate_answer(question, answer, context_chunks)
        )
