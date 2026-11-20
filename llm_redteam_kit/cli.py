"""Command line interface.

Usage:
    python -m llm_redteam_kit run --mock
    python -m llm_redteam_kit run --threshold 0.8 --out-dir reports
    python -m llm_redteam_kit validate packs/core.jsonl

Exit codes: 0 = ok / gate passed, 1 = runtime or pack error,
            2 = regression gate failed (score below threshold or baseline).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import ClientConfig, ClientError, OpenAICompatibleClient
from .mock import MockModel
from .pack import PackError, load_pack
from .report import build_report, write_reports
from .runner import run_pack
from .scoring import compare_to_baseline, gate_passes, summarize

def _default_pack():
    """Locate the bundled core pack.

    The canonical copy ships inside the package (``llm_redteam_kit/packs/``)
    so an installed ``llm-redteam-kit run --mock`` works out of the box; the
    repo-root ``packs/`` copy is the fallback for source checkouts.
    """
    package_copy = Path(__file__).resolve().parent / "packs" / "core.jsonl"
    if package_copy.exists():
        return package_copy
    return Path(__file__).resolve().parent.parent / "packs" / "core.jsonl"


DEFAULT_PACK = _default_pack()


def _add_run_args(parser):
    parser.add_argument("--pack", default=str(DEFAULT_PACK), help="path to JSONL test pack")
    parser.add_argument("--mock", action="store_true",
                        help="use the built-in offline mock model (no network, no API key)")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL (or LLM_BASE_URL)")
    parser.add_argument("--model", default=None, help="model name (or LLM_MODEL)")
    parser.add_argument("--api-key", default=None, help="API key (or LLM_API_KEY; env preferred)")
    parser.add_argument("--out-dir", default="reports", help="where to write report.json/report.md")
    parser.add_argument("--threshold", type=float, default=None,
                        help="minimum acceptable pass rate 0..1; exit 2 if below")
    parser.add_argument("--baseline", default=None,
                        help="path to a previous report.json; exit 2 if pass rate drops below it")


def cmd_run(args):
    if args.threshold is not None and not 0.0 <= args.threshold <= 1.0:
        print(
            f"error: --threshold must be between 0 and 1 (got {args.threshold})",
            file=sys.stderr,
        )
        return 1
    try:
        cases = load_pack(args.pack)
    except (PackError, OSError) as exc:
        print(f"error: could not load pack: {exc}", file=sys.stderr)
        return 1

    if args.mock:
        client = MockModel()
        model_label = "mock-model (offline)"
    else:
        config = ClientConfig.from_env(args.base_url, args.model, args.api_key)
        client = OpenAICompatibleClient(config)
        model_label = f"{config.model} @ {config.base_url}"

    print(f"running {len(cases)} cases from {args.pack} against {model_label} ...")
    try:
        results = run_pack(cases, client)
    except ClientError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    summary = summarize(results)
    report = build_report(results, model_label, str(args.pack))
    try:
        json_path, md_path = write_reports(report, args.out_dir)
    except OSError as exc:
        print(f"error: could not write reports to {args.out_dir}: {exc}", file=sys.stderr)
        return 1
    print(
        f"done: {summary.passed}/{summary.total} passed "
        f"(pass rate {summary.pass_rate:.1%}, "
        f"attack success rate {summary.attack_success_rate:.1%})"
    )
    print(f"reports written to {json_path} and {md_path}")

    if args.threshold is not None:
        if not gate_passes(summary, args.threshold):
            print(
                f"GATE FAILED: pass rate {summary.pass_rate:.1%} < threshold {args.threshold:.1%}",
                file=sys.stderr,
            )
            return 2
        print(f"gate passed: pass rate >= {args.threshold:.1%}")

    if args.baseline:
        try:
            baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
            delta = compare_to_baseline(summary, baseline["summary"])
        except (OSError, KeyError, ValueError) as exc:
            print(f"error: could not read baseline: {exc}", file=sys.stderr)
            return 1
        print(f"pass-rate delta vs baseline: {delta:+.1%}")
        if delta < 0:
            print("GATE FAILED: pass rate dropped below baseline", file=sys.stderr)
            return 2

    return 0


def cmd_validate(args):
    try:
        cases = load_pack(args.pack)
    except (PackError, OSError) as exc:
        print(f"invalid pack: {exc}", file=sys.stderr)
        return 1
    by_category = {}
    for case in cases:
        by_category[case.category] = by_category.get(case.category, 0) + 1
    print(f"pack OK: {len(cases)} cases")
    for name, count in sorted(by_category.items()):
        print(f"  {name}: {count}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="llm-redteam-kit",
        description="Authorized LLM red-teaming evaluation toolkit (OWASP LLM Top 10).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run a test pack against a model")
    _add_run_args(run_parser)
    run_parser.set_defaults(func=cmd_run)

    validate_parser = sub.add_parser("validate", help="validate a test pack file")
    validate_parser.add_argument("pack", help="path to JSONL test pack")
    validate_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
