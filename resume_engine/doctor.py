"""Environment diagnostics for resume-engine."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import List

from .config import get as cfg_get
from .llm import OLLAMA_URL, httpx
from . import __version__


@dataclass
class DiagnosticResult:
    name: str
    status: str
    detail: str
    required: bool = False


VALID_MODELS = {"ollama", "openai", "anthropic"}


def _executable_version(executable: str) -> str:
    """Return the installed CLI version string, if available."""
    result = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout or result.stderr).strip()


def _check_python() -> DiagnosticResult:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        return DiagnosticResult("Python", "pass", f"Python {version} detected.", required=True)
    return DiagnosticResult(
        "Python",
        "fail",
        f"Python {version} detected. resume-engine requires Python 3.9+.",
        required=True,
    )


def _check_default_model() -> DiagnosticResult:
    model = cfg_get("model", "ollama")
    if model in VALID_MODELS:
        return DiagnosticResult("Default model", "pass", f"Configured default model: {model}.")
    return DiagnosticResult(
        "Default model",
        "fail",
        f"Configured default model '{model}' is invalid. Use one of: anthropic, ollama, openai.",
        required=True,
    )


def _check_ollama(model: str) -> DiagnosticResult:
    required = model == "ollama"
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        count = len(models) if isinstance(models, list) else 0
        return DiagnosticResult(
            "Ollama",
            "pass",
            f"Ollama is reachable at {OLLAMA_URL} with {count} installed model(s).",
            required=required,
        )
    except Exception as exc:  # pragma: no cover - exercised via monkeypatch in tests
        status = "fail" if required else "warn"
        return DiagnosticResult(
            "Ollama",
            status,
            f"Could not reach Ollama at {OLLAMA_URL}: {exc}",
            required=required,
        )


def _check_api_key(provider: str, env_var: str, model: str) -> DiagnosticResult:
    required = model == provider
    if os.environ.get(env_var):
        return DiagnosticResult(
            provider.capitalize(),
            "pass",
            f"{env_var} is set.",
            required=required,
        )
    status = "fail" if required else "warn"
    return DiagnosticResult(
        provider.capitalize(),
        status,
        f"{env_var} is not set.",
        required=required,
    )


def _check_pandoc() -> DiagnosticResult:
    pandoc = shutil.which("pandoc")
    if pandoc:
        return DiagnosticResult("Pandoc", "pass", f"pandoc found at {pandoc}.")
    return DiagnosticResult(
        "Pandoc",
        "warn",
        "pandoc is not installed. Markdown workflows still work, but PDF export will be unavailable.",
    )


def _check_cli_install() -> DiagnosticResult:
    executable = shutil.which("resume-engine")
    imported_version = os.environ.get("RESUME_ENGINE_VERSION", __version__)
    if not executable:
        return DiagnosticResult(
            "CLI install",
            "warn",
            f"Imported resume-engine {imported_version}, but `resume-engine` is not on PATH.",
        )

    reported = _executable_version(executable)
    match = re.search(r"(\d+\.\d+\.\d+)", reported)
    reported_version = match.group(1) if match else None
    if reported_version == imported_version:
        return DiagnosticResult(
            "CLI install",
            "pass",
            f"resume-engine {imported_version} executable found at {executable}.",
        )

    return DiagnosticResult(
        "CLI install",
        "warn",
        f"Imported resume-engine {imported_version}, but {executable} reports '{reported}'.",
    )


def run_diagnostics() -> List[DiagnosticResult]:
    model = cfg_get("model", "ollama")
    results = [
        _check_python(),
        _check_default_model(),
        _check_ollama(model),
        _check_api_key("openai", "OPENAI_API_KEY", model),
        _check_api_key("anthropic", "ANTHROPIC_API_KEY", model),
        _check_pandoc(),
    ]
    return results


def summarize_results(results: List[DiagnosticResult]) -> tuple[int, int, int]:
    passed = sum(1 for result in results if result.status == "pass")
    warned = sum(1 for result in results if result.status == "warn")
    failed = sum(1 for result in results if result.status == "fail")
    return passed, warned, failed


def results_to_payload(results: List[DiagnosticResult], strict: bool = False) -> dict:
    passed, warned, failed = summarize_results(results)
    return {
        "strict": strict,
        "summary": {
            "passed": passed,
            "warned": warned,
            "failed": failed,
        },
        "all_required_passed": failed == 0,
        "results": [
            {
                "name": result.name,
                "status": result.status,
                "detail": result.detail,
                "required": result.required,
            }
            for result in results
        ],
    }
