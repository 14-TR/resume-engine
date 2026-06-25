"""Tests for grounded output validation."""

from pathlib import Path

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

TAILORED_GROUNDED_REWRITE = """# Alex Rivera

## Experience
### Senior Software Engineer -- Databridge Inc., Denver CO (2022 - Present)
- Collaborated with platform peers to improve the public REST API, keeping the 50+ endpoints documented and client-ready
- Designed AWS cost optimizations that preserved the previously achieved 34% infrastructure reduction
- Developed integration test coverage improvements that sustained the 38% to 82% increase across core services
- Used Python and FastAPI to build backend services for billing and tenant lifecycle management
"""

COVER_LETTER_GROUNDED = """# Cover Letter for Senior Python Engineer Position at Meridian Cloud

Dear Hiring Manager,

I am writing to express my interest in the Senior Python Engineer position at Meridian Cloud.
At Databridge Inc., I led the migration of our monolithic Django application to microservices and built a real-time data ingestion pipeline processing 4M events/day with Kafka and Python workers.
I also reduced AWS infrastructure costs by 34% and mentored junior engineers through architecture reviews.

Best regards,

Alex Rivera
"""


def test_validate_text_has_high_score_for_grounded_output():
    result = validate_text(MASTER, JOB, TAILORED_OK, label="resume")
    assert result.score >= 85
    assert result.issues == []


def test_validate_text_flags_drift_and_unsupported_claims():
    result = validate_text(MASTER, JOB, TAILORED_BAD, label="resume")
    categories = {issue.category for issue in result.issues}
    assert "company drift" in categories
    assert "date drift" in categories
    assert "title drift" in categories or "new proper noun" in categories
    assert any(issue.severity == "high" for issue in result.issues)
    assert result.score < 85


def test_validate_text_keeps_grounded_metrics_and_sentence_start_verbs_supported():
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    result = validate_text(
        master_text=(examples_dir / "master-resume.md").read_text(),
        job_text=(examples_dir / "job-posting.txt").read_text(),
        output_text=TAILORED_GROUNDED_REWRITE,
        label="resume",
    )
    categories = {issue.category for issue in result.issues}
    assert "new proper noun" not in categories
    assert "unsupported claim" not in categories


def test_validate_text_does_not_treat_generic_restful_api_phrase_as_new_proper_noun():
    result = validate_text(
        master_text="Built backend services.\n",
        job_text="Need someone who can ship APIs.\n",
        output_text="- Built RESTful APIs for internal platforms.\n",
        label="resume",
    )
    evidence = {issue.evidence for issue in result.issues}
    assert "RESTful APIs" not in evidence


def test_validate_text_does_not_treat_generic_rest_api_phrases_as_unsupported_skills():
    for phrase in ("REST APIs", "RESTful APIs"):
        result = validate_text(
            master_text="Built backend services.\n",
            job_text="Need someone who can ship APIs.\n",
            output_text=f"- Built {phrase} for internal platforms.\n",
            label="resume",
        )
        unsupported_skills = {
            issue.evidence for issue in result.issues if issue.category == "unsupported skill"
        }
        assert "rest" not in unsupported_skills


def test_validate_text_still_flags_concrete_api_technologies_as_unsupported_skills():
    result = validate_text(
        master_text="Built backend services.\n",
        job_text="Need someone who can ship APIs.\n",
        output_text="- Built GraphQL APIs for internal platforms.\n",
        label="resume",
    )
    unsupported_skills = {
        issue.evidence for issue in result.issues if issue.category == "unsupported skill"
    }
    assert "graphql" in unsupported_skills


def test_validate_text_keeps_grounded_cover_letter_companies_titles_and_metrics_supported():
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    result = validate_text(
        master_text=(examples_dir / "master-resume.md").read_text(),
        job_text=(examples_dir / "job-posting.txt").read_text(),
        output_text=COVER_LETTER_GROUNDED,
        label="cover-letter",
    )
    categories = {issue.category for issue in result.issues}
    assert "company drift" not in categories
    assert "title drift" not in categories
    assert "new proper noun" not in categories
    assert "unsupported claim" not in categories


def test_validate_text_keeps_bundled_tailored_example_out_of_medium_risk():
    repo_root = Path(__file__).resolve().parents[1]
    result = validate_text(
        master_text=(repo_root / "examples" / "master-resume.md").read_text(),
        job_text=(repo_root / "examples" / "job-posting.txt").read_text(),
        output_text=(repo_root / "tailored-resume.md").read_text(),
        label="resume",
    )
    evidence = {issue.evidence for issue in result.issues}
    assert "Optimized AWS" not in evidence
    assert "Over" not in evidence
    assert result.score >= 96


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
    assert report.exists()
    content = report.read_text()
    assert "Validation Report" in content
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
    assert payload["data"]["targets"][0]["label"] == "resume"
    assert any(
        issue["category"] == "company drift" for issue in payload["data"]["targets"][0]["issues"]
    )
