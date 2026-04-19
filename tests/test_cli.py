"""Tests for CLI entry points (no LLM calls)."""

import json

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
    def test_package_generates_fit_summary_and_json_manifest(self, runner, tmp_path, monkeypatch):
        import sys
        import types
        from dataclasses import dataclass, field

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

        @dataclass
        class FitDimension:
            name: str
            score: int
            max_score: int
            notes: list[str] = field(default_factory=list)

        @dataclass
        class FitResult:
            total: int
            dimensions: list[FitDimension]
            verdict: str
            recommendation: str
            strengths: list[str]
            gaps: list[str]
            raw_analysis: str
            ats_score: int

        fit_stub = types.ModuleType("resume_engine.fit")
        fit_stub.assess_fit = lambda resume_text, job_text, model="ollama", ats_top_n=30: FitResult(
            total=88,
            dimensions=[
                FitDimension(
                    name="ATS Keyword Match",
                    score=18,
                    max_score=20,
                    notes=["Matched 9/10 keywords"],
                )
            ],
            verdict="Strong fit",
            recommendation="Apply",
            strengths=["Strong Python API experience"],
            gaps=["Could quantify impact more clearly"],
            raw_analysis="Strong overlap with the role.",
            ats_score=90,
        )
        monkeypatch.setitem(sys.modules, "resume_engine.fit", fit_stub)

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
                "--json",
            ],
        )

        assert result.exit_code == 0
        fit_summary_path = outdir / "fit-summary.md"
        assert fit_summary_path.exists()
        fit_text = fit_summary_path.read_text()
        assert "# Fit Summary" in fit_text
        assert "Score: 88/100" in fit_text
        assert "Strong Python API experience" in fit_text

        manifest_path = outdir / "package-summary.json"
        assert manifest_path.exists()
        payload = json.loads(manifest_path.read_text())
        assert payload["schema"] == "resume-engine.dashboard/v1"
        assert payload["command"] == "package"
        assert payload["artifacts"]["fit_summary_markdown"].endswith("fit-summary.md")
        assert payload["data"]["fit"]["total"] == 88
        assert payload["data"]["validation"] is None

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


