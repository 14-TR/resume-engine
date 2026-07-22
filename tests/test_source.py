"""Tests for shared source loading helpers."""

from __future__ import annotations

import io

import click
import pytest

from resume_engine.source import (
    load_job_posting,
    load_master_resume,
    load_raw_resume_text,
    read_text_file,
)


def test_read_text_file_uses_utf8(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_text("Jose\nGIS analyst", encoding="utf-8")

    assert read_text_file(path) == "Jose\nGIS analyst"


def test_read_text_file_missing_path_raises_click_exception(tmp_path):
    path = tmp_path / "missing.txt"

    with pytest.raises(click.ClickException, match="Input file not found"):
        read_text_file(path)


def test_read_text_file_directory_raises_click_exception(tmp_path):
    with pytest.raises(click.ClickException, match="Input path is a directory"):
        read_text_file(tmp_path)


def test_read_text_file_non_utf8_raises_click_exception(tmp_path):
    path = tmp_path / "resume.txt"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(click.ClickException, match="Input file must be valid UTF-8 text"):
        read_text_file(path)


def test_load_raw_resume_text_from_file(tmp_path):
    path = tmp_path / "raw.txt"
    path.write_text("Jane Doe\nPython", encoding="utf-8")

    assert load_raw_resume_text(str(path), False) == "Jane Doe\nPython"


def test_load_raw_resume_text_from_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("John Smith\nSQL"))

    assert load_raw_resume_text(None, True) == "John Smith\nSQL"


@pytest.mark.parametrize(
    ("text_file", "from_stdin", "message"),
    [
        (None, False, "Provide --text <file> or --stdin"),
        ("raw.txt", True, "Use --text OR --stdin"),
    ],
)
def test_load_raw_resume_text_requires_one_source(text_file, from_stdin, message):
    with pytest.raises(click.UsageError, match=message):
        load_raw_resume_text(text_file, from_stdin)


def test_load_master_resume_from_file(tmp_path):
    path = tmp_path / "master.md"
    path.write_text("# Jane Doe", encoding="utf-8")

    assert load_master_resume(str(path), None, None) == "# Jane Doe"


def test_load_master_resume_from_linkedin_url(monkeypatch):
    monkeypatch.setattr(
        "resume_engine.linkedin.scrape_linkedin_profile",
        lambda url: f"# Profile\n{url}",
    )

    assert load_master_resume(None, "https://www.linkedin.com/in/jane", None) == (
        "# Profile\nhttps://www.linkedin.com/in/jane"
    )


def test_load_master_resume_from_linkedin_export(monkeypatch):
    monkeypatch.setattr(
        "resume_engine.linkedin.parse_linkedin_export",
        lambda export_path: f"# Export\n{export_path}",
    )

    assert load_master_resume(None, None, "linkedin.zip") == "# Export\nlinkedin.zip"


def test_load_master_resume_missing_httpx_raises_click_exception(monkeypatch):
    monkeypatch.setattr(
        "resume_engine.linkedin.scrape_linkedin_profile",
        lambda url: (_ for _ in ()).throw(
            RuntimeError("httpx is required for LinkedIn URL imports; install resume-engine deps.")
        ),
    )

    with pytest.raises(click.ClickException, match="httpx is required for LinkedIn URL imports"):
        load_master_resume(None, "https://www.linkedin.com/in/jane", None)


@pytest.mark.parametrize(
    ("master", "linkedin_url", "linkedin_export", "message"),
    [
        (None, None, None, "Provide --master, --linkedin-url, or --linkedin-export"),
        ("resume.md", "https://example.com", None, "Use only one of --master"),
        ("resume.md", None, "linkedin.zip", "Use only one of --master"),
        (None, "https://example.com", "linkedin.zip", "Use only one of --master"),
    ],
)
def test_load_master_resume_requires_one_source(master, linkedin_url, linkedin_export, message):
    with pytest.raises(click.UsageError, match=message):
        load_master_resume(master, linkedin_url, linkedin_export)


def test_load_job_posting_from_file(tmp_path):
    path = tmp_path / "job.txt"
    path.write_text("Need Python", encoding="utf-8")

    assert load_job_posting(str(path), None) == "Need Python"


def test_load_job_posting_from_url(monkeypatch):
    monkeypatch.setattr(
        "resume_engine.scraper.scrape_job_posting",
        lambda url: f"Scraped {url}",
    )

    assert load_job_posting(None, "https://example.com/job") == "Scraped https://example.com/job"


def test_load_job_posting_missing_httpx_raises_click_exception(monkeypatch):
    monkeypatch.setattr(
        "resume_engine.scraper.scrape_job_posting",
        lambda url: (_ for _ in ()).throw(
            RuntimeError("httpx is required for job URL scraping; install resume-engine deps.")
        ),
    )

    with pytest.raises(click.ClickException, match="httpx is required for job URL scraping"):
        load_job_posting(None, "https://example.com/job")


@pytest.mark.parametrize(
    ("job", "job_url", "message"),
    [
        (None, None, "Provide either --job or --job-url"),
        ("job.txt", "https://example.com/job", "Use only one of --job or --job-url"),
    ],
)
def test_load_job_posting_requires_one_source(job, job_url, message):
    with pytest.raises(click.UsageError, match=message):
        load_job_posting(job, job_url)
