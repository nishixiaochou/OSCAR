from __future__ import annotations

import math
import json
import re
import string
from typing import Any, Iterable

from ..types import Fragment


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def serialize_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def terms(value: Any) -> set[str]:
    text = serialize_content(value).lower()
    table = str.maketrans({char: " " for char in string.punctuation})
    words = text.translate(table).split()
    return {word for word in words if word and word not in STOPWORDS}


def term_vector(value: Any) -> dict[str, float]:
    vector = {}
    for word in terms(value):
        vector[word] = vector.get(word, 0.0) + 1.0
    return vector


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 0.0
    dot = sum(left.get(key, 0.0) * right.get(key, 0.0) for key in keys)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def split_fragments(event_index: int, content: Any) -> list[Fragment]:
    if isinstance(content, dict):
        fragments = []
        for index, key in enumerate(sorted(content), start=1):
            text = serialize_content(content[key])
            fragments.append(Fragment(event_index, index, str(key), text))
        return fragments
    text = serialize_content(content)
    pieces = []
    for match in re.finditer(r"[^.!?\n]+[.!?\n]*", text):
        piece = match.group(0).strip()
        if piece:
            pieces.append((match.start(), match.end(), piece))
    if not pieces and text:
        pieces.append((0, len(text), text))
    return [
        Fragment(event_index, index, (begin, end), piece)
        for index, (begin, end, piece) in enumerate(pieces, start=1)
    ]


def match_score(left: Any, right: Any, lambda_weight: float = 0.5) -> float:
    left_terms = terms(left)
    right_terms = terms(right)
    if not left_terms:
        return 0.0
    lexical = len(left_terms & right_terms) / max(1, len(left_terms))
    semantic = (1.0 + cosine(term_vector(left), term_vector(right))) / 2.0
    return lambda_weight * lexical + (1.0 - lambda_weight) * semantic


def support_score(path_values: Iterable[Any], fragments: Iterable[Fragment]) -> float:
    path_terms = merged_terms(path_values)
    support_terms = merged_terms(fragment.text for fragment in fragments)
    if not path_terms:
        return 0.0
    return len(path_terms & support_terms) / max(1, len(path_terms))


def merged_terms(values: Iterable[Any]) -> set[str]:
    output = set()
    for value in values:
        output |= terms(value)
    return output
