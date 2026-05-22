"""Regression tests for CLI command reference coverage."""

import re
from pathlib import Path

import click

from resume_engine.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMAND_SECTION_RE = re.compile(r"^## `(?P<name>[^`]+)`\n(?P<body>.*?)(?=^## `|\Z)", re.M | re.S)
DOC_FLAG_RE = re.compile(r"`(?P<flag>--[a-z0-9][a-z0-9-]*)`")


def _command_reference_sections() -> dict[str, str]:
    command_reference = (REPO_ROOT / "docs/reference/commands.md").read_text()
    return {
        match.group("name"): match.group("body")
        for match in COMMAND_SECTION_RE.finditer(command_reference)
    }


def _long_options(command: click.Command) -> set[str]:
    long_options: set[str] = set()
    for param in command.params:
        options = [*getattr(param, "opts", []), *getattr(param, "secondary_opts", [])]
        long_options.update(option for option in options if option.startswith("--"))
    return long_options


def test_command_reference_covers_all_top_level_commands():
    sections = _command_reference_sections()

    missing_sections = [name for name in sorted(main.commands) if name not in sections]

    assert missing_sections == []


def test_command_reference_covers_live_command_options():
    sections = _command_reference_sections()
    missing_options = {}

    for name, command in sorted(main.commands.items()):
        if name not in sections:
            continue

        documented_options = {match.group("flag") for match in DOC_FLAG_RE.finditer(sections[name])}
        command_missing = sorted(_long_options(command) - documented_options)
        if command_missing:
            missing_options[name] = command_missing

    assert missing_options == {}


def test_contributing_docs_match_ci_quality_gates():
    docs = (REPO_ROOT / "docs/contributing.md").read_text()

    assert "pytest tests/" in docs
    assert "ruff check resume_engine/ tests/" in docs
    assert "ruff format --check resume_engine/ tests/" in docs
    assert "ruff check ." not in docs
