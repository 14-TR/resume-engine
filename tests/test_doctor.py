"""Tests for the doctor command and diagnostics."""

import json

from click.testing import CliRunner

from resume_engine.cli import main
from resume_engine.doctor import (
    DiagnosticResult,
    _check_cli_install,
    results_to_payload,
    summarize_results,
)


class TestDoctorHelpers:
    def test_summarize_results_counts_statuses(self):
        results = [
            DiagnosticResult("Python", "pass", "ok"),
            DiagnosticResult("Ollama", "warn", "offline"),
            DiagnosticResult("OpenAI", "fail", "missing", required=True),
        ]

        assert summarize_results(results) == (1, 1, 1)

    def test_results_to_payload_serializes_summary_and_required_status(self):
        results = [
            DiagnosticResult("Python", "pass", "ok", required=True),
            DiagnosticResult("Ollama", "warn", "offline"),
            DiagnosticResult("OpenAI", "fail", "missing", required=True),
        ]

        payload = results_to_payload(results, strict=True)

        assert payload["strict"] is True
        assert payload["summary"] == {"passed": 1, "warned": 1, "failed": 1}
        assert payload["all_required_passed"] is False
        assert payload["results"][2]["required"] is True

    def test_cli_install_check_reports_executable_path(self, monkeypatch):
        monkeypatch.setattr("resume_engine.doctor.__version__", "9.9.9")
        monkeypatch.setattr(
            "resume_engine.doctor.shutil.which", lambda name: "/usr/bin/resume-engine"
        )
        monkeypatch.setattr(
            "resume_engine.doctor._executable_version",
            lambda executable: "resume-engine, version 9.9.9",
        )

        result = _check_cli_install()

        assert result.name == "CLI install"
        assert result.status == "pass"
        assert "resume-engine 9.9.9 executable found at /usr/bin/resume-engine" in result.detail

    def test_cli_install_check_warns_on_executable_version_mismatch(self, monkeypatch):
        monkeypatch.setattr("resume_engine.doctor.__version__", "9.9.9")
        monkeypatch.setattr(
            "resume_engine.doctor.shutil.which", lambda name: "/usr/bin/resume-engine"
        )
        monkeypatch.setattr(
            "resume_engine.doctor._executable_version",
            lambda executable: "resume-engine, version 1.2.3",
        )

        result = _check_cli_install()

        assert result.name == "CLI install"
        assert result.status == "warn"
        assert "Imported resume-engine 9.9.9" in result.detail
        assert "/usr/bin/resume-engine reports 'resume-engine, version 1.2.3'" in result.detail

    def test_cli_install_check_warns_when_executable_missing(self, monkeypatch):
        monkeypatch.setattr("resume_engine.doctor.__version__", "9.9.9")
        monkeypatch.setattr("resume_engine.doctor.shutil.which", lambda name: None)

        result = _check_cli_install()

        assert result.name == "CLI install"
        assert result.status == "warn"
        assert "not on PATH" in result.detail
        assert result.required is False


class TestDoctorCommand:
    def test_doctor_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "--strict" in result.output

    def test_doctor_outputs_summary(self, monkeypatch):
        runner = CliRunner()
        fake_results = [
            DiagnosticResult("Python", "pass", "Python 3.11 detected.", required=True),
            DiagnosticResult("Ollama", "warn", "Could not reach Ollama.", required=False),
        ]
        monkeypatch.setattr("resume_engine.doctor.run_diagnostics", lambda: fake_results)

        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        assert "Summary:" in result.output
        assert "Python 3.11 detected." in result.output
        assert "Could not reach Ollama." in result.output

    def test_doctor_strict_fails_on_required_failures(self, monkeypatch):
        runner = CliRunner()
        fake_results = [
            DiagnosticResult("Python", "pass", "Python 3.11 detected.", required=True),
            DiagnosticResult("OpenAI", "fail", "OPENAI_API_KEY is not set.", required=True),
        ]
        monkeypatch.setattr("resume_engine.doctor.run_diagnostics", lambda: fake_results)

        result = runner.invoke(main, ["doctor", "--strict"])
        assert result.exit_code != 0
        assert "Doctor found required setup failures." in result.output

    def test_doctor_json_output(self, monkeypatch):
        runner = CliRunner()
        fake_results = [
            DiagnosticResult("Python", "pass", "Python 3.11 detected.", required=True),
            DiagnosticResult("Ollama", "warn", "Could not reach Ollama.", required=False),
        ]
        monkeypatch.setattr("resume_engine.doctor.run_diagnostics", lambda: fake_results)

        result = runner.invoke(main, ["doctor", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["summary"] == {"passed": 1, "warned": 1, "failed": 0}
        assert payload["all_required_passed"] is True
        assert payload["results"][1]["status"] == "warn"

    def test_doctor_json_strict_fails_on_required_failures(self, monkeypatch):
        runner = CliRunner()
        fake_results = [
            DiagnosticResult("Python", "pass", "Python 3.11 detected.", required=True),
            DiagnosticResult("OpenAI", "fail", "OPENAI_API_KEY is not set.", required=True),
        ]
        monkeypatch.setattr("resume_engine.doctor.run_diagnostics", lambda: fake_results)

        result = runner.invoke(main, ["doctor", "--json", "--strict"])

        assert result.exit_code != 0
        payload = json.loads(
            result.output.splitlines()[:-1]
            and "\n".join(result.output.splitlines()[:-1])
            or result.output
        )
        assert payload["all_required_passed"] is False
        assert "Doctor found required setup failures." in result.output
