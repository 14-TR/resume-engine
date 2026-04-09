"""Tests for the doctor command and diagnostics."""

from click.testing import CliRunner

from resume_engine.cli import main
from resume_engine.doctor import DiagnosticResult, summarize_results


class TestDoctorHelpers:
    def test_summarize_results_counts_statuses(self):
        results = [
            DiagnosticResult("Python", "pass", "ok"),
            DiagnosticResult("Ollama", "warn", "offline"),
            DiagnosticResult("OpenAI", "fail", "missing", required=True),
        ]

        assert summarize_results(results) == (1, 1, 1)


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
