"""Test-pack loading and validation.

A test pack is a JSONL file: one JSON object per line. Each case must define:

    id             unique string id, e.g. "pi-001"
    category       one of CATEGORIES
    owasp          OWASP LLM Top 10 (2025) code, e.g. "LLM01"
    name           short human-readable name
    prompt         the probe sent to the model
    fail_patterns  list of regex strings; a match in the model response is
                   heuristic evidence the attack succeeded
    require_refusal (optional, default False) when True, a response that is
                   neither a refusal nor pattern-matching still fails,
                   because the only safe behaviour for that probe is refusal
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CATEGORIES = (
    "prompt-injection",
    "jailbreak",
    "system-prompt-extraction",
    "data-exfiltration",
)

OWASP_CODES = {f"LLM{i:02d}" for i in range(1, 11)}

REQUIRED_FIELDS = ("id", "category", "owasp", "name", "prompt", "fail_patterns")


class PackError(ValueError):
    """Raised when a test pack is malformed."""


@dataclass(frozen=True)
class TestCase:
    __test__ = False  # not a pytest test class, despite the name

    id: str
    category: str
    owasp: str
    name: str
    prompt: str
    fail_patterns: tuple = ()
    require_refusal: bool = False
    notes: str = field(default="")

    def compiled_patterns(self):
        return [re.compile(p, re.IGNORECASE) for p in self.fail_patterns]


def _validate_case(raw, line_no):
    if not isinstance(raw, dict):
        raise PackError(f"line {line_no}: case must be a JSON object")
    for name in REQUIRED_FIELDS:
        if name not in raw:
            raise PackError(f"line {line_no}: missing required field {name!r}")
    if raw["category"] not in CATEGORIES:
        raise PackError(
            f"line {line_no}: unknown category {raw['category']!r} "
            f"(expected one of {', '.join(CATEGORIES)})"
        )
    if raw["owasp"] not in OWASP_CODES:
        raise PackError(f"line {line_no}: invalid OWASP code {raw['owasp']!r}")
    if not isinstance(raw["prompt"], str) or not raw["prompt"].strip():
        raise PackError(f"line {line_no}: prompt must be a non-empty string")
    patterns = raw["fail_patterns"]
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        raise PackError(f"line {line_no}: fail_patterns must be a list of strings")
    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise PackError(f"line {line_no}: invalid regex {pattern!r}: {exc}") from exc
    return TestCase(
        id=str(raw["id"]),
        category=raw["category"],
        owasp=raw["owasp"],
        name=str(raw["name"]),
        prompt=raw["prompt"],
        fail_patterns=tuple(patterns),
        require_refusal=bool(raw.get("require_refusal", False)),
        notes=str(raw.get("notes", "")),
    )


def load_pack(path):
    """Load and validate a JSONL test pack. Returns a list of TestCase."""
    path = Path(path)
    cases = []
    seen_ids = set()
    with path.open(encoding="utf-8-sig") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PackError(f"line {line_no}: invalid JSON: {exc}") from exc
            case = _validate_case(raw, line_no)
            if case.id in seen_ids:
                raise PackError(f"line {line_no}: duplicate case id {case.id!r}")
            seen_ids.add(case.id)
            cases.append(case)
    if not cases:
        raise PackError(f"{path}: pack contains no cases")
    return cases
