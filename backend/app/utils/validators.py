"""
Layer 1: Structural Validators
Layer 2: Evidence Coverage Checks

These catch 80% of failures instantly without LLM calls.
"""

import re
from typing import List, Dict, Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ValidationResult:
    """Result of validation check"""

    def __init__(self, passed: bool, reason: str = "", severity: str = "error"):
        self.passed = passed
        self.reason = reason
        self.severity = severity  # "error", "warning"

    def __bool__(self):
        return self.passed

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"{status}: {self.reason}" if self.reason else status


class StructuralValidator:
    """Layer 1: Fast, deterministic structural checks"""

    @staticmethod
    def validate_table_usage(answer: str, question: str) -> ValidationResult:
        """Check if table is appropriately used"""
        has_table = "|" in answer and "---" in answer

        # Check if question is comparison/differentiation
        comparison_keywords = [
            "differentiate",
            "compare",
            "contrast",
            "distinguish",
            "vs",
            "versus",
            "difference between",
        ]
        is_comparison = any(kw in question.lower() for kw in comparison_keywords)

        # Check if question asks for author list
        author_keywords = ["list authors", "name authors", "who wrote", "authors of"]
        is_author_list = any(kw in question.lower() for kw in author_keywords)

        # Table should exist for comparisons/author lists
        if (is_comparison or is_author_list) and not has_table:
            return ValidationResult(
                False,
                "Expected table for comparison/author query but none found",
                severity="warning",
            )

        # Table should NOT exist for non-comparison questions
        if has_table and not (is_comparison or is_author_list):
            # Exception: "authors argue" is not asking for table
            if (
                "authors argue" in question.lower()
                or "author argues" in question.lower()
            ):
                return ValidationResult(
                    False, "Unexpected table for 'authors argue' question"
                )

            return ValidationResult(
                False, "Unexpected table in non-comparison answer", severity="warning"
            )

        return ValidationResult(True)

    @staticmethod
    def validate_whitespace(answer: str) -> ValidationResult:
        """Check for leading whitespace or blank lines"""
        if answer.startswith(("\n", " ", "\t")):
            return ValidationResult(False, "Answer starts with whitespace/blank line")

        # Check for excessive blank lines in middle
        if "\n\n\n" in answer:
            return ValidationResult(
                False, "Excessive blank lines in answer", severity="warning"
            )

        return ValidationResult(True)

    @staticmethod
    def validate_verification_format(answer: str, question: str) -> ValidationResult:
        """Check Yes/No questions have proper prefix"""
        verification_starters = [
            "is",
            "does",
            "do",
            "are",
            "was",
            "were",
            "can",
            "will",
        ]

        # Check if question is verification type
        first_word = question.lower().split()[0] if question else ""
        is_verification = first_word in verification_starters

        if is_verification:
            if not answer.startswith(("Yes,", "No,", "Yes.", "No.", "Yes -", "No -")):
                return ValidationResult(
                    False,
                    f"Verification question should start with 'Yes,' or 'No,' (starts with: '{answer[:50]}')",
                )

        return ValidationResult(True)

    @staticmethod
    def validate_length(
        answer: str, min_length: int = 20, max_length: int = 2000
    ) -> ValidationResult:
        """Check answer is reasonable length"""
        length = len(answer.strip())

        if length < min_length:
            return ValidationResult(False, f"Answer too short ({length} chars)")

        if length > max_length:
            return ValidationResult(
                False,
                f"Answer too long ({length} chars), possible runaway generation",
                severity="warning",
            )

        return ValidationResult(True)

    @staticmethod
    def validate_no_meta_text(answer: str) -> ValidationResult:
        """Check for unwanted meta-commentary"""
        meta_phrases = [
            "i cannot",
            "i don't have",
            "as an ai",
            "i apologize",
            "based on the context provided",
            "according to the document",
        ]

        answer_lower = answer.lower()
        for phrase in meta_phrases:
            if phrase in answer_lower:
                return ValidationResult(
                    False, f"Contains meta-commentary: '{phrase}'", severity="warning"
                )

        return ValidationResult(True)


