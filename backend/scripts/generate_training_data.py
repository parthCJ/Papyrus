"""
Extract training data from your uploaded documents for embedding fine-tuning

This script:
1. Connects to Elasticsearch
2. Retrieves your uploaded documents
3. Creates question-answer pairs automatically
4. Generates training data for fine-tuning

Usage:
    python scripts/generate_training_data.py --output training_data.json --limit 100
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.elasticsearch_client import ElasticsearchClient
from app.config import settings
import random


async def extract_training_pairs():
    """Extract training data from indexed documents"""

    print("Connecting to Elasticsearch...")
    es_client = ElasticsearchClient()
    await es_client.initialize()

    print("Fetching documents...")
    documents = await es_client.list_documents(limit=100)

    if len(documents) == 0:
        print("No documents found! Upload some PDFs first.")
        return []

    print(f"Found {len(documents)} documents")

    training_data = []

    # Generate training pairs from each document
    for doc in documents:
        doc_detail = await es_client.get_document(doc.document_id)

        if not doc_detail:
            continue

        # Get document title and abstract
        title = doc_detail.title
        abstract = doc_detail.abstract or ""

        # Create question-answer pairs
        if abstract:
            # Pair 1: "What is this paper about?" -> abstract
            training_data.append(
                {
                    "query": f"What is {title} about?",
                    "positive": abstract[:500],
                    "negative": "This is unrelated content about computer vision.",
                }
            )

            # Pair 2: Title -> abstract
            training_data.append(
                {
                    "query": title,
                    "positive": abstract[:500],
                    "negative": "Random irrelevant text about different topic.",
                }
            )

        # Fetch some chunks from this document
        search_query = {
            "query": {"term": {"document_id": doc.document_id}},
            "size": 5,
            "_source": ["content", "chunk_id"],
        }

        response = await es_client.client.search(
            index=es_client.chunk_index_name, body=search_query
        )

        chunks = [hit["_source"]["content"] for hit in response["hits"]["hits"]]

        # Create pairs from chunks
        for i, chunk in enumerate(chunks):
            if len(chunk) < 50:
                continue

            # Pair chunks from same document (positive)
            if i + 1 < len(chunks):
                training_data.append(
                    {
                        "sentence1": chunk[:300],
                        "sentence2": chunks[i + 1][:300],
                        "score": 0.7,  # Same document, moderately similar
                    }
                )

            # Title -> chunk (positive)
            training_data.append(
                {
                    "query": title,
                    "positive": chunk[:300],
                    "negative": "Unrelated text from different field.",
                }
            )

    await es_client.close()

    print(f"\nGenerated {len(training_data)} training pairs")
    return training_data


async def generate_training_data(
    output_path: str = "training_data.json", limit: int = 100
):
    """Generate and save training data"""

    training_data = await extract_training_pairs()

    if not training_data:
        print("No training data generated. Upload documents first!")
        return

    # Shuffle and limit
    random.shuffle(training_data)
    training_data = training_data[:limit]

    # Save
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(training_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Training data saved to: {output_path}")
    print(f"✓ Total pairs: {len(training_data)}")
    print(f"\nNext steps:")
    print(f"  1. Review and edit {output_path} to improve quality")
    print(f"  2. Run: python scripts/finetune_embeddings_new.py --data {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate training data from documents"
    )
    parser.add_argument(
        "--output", default="training_data.json", help="Output file path"
    )
    parser.add_argument(
        "--limit", type=int, default=100, help="Max training pairs to generate"
    )

    args = parser.parse_args()

    asyncio.run(generate_training_data(args.output, args.limit))


if __name__ == "__main__":
    main()
