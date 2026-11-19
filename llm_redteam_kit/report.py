"""Report generation: build a report dict, render Markdown, write files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .scoring import summarize


def build_report(results, model_label, pack_name):
    """Assemble the full report dict from a list of CaseResult."""
    summary = summarize(results)
    return {
        "tool": "llm-redteam-kit",
        "tool_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model_label,
        "pack": pack_name,
        "summary": summary.to_dict(),
        "results": [r.to_dict() for r in results],
    }


def _pct(value):
    return f"{value * 100:.1f}%"


def to_markdown(report):
    summary = report["summary"]
    lines = [
        "# LLM Red Team Report",
        "",
        f"- **Model / endpoint:** {report['model']}",
        f"- **Test pack:** {report['pack']}",
        f"- **Generated:** {report['generated_at']}",
        f"- **Tool:** llm-redteam-kit {report['tool_version']}",
        "",
        "## Summary",
        "",
        f"- Cases run: **{summary['total']}**",
        f"- Passed: **{summary['passed']}**",
        f"- Failed: **{summary['failed']}**",
        f"- Pass rate: **{_pct(summary['pass_rate'])}**",
        f"- Attack success rate: **{_pct(summary['attack_success_rate'])}** "
        "(share of probes that succeeded against the model; lower is better)",
        "",
        "## Results by category",
        "",
        "| Category | Total | Passed | Failed | Pass rate | Attack success rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, cat in summary["categories"].items():
        lines.append(
            f"| {name} | {cat['total']} | {cat['passed']} | {cat['failed']} "
            f"| {_pct(cat['pass_rate'])} | {_pct(cat['attack_success_rate'])} |"
        )
    lines += [
        "",
        "## Per-case results",
        "",
        "| ID | OWASP | Category | Verdict | Why |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in report["results"]:
        verdict = "PASS" if result["passed"] else "**FAIL**"
        why = "; ".join(result["reasons"]).replace("|", "\\|")
        lines.append(
            f"| {result['id']} | {result['owasp']} | {result['category']} "
            f"| {verdict} | {why} |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "Verdicts come from heuristic detectors (refusal and pattern matching) "
        "and are a triage signal, not ground truth. Manually review every FAIL "
        "row — and spot-check PASS rows — before drawing conclusions about a "
        "model. Only run this toolkit against models you own or are authorized "
        "to evaluate.",
        "",
    ]
    return "\n".join(lines)


def write_reports(report, out_dir):
    """Write report.json and report.md into out_dir. Returns (json, md) paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(to_markdown(report), encoding="utf-8")
    return json_path, md_path
