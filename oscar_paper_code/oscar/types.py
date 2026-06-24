from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Event:
    index: int
    actor: str
    type: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Fragment:
    event_index: int
    fragment_index: int
    span: tuple[int, int] | str
    text: str


@dataclass(frozen=True)
class Contract:
    name: str
    kind: str
    text: str
    priority: int = 1


@dataclass(frozen=True)
class ResidualConstraint:
    contract: Contract
    status: str
    evidence: list[Fragment] = field(default_factory=list)


@dataclass(frozen=True)
class CandidatePath:
    transition: tuple[int, int]
    steps: list[str]
    output: str
    support_score: float
    attribution: dict[str, float]
    quality_score: float


@dataclass(frozen=True)
class ReconstructionResult:
    supported_paths: list[CandidatePath]
    steps: list[str]
    evidence_sources: dict[str, list[str]]


@dataclass(frozen=True)
class RiskSource:
    kind: str
    priority: float
    text: str
    event_index: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidencePackage:
    residuals: list[ResidualConstraint]
    risks: list[RiskSource]


@dataclass(frozen=True)
class VerificationResult:
    output: str
    passed: bool
    score: float
    residuals: list[ResidualConstraint]
    checks: dict[str, bool]


@dataclass(frozen=True)
class OscarResult:
    task_id: str
    original_output: str
    output: str
    accepted: bool
    verification_gain: float
    residuals_before: list[ResidualConstraint]
    residuals_after: list[ResidualConstraint]
    reconstruction: ReconstructionResult
    evidence_package: EvidencePackage
    candidates: list[str]
    selected_candidate: str
    typed_trace_coverage: float

