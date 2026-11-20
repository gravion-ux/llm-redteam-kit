"""Tests for the OpenAI-compatible client (network mocked out)."""

import json
from unittest import mock

import pytest

from llm_redteam_kit.client import ClientConfig, ClientError, OpenAICompatibleClient


class FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _client_returning(body):
    client = OpenAICompatibleClient(ClientConfig(api_key="test-key"))
    patcher = mock.patch(
        "llm_redteam_kit.client.urllib.request.urlopen",
        return_value=FakeResponse(body),
    )
    return client, patcher


def test_client_returns_text_content():
    payload = {"choices": [{"message": {"content": "hello"}}]}
    client, patcher = _client_returning(json.dumps(payload).encode())
    with patcher:
        assert client("hi") == "hello"


def test_client_non_json_response_is_client_error():
    client, patcher = _client_returning(b"<html>not json</html>")
    with patcher, pytest.raises(ClientError, match="did not return JSON"):
        client("hi")


def test_client_non_string_content_is_client_error():
    payload = {"choices": [{"message": {"content": [{"type": "text", "text": "hi"}]}}]}
    client, patcher = _client_returning(json.dumps(payload).encode())
    with patcher, pytest.raises(ClientError, match="not text"):
        client("hi")


def test_client_null_content_becomes_empty_string():
    payload = {"choices": [{"message": {"content": None}}]}
    client, patcher = _client_returning(json.dumps(payload).encode())
    with patcher:
        assert client("hi") == ""
