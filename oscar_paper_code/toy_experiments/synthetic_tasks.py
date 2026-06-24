from __future__ import annotations


def load_synthetic_tasks() -> list[dict]:
    return [
        {
            "id": "toy_phrase_repair",
            "prompt": "Return a short answer that includes stable API.",
            "base_answer": "The answer mentions API behavior.",
            "candidate_outputs": [
                {"output": "The answer preserves stable API behavior.", "scope": "local"}
            ],
            "expected": "The answer preserves stable API behavior.",
            "required_phrases": ["stable API"],
            "contracts": [
                {
                    "name": "required_phrase",
                    "kind": "phrase",
                    "text": "stable API",
                    "priority": 5,
                }
            ],
            "events": [
                {
                    "index": 1,
                    "actor": "user",
                    "type": "message",
                    "content": "Return a short answer that includes stable API.",
                    "meta": {"source": "prompt", "status": "ok"},
                },
                {
                    "index": 2,
                    "actor": "agent",
                    "type": "message",
                    "content": "The answer mentions API behavior.",
                    "meta": {"source": "agent", "status": "warning"},
                },
            ],
            "reconstructed_paths": [
                {
                    "transition": [1, 2],
                    "steps": ["The output preserved API but omitted stable."],
                }
            ],
        },
        {
            "id": "toy_keep_original",
            "prompt": "Return done.",
            "base_answer": "done",
            "expected": "done",
            "required_phrases": ["done"],
            "contracts": [
                {
                    "name": "done",
                    "kind": "phrase",
                    "text": "done",
                    "priority": 3,
                }
            ],
            "events": [
                {
                    "index": 1,
                    "actor": "user",
                    "type": "message",
                    "content": "Return done.",
                    "meta": {"source": "prompt", "status": "ok"},
                }
            ],
        },
    ]
