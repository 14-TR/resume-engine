"""Regression tests for CLI command reference coverage."""

from pathlib import Path

from resume_engine.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_command_reference_covers_all_top_level_commands():
    command_reference = (REPO_ROOT / "docs/reference/commands.md").read_text()

    missing_sections = [
        name for name in sorted(main.commands) if f"## `{name}`" not in command_reference
    ]

    assert missing_sections == []
