"""
Fine-tune embedding model for domain-specific papers
Run: python scripts/finetune_embeddings.py
"""

from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import torch


def finetune_embeddings():
    # Load base model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Create training examples (question, positive answer, negative answer)
    train_examples = [
        InputExample(
            texts=[
                "What is attention?",
                "Attention mechanism focuses on relevant parts",
            ]
        ),
        InputExample(
            texts=["Explain transformers", "Transformers use self-attention layers"]
        ),
        # Add more domain-specific examples from your papers
    ]

    # Create DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

    # Define loss
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # Fine-tune
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=3,
        warmup_steps=100,
        output_path="./models/finetuned-embeddings",
    )

    print("Fine-tuning complete! Model saved to ./models/finetuned-embeddings")


if __name__ == "__main__":
    finetune_embeddings()
