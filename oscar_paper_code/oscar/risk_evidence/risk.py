from __future__ import annotations

from ..structured_trajectory.contracts import ANOMALOUS_STATUS
from ..structured_trajectory.text import match_score
from ..types import EvidencePackage, Event, Fragment, ReconstructionResult, ResidualConstraint, RiskSource


STATUS_PRIORITY = {
    "failed": 5.0,
    "error": 5.0,
    "conflict": 4.5,
    "timeout": 4.0,
    "warning": 3.0,
}


class RiskLocalizer:
    def __init__(
        self,
        gamma_u: float = 0.2,
        top_fragments: int = 5,
        top_risks: int = 8,
        lambda_weight: float = 0.5,
    ):
        self.gamma_u = gamma_u
        self.top_fragments = top_fragments
        self.top_risks = top_risks
        self.lambda_weight = lambda_weight

    def package(
        self,
        residuals: list[ResidualConstraint],
        events: list[Event],
        fragments: list[Fragment],
        reconstruction: ReconstructionResult,
    ) -> EvidencePackage:
        event_by_index = {event.index: event for event in events}
        related = self._related_fragments(fragments, reconstruction.steps)
        residual_risks = [
            RiskSource(
                "residual_constraint",
                residual.contract.priority,
                residual.contract.text,
                None,
                {"status": residual.status},
            )
            for residual in residuals
        ]
        risks = []
        for fragment in related:
            status = event_by_index.get(fragment.event_index, Event(0, "", "", "", {})).meta.get("status")
            if status in ANOMALOUS_STATUS:
                risks.append(
                    RiskSource(
                        "anomalous_fragment",
                        STATUS_PRIORITY.get(status, 1.0),
                        fragment.text,
                        fragment.event_index,
                        {"status": status},
                    )
                )
        for step in reconstruction.steps:
            score = self._anomalous_score(step, related, event_by_index)
            if score >= self.gamma_u:
                risks.append(RiskSource("suspicious_step", score, step, None, {}))
        risks = [risk for _, risk in sorted(enumerate(risks), key=lambda item: (-item[1].priority, item[0]))]
        return EvidencePackage(residuals, (residual_risks + risks)[: self.top_risks])

    def _related_fragments(self, fragments: list[Fragment], steps: list[str]) -> list[Fragment]:
        if not steps:
            return []
        rows = []
        for fragment in fragments:
            score = max(match_score(step, fragment.text, self.lambda_weight) for step in steps)
            if score > 0:
                rows.append((score, fragment))
        rows.sort(key=lambda item: (-item[0], item[1].event_index, item[1].fragment_index))
        return [fragment for _, fragment in rows[: self.top_fragments]]

    def _anomalous_score(self, step: str, fragments: list[Fragment], event_by_index: dict[int, Event]) -> float:
        score = 0.0
        for fragment in fragments:
            event = event_by_index.get(fragment.event_index)
            if event and event.meta.get("status") in ANOMALOUS_STATUS:
                score = max(score, match_score(step, fragment.text, self.lambda_weight))
        return score
