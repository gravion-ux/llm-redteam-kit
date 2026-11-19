import pytest

from llm_redteam_kit.detectors import CaseResult
from llm_redteam_kit.scoring import compare_to_baseline, gate_passes, summarize


def result(case_id, category, passed):
    return CaseResult(
        case_id=case_id,
        category=category,
        owasp="LLM01",
        name=case_id,
        prompt="probe",
        response="resp",
        passed=passed,
    )


@pytest.fixture
def results():
    return [
        result("a-1", "jailbreak", True),
        result("a-2", "jailbreak", False),
        result("b-1", "prompt-injection", True),
        result("b-2", "prompt-injection", True),
        result("b-3", "prompt-injection", False),
        result("b-4", "prompt-injection", True),
    ]


def test_summarize_totals(results):
    summary = summarize(results)
    assert summary.total == 6
    assert summary.passed == 4
    assert summary.failed == 2


def test_summarize_rates(results):
    summary = summarize(results)
    assert summary.pass_rate == pytest.approx(4 / 6)
    assert summary.attack_success_rate == pytest.approx(2 / 6)
    assert summary.pass_rate + summary.attack_success_rate == pytest.approx(1.0)


def test_summarize_category_breakdown(results):
    summary = summarize(results)
    jb = summary.categories["jailbreak"]
    assert (jb.total, jb.passed, jb.failed) == (2, 1, 1)
    assert jb.pass_rate == pytest.approx(0.5)
    pi = summary.categories["prompt-injection"]
    assert (pi.total, pi.passed) == (4, 3)


def test_summary_to_dict_is_serializable(results):
    data = summarize(results).to_dict()
    assert data["total"] == 6
    assert data["pass_rate"] == round(4 / 6, 4)
    assert data["categories"]["jailbreak"]["attack_success_rate"] == 0.5


def test_gate_passes_at_and_above_threshold(results):
    summary = summarize(results)
    assert gate_passes(summary, 0.5)
    assert gate_passes(summary, 4 / 6)
    assert not gate_passes(summary, 0.9)


def test_gate_rejects_out_of_range_threshold(results):
    with pytest.raises(ValueError):
        gate_passes(summarize(results), 1.5)


def test_compare_to_baseline(results):
    summary = summarize(results)
    assert compare_to_baseline(summary, {"pass_rate": 0.5}) == pytest.approx(round(4 / 6 - 0.5, 4))
    assert compare_to_baseline(summary, {"pass_rate": 0.9}) < 0


def test_summarize_empty_results():
    summary = summarize([])
    assert summary.total == 0
    assert summary.pass_rate == 0.0
