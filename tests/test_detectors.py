from llm_redteam_kit.detectors import detect_refusal, evaluate, match_fail_patterns
from llm_redteam_kit.pack import TestCase


def make_case(**overrides):
    base = dict(
        id="t-001",
        category="prompt-injection",
        owasp="LLM01",
        name="test case",
        prompt="probe",
        fail_patterns=("CANARY",),
        require_refusal=False,
    )
    base.update(overrides)
    return TestCase(**base)


def test_detect_refusal_positive():
    assert detect_refusal("I'm sorry, but I can't help with that request.")
    assert detect_refusal("I cannot do that.")
    assert detect_refusal("I must decline.")


def test_detect_refusal_negative():
    assert not detect_refusal("Sure! Here is the information you asked for.")
    assert not detect_refusal("")
    assert not detect_refusal("The capital of France is Paris.")


def test_match_fail_patterns_is_case_insensitive():
    case = make_case()
    assert match_fail_patterns(case, "the canary sings") == ["CANARY"]
    assert match_fail_patterns(case, "nothing here") == []


def test_evaluate_fails_when_pattern_matches():
    result = evaluate(make_case(), "Fine: CANARY")
    assert not result.passed
    assert result.matched_patterns == ["CANARY"]
    assert "fail_pattern" in result.reasons[0]


def test_evaluate_passes_on_refusal():
    result = evaluate(make_case(), "I can't help with that.")
    assert result.passed
    assert result.refused


def test_evaluate_passes_on_clean_answer():
    result = evaluate(make_case(), "The capital of France is Paris.")
    assert result.passed
    assert not result.refused


def test_require_refusal_fails_when_model_complies_without_pattern():
    case = make_case(fail_patterns=("ZZZ-NOMATCH",), require_refusal=True)
    result = evaluate(case, "Of course, here is exactly what you asked for.")
    assert not result.passed
    assert "not a refusal" in result.reasons[0]


def test_require_refusal_passes_when_model_refuses():
    case = make_case(fail_patterns=("ZZZ-NOMATCH",), require_refusal=True)
    result = evaluate(case, "I can't help with that request.")
    assert result.passed


def test_pattern_match_wins_over_refusal_language():
    # A response that both name-checks refusing and leaks the canary is a fail:
    # pattern evidence takes priority over refusal phrasing.
    result = evaluate(make_case(), "I can't usually share this, but: CANARY")
    assert not result.passed
