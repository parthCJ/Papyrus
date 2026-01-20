"""
Regression Test Suite
Tests that prevent known bugs from recurring
"""

from typing import Dict, List
from app.utils.validators import AnswerValidator


# Known failure patterns from development
REGRESSION_TESTS = [
    {
        "name": "cold_fronts_entropy_confusion",
        "question": "What is entropy in the context of cold fronts?",
        "bad_answer": "Entropy measures disorder in thermodynamics...",
        "context": ["The Transformer uses self-attention", "attention mechanisms"],
        "expected_failure": "evidence_coverage",
        "reason": "Should not hallucinate about physics when paper is about NLP",
    },
    {
        "name": "authors_argue_table_misfire",
        "question": "Why do the authors argue self-attention is beneficial?",
        "bad_answer": "| Author | Argument |\n|--------|----------|\n| Smith | ...",
        "context": [],
        "expected_failure": "table_usage",
        "reason": "Should not generate table for 'authors argue' question",
    },
    {
        "name": "comparison_missing_table",
        "question": "What are the differences between BERT and GPT?",
        "bad_answer": "BERT uses bidirectional attention while GPT is autoregressive.",
        "context": [],
        "expected_failure": "table_usage",
        "reason": "Should generate comparison table for differentiate question",
    },
    {
        "name": "verification_missing_prefix",
        "question": "Does the Transformer use recurrence?",
        "bad_answer": "The Transformer architecture does not use recurrence.",
        "expected_failure": "verification_format",
        "reason": "Verification questions must start with Yes/No",
    },
    {
        "name": "whitespace_before_table",
        "question": "Compare attention mechanisms",
        "bad_answer": "\n\n\n| Mechanism | Description |\n|-----------|-------------|\n| Self | ...",
        "expected_failure": "whitespace",
        "reason": "Tables must not have leading whitespace",
    },
    {
        "name": "meta_commentary",
        "question": "What is the main contribution?",
        "bad_answer": "Based on the context provided, the main contribution is...",
        "expected_failure": "no_meta_text",
        "reason": "Should not include meta-commentary about 'the context'",
    },
    {
        "name": "too_short_answer",
        "question": "Explain the attention mechanism in detail",
        "bad_answer": "Self-attention.",
        "expected_failure": "length",
        "reason": "Answer too short for detailed question",
    },
]


class RegressionTester:
    """Runner for regression tests"""

    def __init__(self):
        self.validator = AnswerValidator()

    def run_test(self, test: Dict) -> bool:
        """Run a single regression test"""
        validation_results = self.validator.validate_all(
            answer=test["bad_answer"],
            question=test["question"],
            context_chunks=test.get("context", []),  # Use context if provided
        )

        # Check if expected failure occurred
        expected_failure = test["expected_failure"]

        if expected_failure in validation_results:
            failed = not validation_results[expected_failure].passed
            return failed

        return False

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all regression tests"""
        results = {}

        for test in REGRESSION_TESTS:
            test_name = test["name"]
            passed = self.run_test(test)
            results[test_name] = passed

            if passed:
                print(f"✓ {test_name}: Correctly caught failure")
            else:
                print(f"✗ {test_name}: REGRESSION - missed failure!")
                print(f"  Reason: {test['reason']}")

        return results

    def assert_no_regressions(self):
        """Assert all regression tests pass"""
        results = self.run_all_tests()
        failures = [name for name, passed in results.items() if not passed]

        if failures:
            raise AssertionError(
                f"Regression detected! {len(failures)} tests failed: {failures}"
            )


# Pytest integration (optional - requires pytest)
def test_no_regressions():
    """Pytest: Check all known bugs are still caught"""
    tester = RegressionTester()
    tester.assert_no_regressions()


def test_table_usage_validator():
    """Test table usage validation"""
    validator = AnswerValidator()

    # Should PASS: comparison with table
    result = validator.structural.validate_table_usage(
        answer="| Model | Score |\n|-------|-------|\n| A | 90 |",
        question="Compare model A and B",
    )
    assert result.passed

    # Should FAIL: table for non-comparison
    result = validator.structural.validate_table_usage(
        answer="| Model | Score |\n|-------|-------|\n| A | 90 |",
        question="What is the main idea?",
    )
    assert not result.passed


def test_verification_format():
    """Test verification question format"""
    validator = AnswerValidator()

    # Should PASS: proper Yes/No prefix
    result = validator.structural.validate_verification_format(
        answer="Yes, the model uses attention.",
        question="Does the model use attention?",
    )
    assert result.passed

    # Should FAIL: missing Yes/No
    result = validator.structural.validate_verification_format(
        answer="The model uses attention.", question="Does the model use attention?"
    )
    assert not result.passed


def test_evidence_coverage():
    """Test evidence coverage validation"""
    validator = AnswerValidator()

    context = [
        "The Transformer uses self-attention mechanisms.",
        "It achieves BLEU score of 28.4 on WMT.",
    ]

    # Should PASS: answer grounded in context
    result = validator.evidence.validate_evidence_coverage(
        answer="The Transformer uses self-attention and achieves 28.4 BLEU on WMT.",
        context_chunks=context,
        min_overlap=0.5,
    )
    assert result.passed

    # Should FAIL: answer not in context
    result = validator.evidence.validate_evidence_coverage(
        answer="The model uses convolutional layers and batch normalization.",
        context_chunks=context,
        min_overlap=0.5,
    )
    assert not result.passed


if __name__ == "__main__":
    # Run regression tests manually
    print("Running Regression Test Suite...\n")
    tester = RegressionTester()
    results = tester.run_all_tests()

    total = len(results)
    passed = sum(results.values())

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All regression tests passed!")
    else:
        print(f"✗ {total - passed} regressions detected!")
