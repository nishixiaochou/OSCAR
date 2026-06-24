from __future__ import annotations

from ..structured_trajectory.contracts import ContractTracker
from ..types import Contract, Event, Fragment, VerificationResult


class ReliabilityGate:
    def __init__(self, tracker: ContractTracker):
        self.tracker = tracker

    def evaluate(
        self,
        task: dict,
        output: str,
        contracts: list[Contract],
        events: list[Event],
        fragments: list[Fragment],
    ) -> VerificationResult:
        checks = self.functional_checks(task, output, contracts)
        hard_checks = self.hard_checks(output, contracts)
        residuals = self.tracker.residuals(contracts, events, fragments, output)
        passed = all(hard_checks.values()) if hard_checks else True
        score = sum(1 for value in checks.values() if value) / max(1, len(checks))
        return VerificationResult(output, passed, score, residuals, checks)

    def functional_checks(self, task: dict, output: str, contracts: list[Contract]) -> dict[str, bool]:
        checks = {"non_empty": bool(str(output).strip())}
        expected = task.get("expected")
        if expected is not None:
            checks["expected"] = str(output).strip() == str(expected).strip()
        for phrase in task.get("required_phrases", []):
            checks[f"phrase:{phrase}"] = str(phrase).lower() in str(output).lower()
        for contract in contracts:
            if contract.kind in {"phrase", "exact", "non_empty"}:
                checks[f"contract:{contract.name}"] = self.tracker.check(contract, output) == 1
        return checks

    def hard_checks(self, output: str, contracts: list[Contract]) -> dict[str, bool]:
        checks = {"non_empty": bool(str(output).strip())}
        for contract in contracts:
            if contract.kind in {"phrase", "exact", "non_empty"}:
                checks[f"hard:{contract.name}"] = self.tracker.check(contract, output) == 1
        return checks

    def select(
        self,
        task: dict,
        original: str,
        candidates: list[str],
        contracts: list[Contract],
        events: list[Event],
        fragments: list[Fragment],
    ) -> tuple[VerificationResult, VerificationResult, bool]:
        before = self.evaluate(task, original, contracts, events, fragments)
        best = before
        accepted = False
        for candidate in candidates:
            current = self.evaluate(task, candidate, contracts, events, fragments)
            allowed = (
                current.passed
                and current.score >= before.score
                and len(current.residuals) <= len(before.residuals)
            )
            gain = current.score - before.score
            best_gain = best.score - before.score
            if allowed and (gain > best_gain or (gain == best_gain and candidate != original and not accepted)):
                best = current
                accepted = candidate != original
        return before, best, accepted
