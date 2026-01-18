"""
Fine-tune embedding model for domain-specific papers

Usage:
    python scripts/finetune_embeddings.py --data training_data.json --epochs 3

Requirements:
    pip install sentence-transformers datasets
"""

from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from torch.utils.data import DataLoader
import json
import argparse
from pathlib import Path
from typing import List
import random


def load_training_data(data_path: str) -> List[InputExample]:
    """
    Load training data from JSON file
    Format: [{"query": "question", "positive": "relevant text", "negative": "irrelevant text"}]
    Or: [{"sentence1": "text1", "sentence2": "similar text2", "score": 0.9}]
    """
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = []

    for item in data:
        if "query" in item and "positive" in item:
            # Triplet format (query, positive, negative)
            texts = [item["query"], item["positive"]]
            if "negative" in item:
                texts.append(item["negative"])
            examples.append(InputExample(texts=texts))

        elif "sentence1" in item and "sentence2" in item:
            # Sentence pair with similarity score
            examples.append(
                InputExample(
                    texts=[item["sentence1"], item["sentence2"]],
                    label=float(item.get("score", 1.0)),
                )
            )

    print(f"Loaded {len(examples)} training examples")
    return examples


def create_sample_training_data(output_path: str = "training_data.json"):
    """
    Create sample training data - CUSTOMIZE THIS FOR YOUR DOMAIN
    """

    training_data = [
        # Question-Answer pairs from research papers
        {
            "query": "What is the transformer architecture?",
            "positive": "The Transformer is a model architecture based on self-attention mechanisms, eschewing recurrence entirely.",
            "negative": "We trained our model on ImageNet dataset with 1000 classes.",
        },
        {
            "query": "What is attention mechanism?",
            "positive": "Attention mechanisms allow the model to focus on different parts of the input sequence.",
            "negative": "The learning rate was set to 0.001 with Adam optimizer.",
        },
        {
            "query": "What is BERT?",
            "positive": "BERT stands for Bidirectional Encoder Representations from Transformers.",
            "negative": "The dataset contains 10,000 images collected from the internet.",
        },
        # Similar sentence pairs
        {
            "sentence1": "deep neural network",
            "sentence2": "multi-layer neural network",
            "score": 0.9,
        },
        {
            "sentence1": "machine learning model",
            "sentence2": "statistical learning algorithm",
            "score": 0.85,
        },
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(training_data, f, indent=2)

    print(f"Created sample training data: {output_path}")
    print("IMPORTANT: Replace with real data from your papers!")
    return output_path


def finetune_embeddings(
    base_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    training_data_path: str = "training_data.json",
    output_path: str = "./models/finetuned-embeddings",
    epochs: int = 3,
    batch_size: int = 16,
):
    """Fine-tune embedding model"""

    print(f"Loading base model: {base_model}")
    model = SentenceTransformer(base_model)

    print(f"Loading training data from: {training_data_path}")
    train_examples = load_training_data(training_data_path)

    if len(train_examples) == 0:
        print("ERROR: No training examples found!")
        return

    # Create DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

    # Use MultipleNegativesRankingLoss
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # Create output directory
    Path(output_path).mkdir(parents=True, exist_ok=True)

    print(f"\nStarting fine-tuning:")
    print(f"  - Epochs: {epochs}")
    print(f"  - Batch size: {batch_size}")
    print(f"  - Training examples: {len(train_examples)}")
    print(f"  - Output: {output_path}")

    # Fine-tune
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=epochs,
        warmup_steps=100,
        output_path=output_path,
        show_progress_bar=True,
    )

    print(f"\n✓ Fine-tuning complete!")
    print(f"✓ Model saved to: {output_path}")
    print(f"\nTo use the fine-tuned model:")
    print(f"  1. Update backend/.env:")
    print(f"     EMBEDDING_MODEL={output_path}")
    print(f"  2. Restart backend: docker compose restart backend")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune embedding model")
    parser.add_argument(
        "--base-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Base embedding model",
    )
    parser.add_argument(
        "--data", default="training_data.json", help="Training data JSON file"
    )
    parser.add_argument(
        "--output", default="./models/finetuned-embeddings", help="Output directory"
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument(
        "--create-sample", action="store_true", help="Create sample training data"
    )

    args = parser.parse_args()

    if args.create_sample:
        data_path = create_sample_training_data(args.data)
        print(f"\nEdit {data_path} then run:")
        print(f"python scripts/finetune_embeddings.py --data {data_path}")
    else:
        if not Path(args.data).exists():
            print(f"ERROR: Training data not found: {args.data}")
            print(
                f"Create it with: python scripts/finetune_embeddings.py --create-sample"
            )
            return

        finetune_embeddings(
            base_model=args.base_model,
            training_data_path=args.data,
            output_path=args.output,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )


if __name__ == "__main__":
    main()
