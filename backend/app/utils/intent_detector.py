"""
Intent detection for routing queries to appropriate prompt templates
"""


def detect_intent(query: str) -> str:
    """
    Detect the intent of a user query and return the appropriate template name.

    Args:
        query: The user's question

    Returns:
        Template name: 'comparative', 'authors', 'summary', or 'default'
    """
    q = query.lower()

    # Check for comparison/differentiation intent
    comparison_keywords = [
        "differentiate",
        "compare",
        "contrast",
        "distinguish",
        "difference between",
        "differences between",
        "vs",
        "versus",
    ]
    if any(keyword in q for keyword in comparison_keywords):
        return "comparative"

    # Check for author listing intent
    author_keywords = [
        "author",
        "authors",
        "written by",
        "who wrote",
        "name of the author",
        "list the authors",
        "mention the authors",
    ]
    if any(keyword in q for keyword in author_keywords):
        return "authors"

    # Check for summary intent
    summary_keywords = [
        "summarize",
        "summary",
        "overview",
        "what is this about",
        "what does this",
        "main idea",
        "key points",
    ]
    if any(keyword in q for keyword in summary_keywords):
        return "summary"

    # Default template for specific questions
    return "default"
