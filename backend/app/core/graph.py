from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:
    from neo4j import GraphDatabase, Driver
except Exception:  # pragma: no cover - optional dep
    GraphDatabase = None  # type: ignore
    Driver = None  # type: ignore


@lru_cache(maxsize=1)
def get_neo4j_driver() -> Optional["Driver"]:  # type: ignore[name-defined]
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not uri or not user or not password:
        return None
    if GraphDatabase is None:
        return None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        return driver
    except Exception:
        return None



