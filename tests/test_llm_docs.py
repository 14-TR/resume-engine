"""Regression tests for documented LLM backend defaults."""

from pathlib import Path

from resume_engine.llm import ANTHROPIC_MODEL, OPENAI_MODEL

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_llm_backend_docs_match_default_cloud_models():
    docs = (REPO_ROOT / "docs/reference/llm-backends.md").read_text()

    assert OPENAI_MODEL in docs
    assert ANTHROPIC_MODEL in docs
    assert "Claude Haiku" not in docs