class EvidenceValidator:
    """Layer 2: Evidence coverage checks"""

    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitter
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    @staticmethod
    def is_factual_claim(sentence: str) -> bool:
        """Heuristic to detect factual claims vs meta-text"""
        # Skip if too short
        if len(sentence) < 15:
            return False

        # Skip meta-text
        meta_indicators = ["the context", "the document", "according to", "based on"]
        if any(ind in sentence.lower() for ind in meta_indicators):
            return False

        # Likely factual if contains specific terms
        factual_indicators = ["shows", "demonstrates", "achieves", "uses", "proposes"]
        return any(ind in sentence.lower() for ind in factual_indicators)

    @staticmethod
    def has_citation(sentence: str) -> bool:
        """Check if sentence has citation markers"""
        # Look for [citation], (citation), or academic patterns
        citation_patterns = [
            r"\[.*?\]",  # [1], [Author et al.]
            r"\(.*?\d{4}.*?\)",  # (Author, 2023)
            r"\bet al\.",  # et al.
        ]
        return any(re.search(pattern, sentence) for pattern in citation_patterns)

    @staticmethod
    def calculate_context_overlap(answer: str, context_chunks: List[str]) -> float:
        """Calculate what % of answer tokens appear in context"""
        if not context_chunks:
            return 0.0

        # Get unique important words from answer (exclude stopwords)
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
        }
        answer_words = set(re.findall(r"\b\w{4,}\b", answer.lower()))  # 4+ char words
        answer_words -= stopwords

        if not answer_words:
            return 1.0  # No content words to check

        # Get all words from context
        context_text = " ".join(context_chunks).lower()
        context_words = set(re.findall(r"\b\w{4,}\b", context_text))

        # Calculate overlap
        overlap = len(answer_words & context_words)
        return overlap / len(answer_words)

    @staticmethod
    def validate_evidence_coverage(
        answer: str, context_chunks: List[str], min_overlap: float = 0.5
    ) -> ValidationResult:
        """Check if answer is grounded in retrieved context"""
        if not context_chunks:
            return ValidationResult(
                False, "No context chunks provided for evidence check"
            )

        overlap = EvidenceValidator.calculate_context_overlap(answer, context_chunks)

        if overlap < min_overlap:
            return ValidationResult(
                False,
                f"Low evidence coverage ({overlap:.1%} < {min_overlap:.0%}), possible hallucination",
                severity="warning",
            )

        return ValidationResult(True, f"Evidence coverage: {overlap:.1%}")

    @staticmethod
    def validate_factual_claims_have_support(
        answer: str, context_chunks: List[str]
    ) -> ValidationResult:
        """Check if factual claims have citations or context support"""
        sentences = EvidenceValidator.split_sentences(answer)
        factual_sentences = [
            s for s in sentences if EvidenceValidator.is_factual_claim(s)
        ]

        if not factual_sentences:
            return ValidationResult(True, "No factual claims to verify")

        unsupported = []
        for sentence in factual_sentences:
            has_cite = EvidenceValidator.has_citation(sentence)

            # Check if sentence words appear in context
            sentence_words = set(re.findall(r"\b\w{4,}\b", sentence.lower()))
            context_text = " ".join(context_chunks).lower()
            in_context = any(
                word in context_text for word in sentence_words if len(word) > 5
            )

            if not has_cite and not in_context:
                unsupported.append(sentence[:80])

        if unsupported:
            return ValidationResult(
                False,
                f"Found {len(unsupported)} unsupported claims: {unsupported[0]}...",
                severity="warning",
            )

        return ValidationResult(
            True, f"All {len(factual_sentences)} factual claims have support"
        )


class AnswerValidator:
    """Main validator combining all layers"""

    def __init__(self):
        self.structural = StructuralValidator()
        self.evidence = EvidenceValidator()

    def validate_all(
        self, answer: str, question: str, context_chunks: List[str] = None
    ) -> Dict[str, ValidationResult]:
        """Run all validation checks"""
        results = {}

        # Layer 1: Structural
        results["table_usage"] = self.structural.validate_table_usage(answer, question)
        results["whitespace"] = self.structural.validate_whitespace(answer)
        results["verification_format"] = self.structural.validate_verification_format(
            answer, question
        )
        results["length"] = self.structural.validate_length(answer)
        results["no_meta_text"] = self.structural.validate_no_meta_text(answer)

        # Layer 2: Evidence (if context provided)
        if context_chunks:
            results["evidence_coverage"] = self.evidence.validate_evidence_coverage(
                answer, context_chunks
            )
            results["factual_support"] = (
                self.evidence.validate_factual_claims_have_support(
                    answer, context_chunks
                )
            )

        return results

    def get_failures(
        self, validation_results: Dict[str, ValidationResult]
    ) -> List[Tuple[str, ValidationResult]]:
        """Get all failed validations"""
        return [
            (name, result)
            for name, result in validation_results.items()
            if not result.passed
        ]

    def log_validation_results(
        self, validation_results: Dict[str, ValidationResult], query: str = ""
    ):
        """Log validation results"""
        failures = self.get_failures(validation_results)

        if not failures:
            logger.info(f"✓ All validations passed for query: {query[:50]}")
            return

        # Log failures by severity
        errors = [f for f in failures if f[1].severity == "error"]
        warnings = [f for f in failures if f[1].severity == "warning"]

        if errors:
            logger.error(f"✗ {len(errors)} validation error(s) for query: {query[:50]}")
            for name, result in errors:
                logger.error(f"  - {name}: {result.reason}")

        if warnings:
            logger.warning(
                f"⚠ {len(warnings)} validation warning(s) for query: {query[:50]}"
            )
            for name, result in warnings:
                logger.warning(f"  - {name}: {result.reason}")
