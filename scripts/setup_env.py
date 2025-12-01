# scripts/setup_env.py

import sys
import nltk
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))


def main():
    print("=== STARTING ENVIRONMENT & MODEL SETUP ===")

    # 1. NLTK Data
    print("\n[1/4] Downloading NLTK 'punkt' tokenizer...")
    try:
        nltk.download('punkt', quiet=True)
        print("   -> Success.")
    except Exception as e:
        print(f"   -> Error downloading NLTK data: {e}")

    print("\n[2/4] Downloading Embedding Model for ChromaDB...")
    try:
        from chromadb.utils import embedding_functions

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="intfloat/e5-base-v2"
        )

        ef(["warmup_sequence"])
        print("   -> Success.")
    except Exception as e:
        print(f"   -> Error downloading Embedding Model: {e}")

    print("\n[3/4] Downloading Deduplication Model (SentenceTransformer)...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("   -> Success.")
    except Exception as e:
        print(f"   -> Error downloading SentenceTransformer: {e}")

    print("\n[4/4] Downloading Coreference Model (FastCoref)...")
    try:
        from fastcoref import FCoref

        model = FCoref(device='cpu')
        
        print("   -> Success.")
    except Exception as e:
        print(f"   -> Error downloading FastCoref: {e}")

    print("\n=== SETUP COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()