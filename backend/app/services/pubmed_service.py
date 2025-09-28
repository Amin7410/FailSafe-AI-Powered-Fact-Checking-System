from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

import requests


class PubMedService:
    def __init__(self) -> None:
        self.api_key = os.getenv("PUBMED_API_KEY")
        self.base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.data_dir = Path(__file__).resolve().parents[3] / "data" / "corpus"
        self.cache_path = self.data_dir / "pubmed.jsonl"

    def search_ids(self, query: str, retmax: int = 10) -> List[str]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": retmax,
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        r = requests.get(f"{self.base}/esearch.fcgi", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        return data.get("esearchresult", {}).get("idlist", [])

    def fetch_summaries(self, ids: List[str]) -> List[dict]:
        if not ids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key
        r = requests.get(f"{self.base}/esummary.fcgi", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        result = data.get("result", {})
        docs: List[dict] = []
        for pid in ids:
            item = result.get(pid)
            if not item:
                continue
            title = item.get("title")
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"
            text = item.get("title", "")
            docs.append({
                "id": f"pubmed:{pid}",
                "title": title,
                "url": url,
                "text": text,
            })
        return docs

    def seed_cache(self, query: str, retmax: int = 10) -> int:
        ids = self.search_ids(query=query, retmax=retmax)
        docs = self.fetch_summaries(ids)
        if not docs:
            return 0
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("a", encoding="utf-8") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        return len(docs)



