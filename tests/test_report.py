import json
from pathlib import Path

from llm_redteam_kit.mock import MockModel
from llm_redteam_kit.pack import load_pack
from llm_redteam_kit.report import build_report, to_markdown, write_reports
from llm_redteam_kit.runner import run_pack

PACK_PATH = Path(__file__).resolve().parent.parent / "packs" / "core.jsonl"


def _report():
    cases = load_pack(PACK_PATH)
    results = run_pack(cases, MockModel())
    return build_report(results, "mock-model (offline)", "packs/core.jsonl")


def test_build_report_structure():
    report = _report()
    for key in ("tool", "tool_version", "generated_at", "model", "pack", "summary", "results"):
        assert key in report
    assert report["summary"]["total"] == len(report["results"])
    first = report["results"][0]
    for key in ("id", "category", "owasp", "passed", "matched_patterns", "reasons"):
        assert key in first


def test_markdown_contains_headline_metrics():
    md = to_markdown(_report())
    assert "# LLM Red Team Report" in md
    assert "Attack success rate" in md
    assert "Results by category" in md
    assert "prompt-injection" in md
    assert "system-prompt-extraction" in md


def test_markdown_lists_every_case():
    report = _report()
    md = to_markdown(report)
    for result in report["results"]:
        assert result["id"] in md


def test_write_reports_creates_json_and_markdown(tmp_path):
    report = _report()
    json_path, md_path = write_reports(report, tmp_path / "out")
    assert json_path.exists() and md_path.exists()
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["summary"] == report["summary"]
    assert md_path.read_text(encoding="utf-8").startswith("# LLM Red Team Report")
