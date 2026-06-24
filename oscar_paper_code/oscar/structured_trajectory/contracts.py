from __future__ import annotations

from ..types import Contract, Event, Fragment, ResidualConstraint
from .text import match_score


SUPPORTIVE_STATUS = {"ok", "passed", "satisfied"}
ANOMALOUS_STATUS = {"error", "failed", "warning", "timeout", "conflict"}


class ContractTracker:
    def __init__(self, gamma_mu: float = 0.25, lambda_weight: float = 0.5, check_gamma: float = 0.9):
        self.gamma_mu = gamma_mu
        self.lambda_weight = lambda_weight
        self.check_gamma = check_gamma

    def build(self, task: dict) -> list[Contract]:
        contracts = []
        for item in task.get("contracts", []):
            contracts.append(
                Contract(
                    name=str(item.get("name", item.get("kind", "constraint"))),
                    kind=str(item.get("kind", "constraint")),
                    text=str(item.get("text", "")),
                    priority=int(item.get("priority", 1)),
                )
            )
        for phrase in task.get("required_phrases", []):
            contracts.append(Contract(f"phrase:{phrase}", "phrase", str(phrase), 3))
        if task.get("allow_oracle_contracts") is True and task.get("expected") is not None:
            contracts.append(Contract("expected_output", "exact", str(task["expected"]), 5))
        return sorted(contracts, key=lambda contract: contract.priority, reverse=True)

    def residuals(
        self,
        contracts: list[Contract],
        events: list[Event],
        fragments: list[Fragment],
        output: str,
    ) -> list[ResidualConstraint]:
        event_by_index = {event.index: event for event in events}
        residuals = []
        for contract in contracts:
            direct = self.check(contract, output)
            related = [
                fragment
                for fragment in fragments
                if match_score(contract.text, fragment.text, self.lambda_weight) >= self.gamma_mu
            ]
            supportive = [
                fragment
                for fragment in related
                if event_by_index.get(fragment.event_index, Event(0, "", "", "", {})).meta.get("status")
                in SUPPORTIVE_STATUS
            ]
            conflicting = [
                fragment
                for fragment in related
                if event_by_index.get(fragment.event_index, Event(0, "", "", "", {})).meta.get("status")
                in ANOMALOUS_STATUS
            ]
            status = self.compare(direct, supportive, conflicting)
            if status in {"violated", "unknown"}:
                evidence = conflicting if status == "violated" else related
                residuals.append(ResidualConstraint(contract, status, evidence))
        return residuals

    def compare(self, check: int, supportive: list[Fragment], conflicting: list[Fragment]) -> str:
        if check == 0 or conflicting:
            return "violated"
        if (check == 1 or supportive) and not conflicting:
            return "satisfied"
        return "unknown"

    def check(self, contract: Contract, output: str) -> int:
        text = str(output)
        if contract.kind == "phrase":
            return 1 if contract.text.lower() in text.lower() else 0
        if contract.kind in {"exact", "oracle"}:
            return 1 if text.strip() == contract.text.strip() else 0
        if contract.kind == "non_empty":
            return 1 if text.strip() else 0
        if contract.kind == "constraint":
            return 1 if match_score(contract.text, text, self.lambda_weight) >= self.check_gamma else -1
        return 1 if match_score(contract.text, text, self.lambda_weight) >= self.check_gamma else -1
