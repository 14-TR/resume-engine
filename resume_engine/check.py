"""System health checker for resume-engine dependencies."""

from __future__ import annotations

import os
import shutil
import subprocess


def check_ollama() -> dict:
    """Check if Ollama is running and reachable."""
    import httpx

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        resp = httpx.get(f"{ollama_url}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return {"ok": True, "url": ollama_url, "models": models}
    except Exception as exc:
        return {"ok": False, "url": ollama_url, "error": str(exc)}


def check_pandoc() -> dict:
    """Check if pandoc is installed and accessible."""
    path = shutil.which("pandoc")
    if not path:
        return {"ok": False, "error": "pandoc not found in PATH"}
    try:
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
        return {"ok": True, "path": path, "version": version_line}
    except Exception as exc:
        return {"ok": False, "path": path, "error": str(exc)}


def check_pdflatex() -> dict:
    """Check if pdflatex (LaTeX engine) is available for PDF conversion."""
    path = shutil.which("pdflatex")
    if not path:
        return {"ok": False, "error": "pdflatex not found in PATH"}
    try:
        result = subprocess.run(
            ["pdflatex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_line = result.stdout.splitlines()[0] if result.stdout else "unknown"
        return {"ok": True, "path": path, "version": version_line}
    except Exception as exc:
        return {"ok": False, "path": path, "error": str(exc)}


def check_openai_key() -> dict:
    """Check if OPENAI_API_KEY is set (does not validate against API)."""
    key = os.environ.get("OPENAI_API_KEY", "")
    if key and key.startswith("sk-"):
        masked = key[:7] + "..." + key[-4:]
        return {"ok": True, "masked": masked}
    elif key:
        return {"ok": False, "error": "OPENAI_API_KEY is set but does not look like a valid key"}
    else:
        return {"ok": False, "error": "OPENAI_API_KEY not set"}


def check_anthropic_key() -> dict:
    """Check if ANTHROPIC_API_KEY is set (does not validate against API)."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key and key.startswith("sk-ant-"):
        masked = key[:10] + "..." + key[-4:]
        return {"ok": True, "masked": masked}
    elif key:
        return {"ok": False, "error": "ANTHROPIC_API_KEY is set but does not look like a valid key"}
    else:
        return {"ok": False, "error": "ANTHROPIC_API_KEY not set"}


def run_checks() -> list[dict]:
    """Run all health checks and return results as a list of check dicts."""
    results = []

    # Ollama
    ollama = check_ollama()
    entry = {
        "name": "Ollama",
        "category": "LLM Backend",
        "ok": ollama["ok"],
    }
    if ollama["ok"]:
        model_count = len(ollama.get("models", []))
        model_names = ", ".join(ollama.get("models", [])[:3])
        suffix = f" (+{model_count - 3} more)" if model_count > 3 else ""
        entry["detail"] = f"running at {ollama['url']} -- {model_count} model(s) pulled" + (
            f" ({model_names}{suffix})" if model_names else ""
        )
    else:
        entry["detail"] = ollama.get("error", "not reachable")
        entry["hint"] = "Run: ollama serve"
    results.append(entry)

    # Pandoc
    pandoc = check_pandoc()
    entry = {
        "name": "pandoc",
        "category": "PDF Output (optional)",
        "ok": pandoc["ok"],
    }
    if pandoc["ok"]:
        entry["detail"] = pandoc.get("version", "installed")
    else:
        entry["detail"] = pandoc.get("error", "not found")
        entry["hint"] = "Install: brew install pandoc  (macOS) or  sudo apt install pandoc  (Linux)"
    results.append(entry)

    # pdflatex
    pdflatex = check_pdflatex()
    entry = {
        "name": "pdflatex",
        "category": "PDF Output (optional)",
        "ok": pdflatex["ok"],
    }
    if pdflatex["ok"]:
        entry["detail"] = pdflatex.get("version", "installed")
    else:
        entry["detail"] = pdflatex.get("error", "not found")
        entry["hint"] = (
            "Install: brew install basictex  then  sudo tlmgr install titlesec enumitem parskip"
        )
    results.append(entry)

    # OpenAI API key
    openai = check_openai_key()
    entry = {
        "name": "OpenAI API key",
        "category": "LLM Backend (optional)",
        "ok": openai["ok"],
    }
    if openai["ok"]:
        entry["detail"] = f"set ({openai['masked']})"
    else:
        entry["detail"] = openai.get("error", "not set")
        entry["hint"] = "export OPENAI_API_KEY=sk-..."
    results.append(entry)

    # Anthropic API key
    anthropic = check_anthropic_key()
    entry = {
        "name": "Anthropic API key",
        "category": "LLM Backend (optional)",
        "ok": anthropic["ok"],
    }
    if anthropic["ok"]:
        entry["detail"] = f"set ({anthropic['masked']})"
    else:
        entry["detail"] = anthropic.get("error", "not set")
        entry["hint"] = "export ANTHROPIC_API_KEY=sk-ant-..."
    results.append(entry)

    return results
