# Security Policy

`llm-redteam-kit` is a security evaluation tool, so the security of the
tool itself matters. This policy covers vulnerabilities **in this
repository** — the toolkit, its pack handling, and its reporting code.

## Reporting a vulnerability

Please **do not open a public issue** for a vulnerability. Report it
privately, either way:

- GitHub's private vulnerability reporting:
  <https://github.com/gravion-ux/llm-redteam-kit/security/advisories/new>
- Email: priyanshukumarthakur937@gmail.com

Please include:

- A one- or two-sentence description of the issue.
- The version or commit SHA it affects.
- The smallest reproduction you have — a failing test or a crafted
  pack/response file is ideal.
- The impact you believe it has.

You can expect an acknowledgement within a few days.

## Disclosure timing

Please allow **90 days** for a fix to be released before any public
disclosure. If a fix ships earlier, coordinated disclosure can happen
as soon as the fixed version is available. Timing can be discussed —
the goal is that users are not left exposed.

## Scope

In scope — the toolkit itself, for example:

- Code execution or file writes outside the requested output directory
  triggered by a malicious probe pack (`.jsonl`) or a malicious model
  response file.
- The client/runner following redirects or endpoints it was not told
  to use, or leaking the user's API key anywhere other than the
  configured provider endpoint.
- Scoring/report code that can be made to execute embedded content
  from a model response.

Out of scope:

- The probe prompts themselves. The pack implements standard, publicly
  documented evaluation methodology (OWASP LLM Top 10) for authorised
  testing; a probe existing is not a vulnerability.
- Vulnerabilities in a model or service you evaluated with the kit —
  those belong to that model's owner. Run the kit only against models
  and endpoints you own or are explicitly authorised to evaluate.
- A model "failing" a probe. That is a triage signal about the model,
  not a defect in this tool.

## Supported versions

Only the current `main` branch and the latest release are supported.
Older commits are kept for history, not for backports.

## Repository hygiene

GitHub secret scanning and push protection are enabled for this
repository. Dependabot checks Python and GitHub Actions dependencies
weekly, and CodeQL runs on pushes, pull requests, and a weekly schedule.
Never commit API keys or real model responses containing private data;
use the offline mock mode and synthetic fixtures for public examples.
