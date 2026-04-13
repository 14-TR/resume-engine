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
        assert "import" in result.output
        assert "validate" in result.output
        assert "doctor" in result.output

    def test_legacy_module_entrypoint_help(self):
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "--help"],
            cwd="/Users/tr-mini/Desktop/resume-engine",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "AI-powered resume tailoring CLI." in result.stdout
        assert "tailor" in result.stdout

    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.3" in result.output

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

    def test_package_help(self, runner):
        result = runner.invoke(main, ["package", "--help"])
        assert result.exit_code == 0
        assert "--validate-report" in result.output
        assert "--outdir" in result.output

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

    def test_track_help(self, runner):
        result = runner.invoke(main, ["track", "--help"])
        assert result.exit_code == 0
        assert "export" in result.output

    def test_doctor_help(self, runner):
        result = runner.invoke(main, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "--strict" in result.output

    def test_track_export_help(self, runner):
        result = runner.invoke(main, ["track", "export", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--output" in result.output


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


class TestImportCommand:
    def test_import_help(self, runner):
        result = runner.invoke(main, ["import", "--help"])
        assert result.exit_code == 0
        assert "--text" in result.output
        assert "--stdin" in result.output
        assert "--output" in result.output
        assert "--model" in result.output

    def test_import_requires_source(self, runner, tmp_path):
        result = runner.invoke(main, ["import", "--output", str(tmp_path / "out.md")])
        assert result.exit_code != 0
        assert "stdin" in result.output.lower() or "text" in result.output.lower()

    def test_import_rejects_both_sources(self, runner, tmp_path):
        text_file = tmp_path / "raw.txt"
        text_file.write_text("John Doe\nPython developer")
        result = runner.invoke(
            main,
            ["import", "--text", str(text_file), "--stdin", "--output", str(tmp_path / "out.md")],
            input="some stdin",
        )
        assert result.exit_code != 0
        assert "stdin" in result.output.lower() or "both" in result.output.lower()


class TestTrackExportCommand:
    def test_track_export_json_stdout(self, runner, tmp_path, monkeypatch):
        db_dir = tmp_path / "xdg-data"
        monkeypatch.setenv("XDG_DATA_HOME", str(db_dir))

        result = runner.invoke(
            main,
            ["track", "add", "--company", "Acme", "--role", "Engineer", "--status", "screening"],
        )
        assert result.exit_code == 0

        export_result = runner.invoke(main, ["track", "export", "--format", "json"])
        assert export_result.exit_code == 0
        assert '"company": "Acme"' in export_result.output
        assert '"status": "screening"' in export_result.output

    def test_track_export_csv_file(self, runner, tmp_path, monkeypatch):
        db_dir = tmp_path / "xdg-data"
        monkeypatch.setenv("XDG_DATA_HOME", str(db_dir))

        runner.invoke(main, ["track", "add", "--company", "Acme", "--role", "Engineer"])
        runner.invoke(
            main,
            ["track", "add", "--company", "Beta", "--role", "Analyst", "--status", "interview"],
        )

        output_file = tmp_path / "applications.csv"
        export_result = runner.invoke(
            main,
            [
                "track",
                "export",
                "--format",
                "csv",
                "--status",
                "interview",
                "--output",
                str(output_file),
            ],
        )
        assert export_result.exit_code == 0
        assert output_file.exists()
        csv_text = output_file.read_text()
        assert "company,role,date,status,url,notes,created_at,updated_at" in csv_text
        assert "Beta,Analyst" in csv_text
        assert "Acme" not in csv_text


class TestPackageCommand:
    def test_package_generates_validation_report(self, runner, tmp_path, monkeypatch):
        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\n\n## Experience\n- Built Python APIs for Acme Corp.\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Acme Corp needs a Python engineer who can ship APIs.")
        outdir = tmp_path / "application"

        monkeypatch.setattr(
            "resume_engine.engine.tailor_resume",
            lambda master_text, job_text, model, template=None: (
                "# Tailored Resume\n\n- Built Python APIs for Acme Corp.\n"
            ),
        )
        monkeypatch.setattr(
            "resume_engine.engine.generate_cover_letter",
            lambda master_text, job_text, model, template=None: (
                "Dear Acme Corp,\n\nI build Python APIs.\n"
            ),
        )

        result = runner.invoke(
            main,
            [
                "package",
                "--master",
                str(master_file),
                "--job",
                str(job_file),
                "--outdir",
                str(outdir),
                "--validate-report",
            ],
        )

        assert result.exit_code == 0
        assert (outdir / "resume.md").exists()
        assert (outdir / "cover-letter.md").exists()
        report_path = outdir / "validation-report.md"
        assert report_path.exists()
        report_text = report_path.read_text()
        assert "# Validation Report" in report_text
        assert "## Resume" in report_text
        assert "## Cover-Letter" in report_text

    def test_package_skips_validation_report_by_default(self, runner, tmp_path, monkeypatch):
        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\n\n- Built Python APIs.\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Need a Python engineer.")
        outdir = tmp_path / "application"

        monkeypatch.setattr(
            "resume_engine.engine.tailor_resume",
            lambda master_text, job_text, model, template=None: "# Tailored Resume\n",
        )
        monkeypatch.setattr(
            "resume_engine.engine.generate_cover_letter",
            lambda master_text, job_text, model, template=None: "Dear team,\n",
        )

        result = runner.invoke(
            main,
            [
                "package",
                "--master",
                str(master_file),
                "--job",
                str(job_file),
                "--outdir",
                str(outdir),
            ],
        )

        assert result.exit_code == 0
        assert not (outdir / "validation-report.md").exists()
