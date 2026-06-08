"""Tests for LLM provider helpers."""

import importlib
import sys
from typing import Optional


def _reload_llm(monkeypatch, timeout_value: Optional[str] = None):
    if timeout_value is None:
        monkeypatch.delenv("OLLAMA_GENERATE_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("OLLAMA_GENERATE_TIMEOUT_SECONDS", timeout_value)
    sys.modules.pop("resume_engine.llm", None)
    import resume_engine.llm as llm

    return importlib.reload(llm)


def test_ollama_generate_timeout_defaults_longer_for_real_generation(monkeypatch):
    llm = _reload_llm(monkeypatch)
    assert llm.OLLAMA_GENERATE_TIMEOUT_SECONDS == 360


def test_ollama_generate_timeout_can_be_overridden(monkeypatch):
    llm = _reload_llm(monkeypatch, "480")
    assert llm.OLLAMA_GENERATE_TIMEOUT_SECONDS == 480


def test_ollama_uses_generate_timeout_for_requests(monkeypatch):
    llm = _reload_llm(monkeypatch, "480")
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "tailored output"}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(llm.httpx, "post", fake_post)

    result = llm.complete("test prompt", model="ollama")

    assert result == "tailored output"
    assert captured["url"].endswith("/api/generate")
    assert captured["timeout"] == 480
