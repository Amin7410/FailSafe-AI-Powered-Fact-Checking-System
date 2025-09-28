from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import faiss  # type: ignore

from .embedding_service import embed_texts
from .multilingual_service import MultilingualEmbeddingService, MultilingualService
from .provenance_service import provenance_tracker, ProvenanceType, SourceType
from datetime import datetime
import json
import os
import time
import hashlib


SEED_DOCS = [
    {
        "id": "doc1",
        "title": "Vaccines and autism: evidence from large-scale studies",
        "url": "https://example.org/vax-study",
        "text": "Multiple large-scale studies find no link between vaccines and autism.",
    },
    {
        "id": "doc2",
        "title": "Climate change: scientific consensus",
        "url": "https://example.org/climate-consensus",
        "text": "Over 97% of actively publishing climate scientists agree that climate-warming trends are extremely likely due to human activities.",
    },
]


class RetrievalService:
    def __init__(self) -> None:
        self._index = None
        self._texts: List[str] = []
        self._docs: List[dict] = []
        # Paths
        self._root = Path(__file__).resolve().parents[3]
        self._data_dir = self._root / "data"
        self._corpus_path = self._data_dir / "corpus" / "seed.jsonl"
        self._emb_dir = self._data_dir / "embeddings"
        self._faiss_path = self._emb_dir / "faiss.index"
        self._meta_path = self._emb_dir / "faiss_meta.json"
        # TTL cache
        self._cache: dict[str, tuple[float, list[dict]]] = {}
        # Multilingual support
        self.multilingual_embeddings = MultilingualEmbeddingService()

    def _load_corpus(self) -> Tuple[List[dict], str]:
        if self._corpus_path.exists():
            docs: List[dict] = []
            with self._corpus_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if all(k in obj for k in ("id", "title", "url", "text")):
                            docs.append(obj)
                    except json.JSONDecodeError:
                        continue
            # Merge pubmed cache if present
            pubmed_path = self._data_dir / "pubmed.jsonl"
            if pubmed_path.exists():
                with pubmed_path.open("r", encoding="utf-8") as f2:
                    for line in f2:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            if all(k in obj for k in ("id", "title", "url", "text")):
                                docs.append(obj)
                        except json.JSONDecodeError:
                            continue
            if docs:
                return docs, "file+pubmed"
        return SEED_DOCS, "seed"

    def _persist_index(self) -> None:
        try:
            self._emb_dir.mkdir(parents=True, exist_ok=True)
            if self._index is not None:
                faiss.write_index(self._index, str(self._faiss_path))
            meta = {
                "count": len(self._texts),
                "docs": self._docs,
            }
            with self._meta_path.open("w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False)
        except Exception:
            # Best-effort persistence
            pass

    def _try_load_index(self) -> bool:
        try:
            if self._faiss_path.exists() and self._meta_path.exists():
                index = faiss.read_index(str(self._faiss_path))
                with self._meta_path.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
                self._index = index
                self._docs = list(meta.get("docs", []))
                self._texts = [d.get("text", "") for d in self._docs]
                return len(self._texts) > 0
        except Exception:
            return False
        return False

    def _ensure_index(self) -> None:
        if self._index is not None:
            return
        # Try load from disk first
        if self._try_load_index():
            return
        # Else build
        docs, source_type = self._load_corpus()
        self._docs = docs
        self._texts = [doc["text"] for doc in docs]
        vectors = embed_texts(self._texts)
        dim = vectors.shape[1]
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(vectors)
        # Persist for reuse
        self._persist_index()

    def retrieve(self, sag: dict, language: str = "en") -> list[dict]:
        # Enhanced retrieval with multilingual support and provenance tracking
        start_time = time.time()
        self._ensure_index()
        query_text = (sag.get("raw") or "").strip()
        if not query_text:
            return []
        
        # Track input
        input_hash = hashlib.sha256(query_text.encode()).hexdigest()
        input_entry = provenance_tracker.track_input(
            source_id=f"query_{input_hash[:8]}",
            source_type=SourceType.TEXT,
            metadata={
                "query_text": query_text,
                "language": language,
                "sag_id": sag.get("analysis_id", "unknown")
            }
        )
        
        # TTL cache check with language key
        from ..core.config import get_settings
        settings = get_settings()
        ttl = settings.retrieval_cache["ttl_seconds"]
        now = time.time()
        cache_key = f"{query_text}_{language}"
        cached = self._cache.get(cache_key)
        if cached:
            ts, value = cached
            if now - ts <= ttl:
                # Track cache hit
                provenance_tracker.track_processing(
                    operation="cache_hit",
                    source_id=f"cache_{cache_key[:8]}",
                    parent_ids=[input_entry.id],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                return value
        
        # Use multilingual embeddings if language is not English
        if language != "en" and self.multilingual_embeddings.is_language_supported(language):
            qv = self.multilingual_embeddings.embed_texts([query_text], language)
            embedding_method = "multilingual"
        else:
            qv = embed_texts([query_text])
            embedding_method = "standard"
        
        # Track embedding generation
        embedding_entry = provenance_tracker.track_processing(
            operation=f"embedding_{embedding_method}",
            source_id=f"embed_{input_hash[:8]}",
            parameters={
                "method": embedding_method,
                "language": language,
                "text_length": len(query_text)
            },
            input_data_hash=input_hash,
            parent_ids=[input_entry.id],
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        scores, idxs = self._index.search(qv, k=min(3, len(self._texts)))
        results: list[dict] = []
        
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            doc = self._docs[idx] if 0 <= idx < len(self._docs) else None
            if doc is None:
                continue
            
            # Track each evidence item
            evidence_entry = provenance_tracker.track_evidence(
                evidence_id=doc["id"],
                source_url=doc["url"],
                confidence_score=float(score),
                metadata={
                    "title": doc["title"],
                    "text_length": len(doc["text"]),
                    "index_position": int(idx),
                    "language": language,
                    "multilingual_retrieval": language != "en"
                },
                parent_ids=[embedding_entry.id]
            )
            
            results.append({
                "id": doc["id"],
                "source": doc["url"],
                "title": doc["title"],
                "snippet": doc["text"],
                "score": float(score),
                "provenance_timestamp": datetime.utcnow().isoformat(),
                "source_type": "file" if self._corpus_path.exists() else "seed",
                "language": language,
                "multilingual_retrieval": language != "en",
                "provenance_id": evidence_entry.id
            })
        
        # Track retrieval completion
        retrieval_entry = provenance_tracker.track_processing(
            operation="retrieval_complete",
            source_id=f"retrieval_{input_hash[:8]}",
            parameters={
                "query_text": query_text,
                "language": language,
                "results_count": len(results),
                "embedding_method": embedding_method
            },
            parent_ids=[embedding_entry.id],
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        # Save to cache with size bound
        self._cache[cache_key] = (now, results)
        max_entries = settings.retrieval_cache["max_entries"]
        if len(self._cache) > max_entries:
            # Remove oldest
            oldest_key = min(self._cache.items(), key=lambda kv: kv[1][0])[0]
            self._cache.pop(oldest_key, None)
        
        return results


