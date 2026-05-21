"""Regression tests for documented LLM backend defaults."""

from pathlib import Path

from resume_engine.llm import ANTHROPIC_MODEL, OPENAI_MODEL

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_WITH_CLOUD_DEFAULT_MODEL_CLAIMS = (
    REPO_ROOT / "docs/reference/llm-backends.md",
    REPO_ROOT / "docs/technical-paper.md",
)


def test_llm_backend_docs_match_default_cloud_models():
    for doc_path in DOCS_WITH_CLOUD_DEFAULT_MODEL_CLAIMS:
        docs = doc_path.read_text()

        assert OPENAI_MODEL in docs, f"{doc_path} must document the OpenAI default"
        assert ANTHROPIC_MODEL in docs, f"{doc_path} must document the Anthropic default"
        assert "Claude Haiku" not in docs, f"{doc_path} must not document stale Anthropic defaults"
