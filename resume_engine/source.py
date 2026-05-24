"""Shared source loading helpers for user-provided resume and job text."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import click


def read_text_file(path: str | Path) -> str:
    """Read user-provided text files with a consistent encoding."""
    return Path(path).read_text(encoding="utf-8")


def load_raw_resume_text(text_file: str | None, from_stdin: bool) -> str:
    """Load raw import text from exactly one import source."""
    if not text_file and not from_stdin:
        raise click.UsageError("Provide --text <file> or --stdin to read from stdin")
    if text_file and from_stdin:
        raise click.UsageError("Use --text OR --stdin, not both")

    if from_stdin:
        return sys.stdin.read()
    return read_text_file(text_file)  # type: ignore[arg-type]


def load_master_resume(
    master: str | None,
    linkedin_url: str | None,
    linkedin_export: str | None,
    *,
    status: Callable[[str], None] | None = None,
) -> str:
    """Load master resume text from exactly one master resume source."""
    sources = [source for source in (master, linkedin_url, linkedin_export) if source]
    if len(sources) == 0:
        raise click.UsageError(
            "Provide --master, --linkedin-url, or --linkedin-export as the resume source."
        )
    if len(sources) > 1:
        raise click.UsageError("Use only one of --master, --linkedin-url, or --linkedin-export.")

    if linkedin_url:
        from .linkedin import scrape_linkedin_profile

        if status:
            status("[dim]Fetching LinkedIn profile...[/dim]")
        return scrape_linkedin_profile(linkedin_url)

    if linkedin_export:
        from .linkedin import parse_linkedin_export

        if status:
            status("[dim]Parsing LinkedIn export...[/dim]")
        return parse_linkedin_export(linkedin_export)

    return read_text_file(master)  # type: ignore[arg-type]


def load_job_posting(job: str | None, job_url: str | None) -> str:
    """Load job posting text from exactly one job source."""
    sources = [source for source in (job, job_url) if source]
    if len(sources) == 0:
        raise click.UsageError("Provide either --job or --job-url")
    if len(sources) > 1:
        raise click.UsageError("Use only one of --job or --job-url.")

    if job_url:
        from .scraper import scrape_job_posting

        return scrape_job_posting(job_url)

    return read_text_file(job)  # type: ignore[arg-type]
