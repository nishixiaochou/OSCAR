from __future__ import annotations

from .candidate_gating import CandidateGenerator, ReliabilityGate
from .reconstruction_attribution import ReasoningReconstructor
from .risk_evidence import RiskLocalizer
from .structured_trajectory import ContractTracker, TrajectoryBuilder
from .types import OscarResult


class Oscar:
    def __init__(self, enhancement_budget: int = 1):
        self.enhancement_budget = enhancement_budget
        self.trajectory = TrajectoryBuilder()
        self.contracts = ContractTracker()
        self.reconstructor = ReasoningReconstructor()
        self.risk = RiskLocalizer()
        self.candidates = CandidateGenerator()
        self.gate = ReliabilityGate(self.contracts)

    def run(self, task: dict) -> OscarResult:
        events = self.trajectory.build_events(task)
        fragments = self.trajectory.build_fragments(events)
        original = str(task.get("candidate_answer", task.get("base_answer", task.get("answer", ""))))
        contracts = self.contracts.build(task)
        residuals_before = self.contracts.residuals(contracts, events, fragments, original)
        reconstruction = self.reconstructor.reconstruct(events, fragments, task)
        package = self.risk.package(residuals_before, events, fragments, reconstruction)
        candidates = self.candidates.generate(task, original, package, self.enhancement_budget)
        before, selected, accepted = self.gate.select(task, original, candidates, contracts, events, fragments)
        return OscarResult(
            task_id=str(task.get("id", "")),
            original_output=original,
            output=selected.output,
            accepted=accepted,
            verification_gain=max(0.0, selected.score - before.score),
            residuals_before=before.residuals,
            residuals_after=selected.residuals,
            reconstruction=reconstruction,
            evidence_package=package,
            candidates=candidates,
            selected_candidate=selected.output,
            typed_trace_coverage=self.trajectory.coverage(events),
        )
