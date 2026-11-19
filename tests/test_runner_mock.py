from pathlib import Path

from llm_redteam_kit.mock import MockModel
from llm_redteam_kit.pack import load_pack
from llm_redteam_kit.runner import run_pack

PACK_PATH = Path(__file__).resolve().parent.parent / "packs" / "core.jsonl"


def test_mock_run_covers_every_case():
    cases = load_pack(PACK_PATH)
    results = run_pack(cases, MockModel())
    assert len(results) == len(cases)
    assert [r.case_id for r in results] == [c.id for c in cases]


def test_mock_run_is_deterministic():
    cases = load_pack(PACK_PATH)
    first = [r.passed for r in run_pack(cases, MockModel())]
    second = [r.passed for r in run_pack(cases, MockModel())]
    assert first == second


def test_mock_run_produces_mixed_verdicts():
    # The mock model is intentionally imperfect: a healthy pipeline demo
    # should show both passes and fails, not a degenerate 0% or 100%.
    cases = load_pack(PACK_PATH)
    results = run_pack(cases, MockModel())
    verdicts = {r.passed for r in results}
    assert verdicts == {True, False}


def test_mock_model_refuses_dan_but_leaks_to_extraction():
    mock = MockModel()
    dan = [c for c in load_pack(PACK_PATH) if c.id == "jb-001"][0]
    leak = [c for c in load_pack(PACK_PATH) if c.id == "sp-002"][0]
    assert "DAN MODE ENABLED" not in mock(dan.prompt)
    assert "PROJECT-NIGHTINGALE" in mock(leak.prompt)


def test_runner_works_with_any_callable():
    cases = load_pack(PACK_PATH)
    results = run_pack(cases, lambda prompt: "I can't help with that.")
    assert all(r.passed for r in results)
