#!/usr/bin/env python3
from __future__ import annotations

"""
Seed a few RDF-like nodes and edges into local Neo4j via GraphService driver.

This is a minimal helper for Epic 1.3.3.
"""

from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from backend.app.services.graph_service import GraphService


def main() -> None:
    service = GraphService()
    if not service.available():
        print("Neo4j driver not available. Ensure NEO4J_URL and credentials are configured.")
        return

    # Minimal sample: one claim with two evidence nodes
    claim: dict[str, Any] = {
        "id": "demo-claim-1",
        "text": "Vaccines are safe and effective.",
        "language": "en",
    }
    sag = {"nodes": [], "edges": []}
    evidence = [
        {"source": "https://example.org/study-1", "title": "Study 1", "score": 0.9, "provenance_timestamp": None},
        {"source": "https://who.int/report", "title": "WHO Report", "score": 0.85, "provenance_timestamp": None},
    ]

    service.store_analysis(claim, sag, evidence)
    print("Seeded demo RDF-like data into Neo4j.")


if __name__ == "__main__":
    main()
