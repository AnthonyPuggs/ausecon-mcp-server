from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_MANIFEST = Path(__file__).resolve().parent / "questions.yaml"

_ANSWER_TYPES = {"pinned", "live"}
_SOURCES = {"abs", "rba", "apra", "derived"}
_RESOLVER_KINDS = {"economic", "derived"}


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    question: str
    answer_type: str
    category: str
    source: str
    tolerance: float
    unit: str
    note: str
    expected_value: float | None = None
    expected_period: str | None = None
    resolver: dict | None = None


def load_questions(path: Path = DEFAULT_MANIFEST) -> list[EvalQuestion]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("questions.yaml must be a non-empty list")

    questions: list[EvalQuestion] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"entry {index} is not a mapping")
        try:
            question = EvalQuestion(**item)
        except TypeError as exc:
            raise ValueError(f"entry {index} has bad fields: {exc}") from exc

        if question.id in seen:
            raise ValueError(f"duplicate question id {question.id!r}")
        seen.add(question.id)

        if question.answer_type not in _ANSWER_TYPES:
            raise ValueError(f"{question.id}: answer_type must be one of {sorted(_ANSWER_TYPES)}")
        if question.source not in _SOURCES:
            raise ValueError(f"{question.id}: source must be one of {sorted(_SOURCES)}")
        if question.tolerance < 0:
            raise ValueError(f"{question.id}: tolerance must be >= 0")
        if not question.question.strip() or not question.note.strip():
            raise ValueError(f"{question.id}: question and note must be non-empty")

        if question.answer_type == "pinned":
            if question.expected_value is None or not question.expected_period:
                raise ValueError(f"{question.id}: pinned entries need expected_value and period")
        else:
            resolver = question.resolver
            if not isinstance(resolver, dict):
                raise ValueError(f"{question.id}: live entries need a resolver mapping")
            if resolver.get("kind") not in _RESOLVER_KINDS:
                raise ValueError(f"{question.id}: resolver.kind must be economic or derived")
            if not resolver.get("concept"):
                raise ValueError(f"{question.id}: resolver.concept is required")

        questions.append(question)
    return questions
