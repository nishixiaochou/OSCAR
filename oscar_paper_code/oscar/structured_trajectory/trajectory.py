from __future__ import annotations

from ..types import Event, Fragment
from .text import serialize_content, split_fragments


class TrajectoryBuilder:
    def build_events(self, task: dict) -> list[Event]:
        events = []
        for position, item in enumerate(task.get("events", []), start=1):
            events.append(
                Event(
                    index=int(item.get("index", item.get("step", position))),
                    actor=str(item.get("actor", "agent")),
                    type=str(item.get("type", item.get("kind", "message"))),
                    content=serialize_content(item.get("content", "")),
                    meta=dict(item.get("meta", {})),
                )
            )
        if events:
            return events
        return [
            Event(
                index=1,
                actor="user",
                type="message",
                content=serialize_content(task.get("prompt", "")),
                meta={"source": "prompt", "observability": "low"},
            )
        ]

    def build_fragments(self, events: list[Event]) -> list[Fragment]:
        fragments = []
        for event in events:
            fragments.extend(split_fragments(event.index, event.content))
        return fragments

    def coverage(self, events: list[Event]) -> float:
        if not events:
            return 0.0
        valid = sum(
            1
            for event in events
            if event.index is not None
            and event.actor
            and event.type
            and isinstance(event.content, str)
            and isinstance(event.meta, dict)
        )
        return valid / len(events)

