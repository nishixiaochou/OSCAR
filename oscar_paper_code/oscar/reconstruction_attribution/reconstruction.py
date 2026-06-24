from __future__ import annotations

from ..structured_trajectory.text import support_score, terms
from ..types import CandidatePath, Event, Fragment, ReconstructionResult


class ReasoningReconstructor:
    def __init__(
        self,
        gamma_s: float = 0.2,
        gamma_alpha: float = 0.05,
        gamma_m: float = 0.05,
        epsilon: float = 1e-8,
        top_steps: int = 3,
    ):
        self.gamma_s = gamma_s
        self.gamma_alpha = gamma_alpha
        self.gamma_m = gamma_m
        self.epsilon = epsilon
        self.top_steps = top_steps

    def reconstruct(
        self,
        events: list[Event],
        fragments: list[Fragment],
        task: dict | None = None,
    ) -> ReconstructionResult:
        task = task or {}
        candidates = self._candidate_specs(events, task)
        supported = []
        for left, right, steps in candidates:
            local = [fragment for fragment in fragments if fragment.event_index in {left.index, right.index}]
            output = right.content
            values = steps + [output]
            support = support_score(values, local)
            attribution = self._attribution(values, local)
            quality = sum(value for value in attribution.values() if value >= self.gamma_alpha)
            if support >= self.gamma_s and quality >= self.gamma_m:
                supported.append(CandidatePath((left.index, right.index), steps, output, support, attribution, quality))
        ranked_steps = self._prune_steps(supported, fragments)
        evidence_sources = {}
        for path in supported:
            for key, value in path.attribution.items():
                if value > 0:
                    evidence_sources.setdefault(str(path.transition), []).append(key)
        return ReconstructionResult(supported, ranked_steps, evidence_sources)

    def _candidate_specs(self, events: list[Event], task: dict) -> list[tuple[Event, Event, list[str]]]:
        explicit = []
        event_by_index = {event.index: event for event in events}
        for item in task.get("reconstructed_paths", []):
            transition = item.get("transition", [])
            if len(transition) != 2:
                continue
            left = event_by_index.get(int(transition[0]))
            right = event_by_index.get(int(transition[1]))
            if left and right:
                explicit.append((left, right, [str(step) for step in item.get("steps", [])]))
        if explicit:
            return explicit
        generated = []
        for left, right in zip(events, events[1:]):
            shared = sorted(terms(left.content) & terms(right.content))
            if shared:
                generated.append((left, right, [f"carry {' '.join(shared[:4])}"]))
        return generated

    def _attribution(self, values: list[str], fragments: list[Fragment]) -> dict[str, float]:
        base = support_score(values, fragments)
        deltas = {}
        for fragment in fragments:
            masked = [item for item in fragments if item != fragment]
            key = f"{fragment.event_index}:{fragment.fragment_index}"
            deltas[key] = max(0.0, base - support_score(values, masked))
        total = sum(deltas.values()) + self.epsilon
        return {key: value / total for key, value in deltas.items()}

    def _prune_steps(self, paths: list[CandidatePath], fragments: list[Fragment]) -> list[str]:
        rows = []
        fragment_by_key = {f"{fragment.event_index}:{fragment.fragment_index}": fragment for fragment in fragments}
        for path in paths:
            for step in path.steps:
                omega = 0.0
                for key, alpha in path.attribution.items():
                    fragment = fragment_by_key.get(key)
                    if fragment and terms(step) & terms(fragment.text):
                        omega = max(omega, alpha)
                if omega > 0:
                    rows.append((omega, step))
        rows.sort(key=lambda item: (-item[0], item[1]))
        return [step for _, step in rows[: self.top_steps]]
