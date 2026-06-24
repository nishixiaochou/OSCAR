from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from baselines.registry import BASELINE_SOURCES
from oscar import Oscar
from .synthetic_tasks import load_synthetic_tasks


def score_output(task: dict, output: str) -> float:
    expected = task.get("expected")
    if expected is not None and str(output).strip() == str(expected).strip():
        return 1.0
    phrases = task.get("required_phrases", [])
    if not phrases:
        return 1.0 if str(output).strip() else 0.0
    return sum(str(phrase).lower() in str(output).lower() for phrase in phrases) / max(1, len(phrases))


def baseline_output(task: dict, name: str) -> str:
    if name == "prompt_only_refinement":
        candidates = task.get("candidate_outputs", [])
        if candidates:
            first = candidates[0]
            if isinstance(first, dict):
                return str(first.get("output", first.get("answer", task.get("base_answer", ""))))
            return str(first)
    return str(task.get("base_answer", task.get("answer", "")))


def summarize(rows: list[dict]) -> dict[str, dict]:
    methods = sorted({row["method"] for row in rows})
    summary = {}
    for method in methods:
        selected = [row for row in rows if row["method"] == method]
        summary[method] = {
            "task_count": len(selected),
            "success_rate": mean(row["success"] for row in selected),
            "accepted_count": sum(row.get("accepted", False) for row in selected),
            "avg_verification_gain": mean(row.get("verification_gain", 0.0) for row in selected),
            "avg_risk_count": mean(row.get("risk_count", 0) for row in selected),
            "avg_reconstructed_steps": mean(row.get("reconstructed_steps", 0) for row in selected),
        }
    return summary


def run_toy_experiment() -> dict:
    tasks = load_synthetic_tasks()
    rows = []
    baseline_names = [source.name for source in BASELINE_SOURCES]
    for task in tasks:
        for name in baseline_names:
            output = baseline_output(task, name)
            rows.append(
                {
                    "task_id": task["id"],
                    "method": name,
                    "output": output,
                    "success": score_output(task, output),
                    "accepted": False,
                    "verification_gain": 0.0,
                    "risk_count": 0,
                    "reconstructed_steps": 0,
                }
            )
        result = Oscar(enhancement_budget=1).run(task)
        rows.append(
            {
                "task_id": task["id"],
                "method": "oscar",
                "output": result.output,
                "success": score_output(task, result.output),
                "accepted": result.accepted,
                "verification_gain": result.verification_gain,
                "risk_count": len(result.evidence_package.risks),
                "reconstructed_steps": len(result.reconstruction.steps),
            }
        )
    return {"dataset": "synthetic_toy", "rows": rows, "methods": summarize(rows)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_toy_experiment()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
