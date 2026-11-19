"""llm-redteam-kit: an authorized LLM red-teaming evaluation toolkit.

Sends a curated pack of prompt-injection, jailbreak, system-prompt-extraction
and data-exfiltration probes to an OpenAI-compatible chat endpoint (or to a
built-in offline mock model), scores the responses with heuristic detectors,
and produces JSON + Markdown reports with a CI regression gate.

Only test models and applications you own or are authorized to evaluate.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
