"""Tests for CLI entry points (no LLM calls)."""

import pytest
from click.testing import CliRunner

from resume_engine.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIHelp:
    def test_main_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "tailor" in result.output
        assert "cover" in result.output
        assert "package" in result.output
        assert "ats" in result.output
        assert "batch" in result.output
        assert "templates" in result.output

    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.output

    def test_tailor_help(self, runner):
        result = runner.invoke(main, ["tailor", "--help"])
        assert result.exit_code == 0
        assert "--master" in result.output
        assert "--job" in result.output
        assert "--model" in result.output
        assert "--format" in result.output

    def test_cover_help(self, runner):
        result = runner.invoke(main, ["cover", "--help"])
        assert result.exit_code == 0
        assert "--master" in result.output

    def test_ats_help(self, runner):
        result = runner.invoke(main, ["ats", "--help"])
        assert result.exit_code == 0
        assert "--resume" in result.output
        assert "--job" in result.output

    def test_batch_help(self, runner):
        result = runner.invoke(main, ["batch", "--help"])
        assert result.exit_code == 0
        assert "--master" in result.output
        assert "--jobs-dir" in result.output

    def test_templates_list_help(self, runner):
        result = runner.invoke(main, ["templates", "list", "--help"])
        assert result.exit_code == 0


class TestATSCommand:
    def test_ats_requires_job(self, runner, tmp_path):
        resume_file = tmp_path / "resume.md"
        resume_file.write_text("# Jane Doe\nPython developer")
        result = runner.invoke(main, ["ats", "--resume", str(resume_file)])
        assert result.exit_code != 0
        assert "job" in result.output.lower() or "error" in result.output.lower()

    def test_ats_full_run(self, runner, tmp_path):
        resume_file = tmp_path / "resume.md"
        resume_file.write_text(
            "# Jane Doe\n## Skills\nPython, Django, PostgreSQL, REST APIs\n"
            "## Experience\nPython developer with Django and PostgreSQL. REST API design."
        )
        job_file = tmp_path / "job.txt"
        job_file.write_text(
            "We need a Python developer. Python skills required. Django framework experience. "
            "PostgreSQL database. Python REST API development. Python testing."
        )
        result = runner.invoke(main, ["ats", "--resume", str(resume_file), "--job", str(job_file)])
        assert result.exit_code == 0
        assert "%" in result.output

    def test_ats_before_after_comparison(self, runner, tmp_path):
        original = tmp_path / "original.md"
        original.write_text("# Jane\nJava developer")
        tailored = tmp_path / "tailored.md"
        tailored.write_text("# Jane\nPython developer with Django and SQL skills.")
        job = tmp_path / "job.txt"
        job.write_text(
            "Python Django SQL developer needed. Python required. Django preferred. SQL database."
        )
        result = runner.invoke(
            main,
            [
                "ats",
                "--resume",
                str(original),
                "--job",
                str(job),
                "--tailored",
                str(tailored),
            ],
        )
        assert result.exit_code == 0
        assert "%" in result.output


class TestTemplatesCommand:
    def test_templates_list_runs(self, runner):
        result = runner.invoke(main, ["templates", "list"])
        assert result.exit_code == 0

    def test_templates_show_unknown(self, runner):
        result = runner.invoke(main, ["templates", "show", "nonexistent-xyz"])
        assert result.exit_code != 0
