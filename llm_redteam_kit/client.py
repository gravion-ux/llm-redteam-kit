"""Minimal OpenAI-compatible chat client (standard library only).

Works with any endpoint that implements POST /chat/completions in the
OpenAI shape: OpenAI itself, Azure OpenAI (with an api-compatible base
URL), Ollama, LM Studio, vLLM, OpenRouter, and self-hosted gateways.

Configuration comes from the environment so keys never live in code:

    LLM_BASE_URL   default https://api.openai.com/v1
    LLM_MODEL      default gpt-4o-mini
    LLM_API_KEY    required for real endpoints (not needed for --mock)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"


class ClientError(RuntimeError):
    """Raised when the endpoint cannot be reached or returns an error."""


@dataclass
class ClientConfig:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str = ""
    timeout: float = 60.0

    @classmethod
    def from_env(cls, base_url=None, model=None, api_key=None):
        return cls(
            base_url=(base_url or os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/"),
            model=model or os.environ.get("LLM_MODEL") or DEFAULT_MODEL,
            api_key=api_key or os.environ.get("LLM_API_KEY") or "",
        )


class OpenAICompatibleClient:
    """Callable client: client(prompt) -> response text."""

    def __init__(self, config):
        self.config = config

    def __call__(self, prompt):
        cfg = self.config
        if not cfg.api_key:
            raise ClientError(
                "no API key configured: set LLM_API_KEY or use --mock for offline runs"
            )
        payload = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
        }
        request = urllib.request.Request(
            f"{cfg.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=cfg.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise ClientError(f"endpoint returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ClientError(f"could not reach endpoint: {exc.reason}") from exc
        try:
            return body["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise ClientError(f"unexpected response shape: {str(body)[:300]}") from exc
