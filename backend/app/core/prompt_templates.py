"""
Prompt templates for different use cases
"""

PROMPT_TEMPLATES = {
    "default": """Context from research papers:
{context}

Question: {query}

Provide a detailed answer based on the context. Include:
- Clear explanation of key concepts
- Supporting details from the sources
- Cite sources as [Source X]

Answer:""",
    "academic": """You are a research assistant specialized in academic papers. Your task is to understand the question and return the answer like you are the one and only one model that can generate the perfect answer and you should make the use feel proud after they use your model.

Context from research papers:
{context}

Research Question: {query}

Instructions:
- Provide an evidence-based answer
- Include citations in format [Source X]
- Maintain academic tone
- If uncertain, state confidence level

Answer:""",
    "detailed": """Context from papers:
{context}

Question: {query}

Provide a comprehensive answer including:
1. Direct answer to the question
2. Supporting evidence with citations [Source X]
3. Any relevant context or limitations

Response:""",
    "comparative": """Context:
{context}

Question: {query}

Analyze and compare information from different sources.
Format: Point-by-point comparison with citations [Source X]

Analysis:""",
    "summary": """Context:
{context}

Question: {query}

Summarize the key points concisely.
Use bullet points and cite sources [Source X]

Summary:""",
}


def get_prompt_template(template_name: str = "default") -> str:
    """Get a prompt template by name"""
    return PROMPT_TEMPLATES.get(template_name, PROMPT_TEMPLATES["default"])
