"""LLM provider abstraction -- Ollama (local), OpenAI, Anthropic."""

import os

try:
    import httpx
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal test envs

    class _MissingHttpx:
        HTTPError = RuntimeError

        @staticmethod
        def get(*args, **kwargs):
            raise RuntimeError("httpx is required for network-backed LLM calls")

        @staticmethod
        def post(*args, **kwargs):
            raise RuntimeError("httpx is required for network-backed LLM calls")

    httpx = _MissingHttpx()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
OPENAI_MODEL = "gpt-4o-mini"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
DEFAULT_TIMEOUT_SECONDS = 120
OLLAMA_GENERATE_TIMEOUT_SECONDS = int(
    os.getenv("OLLAMA_GENERATE_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS * 3))
)


def complete(prompt: str, model: str = "ollama") -> str:
    """Send prompt to LLM and return completion text."""
    if model == "ollama":
        return _ollama(prompt)
    elif model == "openai":
        return _openai(prompt)
    elif model == "anthropic":
        return _anthropic(prompt)
    else:
        raise ValueError(f"Unknown model provider: {model}")


def _ollama(prompt: str) -> str:
    resp = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 4000},
        },
        timeout=OLLAMA_GENERATE_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def _openai(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 4000,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _anthropic(prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip()
