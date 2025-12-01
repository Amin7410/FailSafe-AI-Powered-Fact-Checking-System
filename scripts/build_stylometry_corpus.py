# scripts/build_stylometry_corpus.py

import sys
import os
import re
import json
import pickle
import math
import numpy as np
from pathlib import Path
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.append(str(Path(__file__).resolve().parent.parent))

from factcheck.utils.config_loader import PROJECT_ROOT

try:
    from datasets import load_dataset
except ImportError:
    print("Error: Library 'datasets' not found.")
    print("Please run: pip install datasets scikit-learn numpy")
    sys.exit(1)

MODEL_DIR = PROJECT_ROOT / "models" / "stylometry"
IDF_VECTOR_PATH = MODEL_DIR / "idf_vector.pkl"
ENTROPY_STATS_PATH = MODEL_DIR / "entropy_stats.json"


def calculate_entropy(text: str):
    tokens = re.findall(r'\b\w+\b', text.lower())
    if not tokens:
        return 0
    
    counts = Counter(tokens)
    total_tokens = len(tokens)
    
    probabilities = [count / total_tokens for count in counts.values()]
    
    entropy = -sum(p * math.log2(p) for p in probabilities)
    return entropy


def main():
    print(f"Output Directory: {MODEL_DIR}")
    
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        print("   -> Directory created.")

    print("\n[1/3] Loading dataset 'ag_news' from Hugging Face...")
    try:
        dataset = load_dataset("ag_news", split="train[:10000]")
        corpus = dataset['text']
        print(f"   -> Loaded {len(corpus)} documents.")
    except Exception as e:
        print(f"   -> Error loading dataset: {e}")
        return

    print("\n[2/3] Training TF-IDF Vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=20000, 
        use_idf=True, 
        smooth_idf=True, 
        norm=None,
        stop_words='english'
    )
    vectorizer.fit(corpus)
   
    with open(IDF_VECTOR_PATH, 'wb') as f:
        pickle.dump(vectorizer, f)
    print(f"   -> Saved IDF model to: {IDF_VECTOR_PATH.name}")

    print("\n[3/3] Calculating Entropy Statistics...")
    entropy_values = [calculate_entropy(text) for text in corpus]

    mean_entropy = np.mean(entropy_values)
    std_entropy = np.std(entropy_values)
    
    entropy_stats = {
        "mean": float(mean_entropy),
        "std": float(std_entropy),
        "sample_size": len(corpus),
        "description": "Baseline statistics from AG News dataset (10k samples)"
    }

    with open(ENTROPY_STATS_PATH, 'w') as f:
        json.dump(entropy_stats, f, indent=2)
    
    print(f"   -> Saved stats to: {ENTROPY_STATS_PATH.name}")
    print("\n=== STYLOMETRY BUILD COMPLETE ===")


if __name__ == "__main__":
    main()