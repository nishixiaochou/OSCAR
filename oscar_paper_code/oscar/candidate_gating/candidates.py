from __future__ import annotations

from ..structured_trajectory.contracts import ANOMALOUS_STATUS
from ..types import EvidencePackage, RiskSource


class CandidateGenerator:
    def __init__(self, top_hints: int = 8):
        self.top_hints = top_hints

    def generate(self, task: dict, original_output: str, package: EvidencePackage, budget: int) -> list[str]:
        if budget <= 0 or not package.risks:
            return [original_output]
        interventions = self.interventions(task, original_output, package)
        outputs = [original_output]
        for item in self.retry(task, interventions, budget):
            if isinstance(item, dict):
                if self._blocked_global_rewrite(item, package):
                    continue
                value = str(item.get("output", item.get("answer", "")))
            else:
                value = str(item)
            if value and value not in outputs:
                outputs.append(value)
            if len(outputs) - 1 >= budget:
                break
        return outputs

    def hints(self, package: EvidencePackage) -> list[str]:
        return [self.hint(risk) for risk in self.top_risks(package)]

    def top_risks(self, package: EvidencePackage) -> list[RiskSource]:
        rows = []
        for index, risk in enumerate(package.risks):
            rows.append((risk.priority, index, risk))
        rows.sort(key=lambda item: (-item[0], item[1]))
        return [risk for _, _, risk in rows[: self.top_hints]]

    def hint(self, risk: RiskSource) -> str:
        if risk.kind == "residual_constraint":
            return f"preserve residual constraint: {risk.text}"
        if risk.kind == "anomalous_fragment":
            return f"handle anomalous observation: {risk.text}"
        if risk.kind == "suspicious_step":
            return f"correct suspicious transition step: {risk.text}"
        return f"revise local risk: {risk.text}"

    def interventions(self, task: dict, original_output: str, package: EvidencePackage) -> list[dict]:
        prompt = str(task.get("prompt", ""))
        residuals = [residual.contract.text for residual in package.residuals]
        rows = []
        for risk in self.top_risks(package):
            rows.append(
                {
                    "x": prompt,
                    "y0": original_output,
                    "residuals": residuals,
                    "risk": risk,
                    "hint": self.hint(risk),
                }
            )
        return rows

    def retry(self, task: dict, interventions: list[dict], budget: int) -> list[dict | str]:
        items = list(task.get("candidate_outputs", [])) + list(task.get("patch_candidates", []))
        return items[: min(budget, len(interventions), len(items))]

    def _blocked_global_rewrite(self, item: dict, package: EvidencePackage) -> bool:
        statuses = {risk.meta.get("status") for risk in package.risks}
        return item.get("scope") == "global" and bool(statuses & ANOMALOUS_STATUS)
