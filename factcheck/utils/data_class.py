# ./factcheck/utils/data_class.pyS

from collections import Counter
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass


@dataclass
class TokenUsage:
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: Optional[int] = 0


@dataclass
class PipelineUsage:
    decomposer: TokenUsage = None
    checkworthy: TokenUsage = None
    query_generator: TokenUsage = None
    evidence_crawler: TokenUsage = None
    claimverify: TokenUsage = None


@dataclass
class Evidence:
    claim: str = None
    text: str = None  
    url: str = None
    reasoning: str = None
    relationship: str = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False
        return True


@dataclass
class ClaimDetail:

    id: int = None
    claim: str = None
    checkworthy: bool = None
    checkworthy_reason: str = None
    origin_text: str = None
    start: int = None
    end: int = None
    queries: List[str] = None
    evidences: List[dict] = None
    factuality: any = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False
        for evidence in self.evidences:
            if not evidence.attribute_check():
                print(f"Field {field.name} is None")
                return False
        return True


@dataclass
class FCSummary:
    num_claims: int = None
    num_checkworthy_claims: int = None
    num_verified_claims: int = None
    num_supported_claims: int = None
    num_refuted_claims: int = None
    num_controversial_claims: int = None
    factuality: float = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False
        return True


@dataclass
class FactCheckOutput:
    raw_text: str = None
    token_count: int = None
    usage: PipelineUsage = None
    claim_detail: List[ClaimDetail] = None
    summary: FCSummary = None
    final_report: str = None

    def attribute_check(self) -> bool:
        for field in self.__dataclass_fields__.values():
            if getattr(self, field.name) is None:
                print(f"Field {field.name} is None")
                return False

        for claim in self.claim_detail:
            if not claim.attribute_check():
                print(f"Field {field.name} is None")
                return False

        self.summary.attribute_check()

        return True
