## What changed

<!-- One or two sentences. What is different after this pull request? -->

## Why

<!-- Link the issue it closes, or state the problem it solves. For a
     probe case: the weakness it detects and its OWASP LLM category. -->

## How it was tested

<!-- The exact commands you ran and what they printed, e.g.
     `python -m pytest -q` (all passing),
     `python -m llm_redteam_kit validate packs/core.jsonl`,
     `python -m llm_redteam_kit run --mock --threshold 0.5 --out-dir reports`. -->

## Checklist

- [ ] Full test suite passes locally and CI is green
- [ ] Tests added or updated for the change (detector changes include the exact response text that motivated them)
- [ ] For probe cases: **both** pack copies updated byte-identical (`packs/core.jsonl` and `llm_redteam_kit/packs/core.jsonl`), and `validate` passes
- [ ] No new runtime dependency (the toolkit is standard-library only)
- [ ] No real API keys, endpoints I am not authorised to test, or secrets anywhere in the diff
- [ ] Docs updated (README / docs) if behaviour changed
- [ ] One logical change in this PR
