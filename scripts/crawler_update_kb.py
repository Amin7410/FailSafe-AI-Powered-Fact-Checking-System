#!/usr/bin/env python3
from __future__ import annotations

"""
Simple crawler/update script:
- Fetch a few RSS/news items and arXiv abstracts (placeholder).
- Append to data/corpus/news.jsonl and data/corpus/research.jsonl.
- Rebuild FAISS index via build_knowledge_base.py.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "corpus"


def fetch_news_samples() -> List[Dict]:
    # Placeholder: static samples
    return [
        {
            "id": "news:sample1",
            "title": "Science report indicates vaccine effectiveness",
            "url": "https://news.example.com/vaccine",
            "text": "A recent report summarizes evidence of vaccine effectiveness.",
        }
    ]


def fetch_research_samples() -> List[Dict]:
    return [
        {
            "id": "arxiv:sample1",
            "title": "A study on misinformation detection",
            "url": "https://arxiv.org/abs/0000.0000",
            "text": "This paper explores detection of misinformation using embeddings.",
        }
    ]


def append_jsonl(path: Path, docs: List[Dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return len(docs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    news = fetch_news_samples()
    research = fetch_research_samples()

    n1 = append_jsonl(DATA_DIR / "news.jsonl", news)
    n2 = append_jsonl(DATA_DIR / "research.jsonl", research)
    print(f"Appended: news={n1}, research={n2}")

    if args.rebuild:
        # Rebuild FAISS index combining all corpus files is handled by build_knowledge_base.py
        from subprocess import run
        run(["python", str(ROOT / "scripts" / "build_knowledge_base.py")], check=False)


if __name__ == "__main__":
    main()


