#!/usr/bin/env python3
from __future__ import annotations

"""
Build a small local knowledge base:
- Load a tiny subset from FEVER-like JSONL (if provided) and Simple English abstracts (optional).
- Create embeddings using existing services.
- Build and persist a FAISS index and metadata under data/embeddings/.

Usage:
  python scripts/build_knowledge_base.py --input data/corpus/seed.jsonl --output data/embeddings
If --input is omitted, will fall back to whatever corpus RetrievalService would use.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

import faiss  # type: ignore

import sys

# Allow importing app services when running from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from backend.app.services.embedding_service import embed_texts


def load_corpus(input_path: Path) -> List[Dict]:
    docs: List[Dict] = []
    if input_path.exists():
        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if all(k in obj for k in ("id", "title", "url", "text")):
                    docs.append(obj)
    return docs


def build_index(docs: List[Dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    texts = [d["text"] for d in docs]
    if not texts:
        print("No documents found. Exiting.")
        return

    vectors = embed_texts(texts)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    faiss_path = output_dir / "faiss.index"
    meta_path = output_dir / "faiss_meta.json"

    faiss.write_index(index, str(faiss_path))
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump({"count": len(texts), "docs": docs}, f, ensure_ascii=False)

    print(f"Saved FAISS index to {faiss_path}")
    print(f"Saved metadata to {meta_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=str(ROOT / "data" / "corpus" / "seed.jsonl"))
    parser.add_argument("--output", type=str, default=str(ROOT / "data" / "embeddings"))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    docs = load_corpus(input_path)
    if not docs:
        print(f"No docs loaded from {input_path}. If this is expected, please provide an input file.")
    build_index(docs, output_dir)


if __name__ == "__main__":
    main()


