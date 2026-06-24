# OSCAR Paper Code

This folder contains a paper-aligned implementation scaffold for OSCAR, and a synthetic toy experiment.

## Method Implementation

`oscar/structured_trajectory` implements the paper's typed trajectory, observable support fragments, `Match`, constraint comparison function, and residual constraint set.

`oscar/reconstruction_attribution` implements adjacent-transition reconstructed paths, local observable support, masking deltas, normalized attribution weights, supported path filtering, and top-`B_R` step pruning.

`oscar/risk_evidence` implements top-`B_O` related observations, anomalous association scores, anomalous observation risks, suspicious reconstructed-step risks, top-`B_G` bounded risk selection, and the evidence package.

`oscar/candidate_gating` implements risk hints, intervention inputs, budgeted retry candidates, deterministic verification score, hard checks, non-degradation acceptance, and final candidate selection.

`oscar/pipeline.py` connects the four modules through `Oscar.run(task)`.

## Task Schema

The minimal task input is a Python dictionary:

```python
task = {
    "id": "example",
    "prompt": "Return a short answer.",
    "base_answer": "previous answer",
    "events": [
        {
            "index": 1,
            "actor": "user",
            "type": "message",
            "content": "Return a short answer.",
            "meta": {"source": "prompt", "status": "ok"},
        }
    ],
    "contracts": [
        {"name": "non_empty", "kind": "non_empty", "text": "non-empty answer", "priority": 1}
    ],
    "candidate_outputs": [{"output": "candidate answer", "scope": "local"}],
}
```

Optional fields include `required_phrases`, `expected`, `allow_oracle_contracts`, `patch_candidates`, and `reconstructed_paths`.

## Basic Usage

Run OSCAR directly from Python:

```bash
PYTHONPATH=/oscar_paper_code python3 - <<'PY'
from oscar import Oscar
from toy_experiments.synthetic_tasks import load_synthetic_tasks

task = load_synthetic_tasks()[0]
result = Oscar(enhancement_budget=1).run(task)
print(result.output)
print(result.accepted)
print(result.verification_gain)
PY
```

Run the synthetic toy experiment:

```bash
PYTHONPATH=/oscar_paper_code python3 -m toy_experiments.toy_experiment
```

Write the synthetic toy experiment output to JSON:

```bash
PYTHONPATH=/oscar_paper_code python3 -m toy_experiments.toy_experiment --output /tmp/oscar_toy_result.json
```

Run the current unit tests:

```bash
PYTHONPATH=/oscar_paper_code python3 -m unittest tests.test_oscar_toy_experiment
```

## Boundary

The synthetic toy experiment is not a real benchmark. It does not connect to real datasets, model providers, external APIs, official benchmark runners, or official baseline repositories.

Do not report toy experiment output as paper benchmark evidence.