class TestFitCommand:
    def test_fit_json_output(self, runner, tmp_path, monkeypatch):
        import sys
        import types
        from dataclasses import dataclass, field

        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\nPython, AWS, Kubernetes\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Need Python, AWS, Kubernetes.")

        @dataclass
        class FitDimension:
            name: str
            score: int
            max_score: int
            notes: list[str] = field(default_factory=list)

        @dataclass
        class FitResult:
            total: int
            dimensions: list[FitDimension]
            verdict: str
            recommendation: str
            strengths: list[str]
            gaps: list[str]
            raw_analysis: str
            ats_score: int

        fake_fit = types.ModuleType("resume_engine.fit")
        fake_fit.assess_fit = lambda master_text, job_text, model="ollama": FitResult(
            total=82,
            dimensions=[
                FitDimension(name="ATS Keyword Match", score=16, max_score=20, notes=["Matched 3/3 keywords"]),
                FitDimension(name="Required Skills Coverage", score=21, max_score=25),
                FitDimension(name="Seniority / Level Match", score=17, max_score=20),
                FitDimension(name="Industry / Domain Fit", score=12, max_score=15),
                FitDimension(name="Overall Assessment", score=16, max_score=20),
            ],
            verdict="Strong fit for the role",
            recommendation="Apply",
            strengths=["Strong Python match"],
            gaps=["No explicit fintech background"],
            raw_analysis="Structured analysis",
            ats_score=80,
        )
        monkeypatch.setitem(sys.modules, "resume_engine.fit", fake_fit)

        result = runner.invoke(
            main,
            ["fit", "--master", str(master_file), "--job", str(job_file), "--json"],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["schema"] == "resume-engine.dashboard/v1"
        assert payload["command"] == "fit"
        assert payload["inputs"]["master"] == str(master_file)
        assert payload["inputs"]["job"] == str(job_file)
        assert payload["inputs"]["job_url"] is None
        assert payload["inputs"]["model"] == "ollama"
        assert payload["summary"]["total"] == 82
        assert payload["summary"]["recommendation"] == "Apply"
        assert len(payload["data"]["dimensions"]) == 5


class TestCoverCommand:
    def test_cover_json_output_uses_dashboard_schema(self, runner, tmp_path, monkeypatch):
        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\nPython developer\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Need a Python developer.")
        output_file = tmp_path / "cover.md"

        monkeypatch.setattr(
            "resume_engine.engine.generate_cover_letter",
            lambda master_text, job_text, model, template=None: "Dear Team,\n\nI build Python systems.\n",
        )

        result = runner.invoke(
            main,
            [
                "cover",
                "--master",
                str(master_file),
                "--job",
                str(job_file),
                "--output",
                str(output_file),
                "--json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["schema"] == "resume-engine.dashboard/v1"
        assert payload["command"] == "cover"
        assert payload["inputs"]["master"] == str(master_file)
        assert payload["artifacts"]["cover_letter_markdown"] == str(output_file)
        assert payload["data"]["cover_letter_markdown"].startswith("Dear Team")
        assert output_file.exists()

class TestTailorCommand:
    def test_tailor_json_output_uses_dashboard_schema(self, runner, tmp_path, monkeypatch):
        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\nPython developer\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Need a Python developer.")
        output_file = tmp_path / "tailored.md"

        monkeypatch.setattr(
            "resume_engine.engine.tailor_resume",
            lambda master_text, job_text, model, template=None: "# Tailored Resume\n\n- Python developer\n",
        )

        result = runner.invoke(
            main,
            [
                "tailor",
                "--master",
                str(master_file),
                "--job",
                str(job_file),
                "--output",
                str(output_file),
                "--json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["schema"] == "resume-engine.dashboard/v1"
        assert payload["command"] == "tailor"
        assert payload["inputs"]["master"] == str(master_file)
        assert payload["artifacts"]["resume_markdown"] == str(output_file)
        assert payload["data"]["resume_markdown"].startswith("# Tailored Resume")
        assert output_file.exists()


class TestInterviewCommand:
    def test_interview_json_output_uses_dashboard_schema(self, runner, tmp_path, monkeypatch):
        import sys
        import types
        from dataclasses import dataclass, field

        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\nPython developer\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Need a Python developer.")

        @dataclass
        class InterviewQuestion:
            number: int
            category: str
            question: str
            framework: str = ""

        @dataclass
        class FollowupQuestion:
            number: int
            question: str
            probing: str = ""

        @dataclass
        class InterviewPrep:
            questions: list[InterviewQuestion] = field(default_factory=list)
            followups: list[FollowupQuestion] = field(default_factory=list)
            raw_questions: str = ""
            raw_followups: str = ""

        fake_interview = types.ModuleType("resume_engine.interview")
        fake_interview.generate_interview_prep = lambda *args, **kwargs: InterviewPrep(
            questions=[InterviewQuestion(number=1, category="Behavioral", question="Tell me about a project.")],
            followups=[FollowupQuestion(number=1, question="What was the impact?", probing="Metrics")],
        )
        monkeypatch.setitem(sys.modules, "resume_engine.interview", fake_interview)

        result = runner.invoke(
            main,
            ["interview", "--master", str(master_file), "--job", str(job_file), "--json"],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["schema"] == "resume-engine.dashboard/v1"
        assert payload["command"] == "interview"
        assert payload["summary"]["question_count"] == 1
        assert payload["summary"]["followup_count"] == 1
        assert payload["data"]["questions"][0]["question"] == "Tell me about a project."


class TestValidateCommand:
    def test_validate_json_output_uses_dashboard_schema(self, runner, tmp_path, monkeypatch):
        import sys
        import types
        from dataclasses import dataclass, field

        master_file = tmp_path / "master.md"
        master_file.write_text("# Jane Doe\nPython developer\n")
        job_file = tmp_path / "job.txt"
        job_file.write_text("Need a Python developer.")
        resume_file = tmp_path / "tailored.md"
        resume_file.write_text("# Tailored Resume\n")

        @dataclass
        class ValidationIssue:
            severity: str
            category: str
            message: str
            evidence: str = None
            suggestion: str = None

        @dataclass
        class ValidationTarget:
            label: str
            score: int
            issues: list[ValidationIssue] = field(default_factory=list)

        @dataclass
        class ValidationReport:
            targets: list[ValidationTarget] = field(default_factory=list)

        fake_validate = types.ModuleType("resume_engine.validate")
        fake_validate.validate_outputs = lambda **kwargs: ValidationReport(
            targets=[
                ValidationTarget(
                    label="resume",
                    score=72,
                    issues=[ValidationIssue(severity="high", category="claim", message="Metric not grounded")],
                )
            ]
        )
        monkeypatch.setitem(sys.modules, "resume_engine.validate", fake_validate)

        result = runner.invoke(
            main,
            [
                "validate",
                "--master",
                str(master_file),
                "--job",
                str(job_file),
                "--resume",
                str(resume_file),
                "--json",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["schema"] == "resume-engine.dashboard/v1"
        assert payload["command"] == "validate"
        assert payload["summary"]["issue_count"] == 1
        assert payload["summary"]["high_severity_issue_count"] == 1
        assert payload["summary"]["lowest_trust_score"] == 72
        assert payload["data"]["targets"][0]["label"] == "resume"
