"""Tests for grounded output validation."""

from click.testing import CliRunner

from resume_engine.cli import main
from resume_engine.validate import validate_outputs, validate_text

MASTER = """# Jane Smith

## Experience
### Senior Software Engineer -- Acme Corp (2021-2024)
- Led migration of monolith to microservices, reducing latency by 40%
- Built CI/CD pipeline with GitHub Actions

## Skills
Python, AWS, Kubernetes, PostgreSQL
"""

JOB = """Senior Backend Engineer

Acme Corp is hiring a Senior Backend Engineer.
Requirements: Python, AWS, Kubernetes, PostgreSQL.
"""

TAILORED_OK = """# Jane Smith

## Experience
### Senior Software Engineer -- Acme Corp (2021-2024)
- Led migration of monolith to microservices, reducing latency by 40%
- Built CI/CD pipeline with GitHub Actions

## Skills
Python, AWS, Kubernetes, PostgreSQL
"""

TAILORED_BAD = """# Jane Smith

## Experience
### Principal AI Architect -- Globex Corporation (2022-2025)
- Increased revenue by 300% across 12 countries with a brand new GenAI platform
- Managed 45 engineers across three continents

## Skills
Python, AWS, Kubernetes, PostgreSQL, Terraform
"""


def test_validate_text_has_high_score_for_grounded_output():
    result = validate_text(MASTER, JOB, TAILORED_OK, label="resume")
    assert result.score >= 85
    assert result.issues == []


def test_validate_text_accepts_fixture_grounded_company_formats_and_metrics():
    master = """# Alex Rivera

## Experience
### Senior Software Engineer \u2014 Databridge Inc., Denver CO (2022 - Present)
- Reduced AWS infrastructure cost by 34% by rightsizing EC2 instances and introducing Lambda for async jobs
"""
    job = """Senior Python Engineer - Platform Team
Meridian Cloud | Remote (US)

Meridian Cloud needs Python engineers to improve AWS architecture and cost optimization.
"""
    tailored = """# Alex Rivera

## Experience
### Senior Software Engineer - Databridge Inc., Denver CO (2022 - Present)
- Cut AWS infrastructure costs by 34% through EC2 rightsizing and Lambda async processing for Meridian Cloud platform needs
"""

    result = validate_text(master, job, tailored, label="resume")

    high_risk = {issue.category for issue in result.issues if issue.severity == "high"}
    assert "company drift" not in high_risk
    assert "unsupported claim" not in high_risk


def test_validate_text_flags_drift_and_unsupported_claims():
    result = validate_text(MASTER, JOB, TAILORED_BAD, label="resume")
    categories = {issue.category for issue in result.issues}
    assert "company drift" in categories
    assert "date drift" in categories
    assert "title drift" in categories or "new proper noun" in categories
    assert any(issue.severity == "high" for issue in result.issues)
    assert result.score < 85


def test_validate_outputs_supports_resume_and_cover_letter():
    report = validate_outputs(
        master_text=MASTER,
        job_text=JOB,
        tailored_resume_text=TAILORED_OK,
        cover_letter_text="Dear Acme Corp, I am excited to apply.",
    )
    assert len(report.targets) == 2
    assert {target.label for target in report.targets} == {"resume", "cover-letter"}


def test_validate_cli_requires_target(tmp_path):
    master = tmp_path / "master.md"
    job = tmp_path / "job.txt"
    master.write_text(MASTER)
    job.write_text(JOB)

    runner = CliRunner()
    result = runner.invoke(main, ["validate", "--master", str(master), "--job", str(job)])
    assert result.exit_code != 0
    assert "--resume" in result.output or "cover-letter" in result.output


def test_validate_cli_runs_and_writes_report(tmp_path):
    master = tmp_path / "master.md"
    job = tmp_path / "job.txt"
    tailored = tmp_path / "tailored.md"
    report = tmp_path / "validation.md"
    master.write_text(MASTER)
    job.write_text(JOB)
    tailored.write_text(TAILORED_BAD)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "validate",
            "--master",
            str(master),
            "--job",
            str(job),
            "--resume",
            str(tailored),
            "--output",
            str(report),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "trust score" in result.output.lower()
    assert "Validation review needed: high risk" in result.output
    assert report.exists()
    content = report.read_text()
    assert "Validation Report" in content
    assert "Validation readiness: high risk" in content
    assert "company drift" in content


def test_validate_cli_json_output(tmp_path):
    import json

    master = tmp_path / "master.md"
    job = tmp_path / "job.txt"
    tailored = tmp_path / "tailored.md"
    master.write_text(MASTER)
    job.write_text(JOB)
    tailored.write_text(TAILORED_BAD)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "validate",
            "--master",
            str(master),
            "--job",
            str(job),
            "--resume",
            str(tailored),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema"] == "resume-engine.dashboard/v1"
    assert payload["command"] == "validate"
    assert payload["inputs"]["master"] == str(master)
    assert payload["inputs"]["job"] == str(job)
    assert payload["inputs"]["resume"] == str(tailored)
    assert payload["inputs"]["cover_letter"] is None
    assert payload["summary"]["risk_level"] == "high"
    assert payload["data"]["targets"][0]["label"] == "resume"
    assert any(
        issue["category"] == "company drift" for issue in payload["data"]["targets"][0]["issues"]
    )


def test_validate_cli_accepts_linkedin_export_source(monkeypatch, tmp_path):
    job = tmp_path / "job.txt"
    tailored = tmp_path / "tailored.md"
    report = tmp_path / "validation.md"
    job.write_text(JOB)
    tailored.write_text(TAILORED_OK)

    monkeypatch.setattr(
        "resume_engine.linkedin.parse_linkedin_export",
        lambda export_path: MASTER,
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "validate",
            "--linkedin-export",
            "linkedin.zip",
            "--job",
            str(job),
            "--resume",
            str(tailored),
            "--output",
            str(report),
        ],
    )

    assert result.exit_code == 0, result.output
    assert report.exists()


def test_validate_cli_rejects_multiple_master_sources(tmp_path):
    master = tmp_path / "master.md"
    job = tmp_path / "job.txt"
    tailored = tmp_path / "tailored.md"
    master.write_text(MASTER)
    job.write_text(JOB)
    tailored.write_text(TAILORED_OK)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "validate",
            "--master",
            str(master),
            "--linkedin-export",
            "linkedin.zip",
            "--job",
            str(job),
            "--resume",
            str(tailored),
        ],
    )

    assert result.exit_code != 0
    assert "Use only one of --master" in result.output
