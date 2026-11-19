import json
import re
from pathlib import Path

import pytest

from llm_redteam_kit.pack import CATEGORIES, OWASP_CODES, PackError, load_pack

PACK_PATH = Path(__file__).resolve().parent.parent / "packs" / "core.jsonl"


@pytest.fixture(scope="module")
def cases():
    return load_pack(PACK_PATH)


def test_pack_loads_and_is_substantial(cases):
    assert len(cases) >= 20


def test_case_ids_are_unique(cases):
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids))


def test_all_cases_have_required_content(cases):
    for case in cases:
        assert case.id
        assert case.name
        assert case.prompt.strip()
        assert case.fail_patterns, f"{case.id} has no fail patterns"


def test_categories_and_owasp_codes_are_valid(cases):
    for case in cases:
        assert case.category in CATEGORIES
        assert case.owasp in OWASP_CODES


def test_pack_covers_every_category(cases):
    present = {c.category for c in cases}
    assert present == set(CATEGORIES)


def test_fail_patterns_are_valid_regex(cases):
    for case in cases:
        for pattern in case.fail_patterns:
            re.compile(pattern)  # raises if invalid


def _write(tmp_path, text):
    path = tmp_path / "pack.jsonl"
    path.write_text(text, encoding="utf-8")
    return path


def _case_line(**overrides):
    case = {
        "id": "x-001",
        "category": "jailbreak",
        "owasp": "LLM01",
        "name": "example",
        "prompt": "do the thing",
        "fail_patterns": ["THING"],
    }
    case.update(overrides)
    return json.dumps(case)


def test_load_pack_rejects_missing_field(tmp_path):
    path = _write(tmp_path, json.dumps({"id": "x-001"}) + "\n")
    with pytest.raises(PackError):
        load_pack(path)


def test_load_pack_rejects_duplicate_ids(tmp_path):
    path = _write(tmp_path, _case_line() + "\n" + _case_line() + "\n")
    with pytest.raises(PackError):
        load_pack(path)


def test_load_pack_rejects_unknown_category(tmp_path):
    path = _write(tmp_path, _case_line(category="nonsense") + "\n")
    with pytest.raises(PackError):
        load_pack(path)


def test_load_pack_rejects_invalid_regex(tmp_path):
    path = _write(tmp_path, _case_line(fail_patterns=["(["]) + "\n")
    with pytest.raises(PackError):
        load_pack(path)


def test_load_pack_skips_blank_lines_and_comments(tmp_path):
    path = _write(tmp_path, "# comment\n\n" + _case_line() + "\n")
    assert len(load_pack(path)) == 1
