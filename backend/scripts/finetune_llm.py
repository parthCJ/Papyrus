"""
Fine-tune LLM for domain-specific question answering
Requires: GPU with 16GB+ VRAM

Steps:
1. Extract QA pairs from your papers
2. Format as training data
3. Fine-tune using Ollama or HuggingFace
"""

import json
from pathlib import Path


def create_training_data():
    """
    Create QA training data from your papers
    Format: {"prompt": "question", "response": "answer with citation"}
    """

    training_data = [
        {
            "prompt": "What is the main contribution of this paper?",
            "response": "The main contribution is the introduction of the transformer architecture which uses self-attention mechanisms.",
        },
        {
            "prompt": "What datasets were used?",
            "response": "The authors used WMT 2014 English-German dataset containing 4.5 million sentence pairs.",
        },
        # Add more domain-specific examples
    ]

    # Save in JSONL format for Ollama
    with open("training_data.jsonl", "w") as f:
        for item in training_data:
            f.write(json.dumps(item) + "\n")

    print(f"Created {len(training_data)} training examples")

    # Create Modelfile for Ollama fine-tuning
    modelfile = """FROM tinyllama

# Fine-tuned on research papers
PARAMETER temperature 0.3
PARAMETER num_predict 256

# System prompt
SYSTEM You are a research assistant specialized in academic papers. Answer questions based on the provided context with citations.
"""

    with open("Modelfile", "w") as f:
        f.write(modelfile)

    print("\nTo fine-tune:")
    print("1. docker exec -it research-rag-ollama bash")
    print("2. ollama create custom-research-model -f /path/to/Modelfile")


if __name__ == "__main__":
    create_training_data()
