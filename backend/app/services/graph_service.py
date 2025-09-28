from __future__ import annotations

from typing import Any

from ..core.graph import get_neo4j_driver


class GraphService:
    def __init__(self) -> None:
        self.driver = get_neo4j_driver()

    def available(self) -> bool:
        return self.driver is not None

    def store_analysis(self, claim: dict[str, Any], sag: dict[str, Any], evidence: list[dict]) -> None:
        if not self.driver:
            return
        try:
            with self.driver.session() as session:
                session.execute_write(self._write_analysis, claim, sag, evidence)
        except Exception:
            # best-effort only
            return

    @staticmethod
    def _write_analysis(tx, claim: dict[str, Any], sag: dict[str, Any], evidence: list[dict]) -> None:
        tx.run(
            "MERGE (c:Claim {id: $id}) SET c.text=$text, c.language=$language",
            id=claim.get("id") or "unknown",
            text=claim.get("text") or "",
            language=claim.get("language") or "en",
        )
        for i, ev in enumerate(evidence):
            tx.run(
                "MERGE (e:Evidence {source: $source}) SET e.title=$title, e.score=$score, e.provenance_timestamp=$ts",
                source=ev.get("source"),
                title=ev.get("title"),
                score=float(ev.get("score", 0.0)),
                ts=ev.get("provenance_timestamp"),
            )
            tx.run(
                "MATCH (c:Claim {id: $cid}),(e:Evidence {source: $source}) MERGE (c)-[:SUPPORTED_BY]->(e)",
                cid=claim.get("id") or "unknown",
                source=ev.get("source"),
            )



