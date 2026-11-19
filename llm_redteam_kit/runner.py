"""Run a test pack against a model client and evaluate every response."""

from __future__ import annotations

from .detectors import evaluate


def run_pack(cases, client):
    """Send every case prompt to `client` (a callable prompt -> text).

    Returns a list of CaseResult in pack order. Client exceptions propagate
    as-is so CI fails loudly on a broken endpoint instead of silently
    scoring an empty run as a pass.
    """
    results = []
    for case in cases:
        response = client(case.prompt)
        results.append(evaluate(case, response))
    return results
