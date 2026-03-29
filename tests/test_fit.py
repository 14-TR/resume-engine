"""Tests for resume_engine.fit module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from resume_engine.fit import (
    FitDimension,
    FitResult,
    _parse_bullets,
    _parse_recommendation,
    _parse_score,
    _parse_verdict,
    _verdict_from_score,
    assess_fit,
)


SAMPLE_RESUME = """# Jane Smith
jane@example.com | (555) 555-1234

## Summary
Senior software engineer with 6 years of experience building distributed systems.

## Experience

### Senior Software Engineer -- Acme Corp (2021-2024)
- Led migration of monolith to microservices, reducing latency by 40%
- Managed team of 4 engineers
- Built CI/CD pipeline with GitHub Actions

### Software Engineer -- Startup X (2018-2021)
- Built Python REST APIs serving 1M requests/day
- Reduced infrastructure costs by 25%

## Education
B.S. Computer Science, State University, 2018

## Skills
Python, Go, AWS, Kubernetes, PostgreSQL, Docker
"""

SAMPLE_JOB = """Senior Backend Engineer

We are looking for a Senior Backend Engineer to join our platform team.

Requirements:
- 5+ years Python experience
- Kubernetes and AWS expertise
- Experience with microservices architecture
- Strong communication and collaboration skills
- Experience leading small teams

Nice to have:
- Go experience
- PostgreSQL optimization
"""

SAMPLE_LLM_RESPONSE = """1. REQUIRED SKILLS COVERAGE (25 pts)
   Jane has Python, Kubernetes, AWS, microservices all from job requirements.
   Score: 22/25

2. SENIORITY AND LEVEL MATCH (20 pts)
   Senior title at Acme Corp aligns well with Senior Backend Engineer role.
   Score: 18/20

3. INDUSTRY AND DOMAIN FIT (15 pts)
   Platform engineering focus matches candidate experience.
   Score: 12/15

4. OVERALL ASSESSMENT (20 pts)
   Strong technical profile, good trajectory for this role.
   Score: 17/20

STRENGTHS:
- Python, Kubernetes, AWS match all core requirements directly
- Led microservices migration at Acme Corp aligns with role scope
- Team management experience meets the small-team leadership requirement

GAPS:
- No explicit platform engineering role title in history
- 6 years total vs 5+ required is close but not a strong buffer

VERDICT: Strong technical match with minor experience gap in platform focus.

RECOMMENDATION: Apply
"""

SAMPLE_LLM_RESPONSE_SKIP = """1. REQUIRED SKILLS COVERAGE (25 pts)
   Missing most required skills.
   Score: 5/25

2. SENIORITY AND LEVEL MATCH (20 pts)
   Junior experience for a senior role.
   Score: 4/20

3. INDUSTRY AND DOMAIN FIT (15 pts)
   Different domain entirely.
   Score: 3/15

4. OVERALL ASSESSMENT (20 pts)
   Significant gaps across the board.
   Score: 5/20

STRENGTHS:
- Some Python experience

GAPS:
- Missing Kubernetes and AWS experience required
- Only 2 years experience vs 5+ required

VERDICT: Significant gap between candidate profile and job requirements.

RECOMMENDATION: Skip
"""


class TestParseScore:
    def test_extracts_score_correctly(self):
        text = "REQUIRED SKILLS COVERAGE (25 pts)\n   Score: 22/25"
        assert _parse_score(text, "REQUIRED SKILLS COVERAGE", 25) == 22

    def test_caps_at_max(self):
        text = "REQUIRED SKILLS COVERAGE\nScore: 30/25"
        assert _parse_score(text, "REQUIRED SKILLS COVERAGE", 25) == 25

    def test_returns_zero_when_not_found(self):
        assert _parse_score("no score here", "SENIORITY", 20) == 0

    def test_extracts_seniority_score(self):
        assert _parse_score(SAMPLE_LLM_RESPONSE, "SENIORITY AND LEVEL MATCH", 20) == 18

    def test_extracts_domain_score(self):
        assert _parse_score(SAMPLE_LLM_RESPONSE, "INDUSTRY AND DOMAIN FIT", 15) == 12

    def test_extracts_overall_score(self):
        assert _parse_score(SAMPLE_LLM_RESPONSE, "OVERALL ASSESSMENT", 20) == 17


class TestParseBullets:
    def test_extracts_strengths(self):
        bullets = _parse_bullets(SAMPLE_LLM_RESPONSE, "STRENGTHS")
        assert len(bullets) == 3
        assert any("Python" in b or "Kubernetes" in b for b in bullets)

    def test_extracts_gaps(self):
        bullets = _parse_bullets(SAMPLE_LLM_RESPONSE, "GAPS")
        assert len(bullets) == 2
        assert any("platform" in b.lower() or "experience" in b.lower() for b in bullets)

    def test_returns_empty_when_section_missing(self):
        assert _parse_bullets("no bullets here", "STRENGTHS") == []

    def test_strips_bullet_markers(self):
        bullets = _parse_bullets(SAMPLE_LLM_RESPONSE, "STRENGTHS")
        for b in bullets:
            assert not b.startswith("-")
            assert not b.startswith("*")


class TestParseVerdict:
    def test_extracts_verdict(self):
        v = _parse_verdict(SAMPLE_LLM_RESPONSE)
        assert "match" in v.lower() or "strong" in v.lower()

    def test_returns_empty_when_missing(self):
        assert _parse_verdict("no verdict here") == ""


class TestParseRecommendation:
    def test_apply(self):
        assert _parse_recommendation(SAMPLE_LLM_RESPONSE) == "Apply"

    def test_skip(self):
        assert _parse_recommendation(SAMPLE_LLM_RESPONSE_SKIP) == "Skip"

    def test_apply_with_caution(self):
        text = "RECOMMENDATION: Apply with caution"
        assert _parse_recommendation(text) == "Apply with caution"

    def test_fuzzy_fallback_apply(self):
        assert _parse_recommendation("you should apply for this") == "Apply"

    def test_fuzzy_fallback_skip(self):
        assert _parse_recommendation("I would skip this one") == "Skip"


class TestVerdictFromScore:
    def test_strong_fit(self):
        assert _verdict_from_score(85) == "Strong fit"

    def test_moderate_fit(self):
        assert _verdict_from_score(70) == "Moderate fit"

    def test_stretch_role(self):
        assert _verdict_from_score(50) == "Stretch role"

    def test_poor_fit(self):
        assert _verdict_from_score(30) == "Poor fit"

    def test_boundary_80(self):
        assert _verdict_from_score(80) == "Strong fit"

    def test_boundary_65(self):
        assert _verdict_from_score(65) == "Moderate fit"

    def test_boundary_45(self):
        assert _verdict_from_score(45) == "Stretch role"


class TestFitDimension:
    def test_pct_calculation(self):
        dim = FitDimension(name="Test", score=15, max_score=20)
        assert dim.pct == 75

    def test_pct_zero_max(self):
        dim = FitDimension(name="Test", score=0, max_score=0)
        assert dim.pct == 0


class TestAssessFit:
    def test_returns_fit_result(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert isinstance(result, FitResult)

    def test_total_in_range(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert 0 <= result.total <= 100

    def test_has_five_dimensions(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert len(result.dimensions) == 5

    def test_recommendation_apply(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert result.recommendation == "Apply"

    def test_recommendation_skip(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE_SKIP):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert result.recommendation == "Skip"

    def test_ats_score_populated(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert 0 <= result.ats_score <= 100

    def test_strengths_populated(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert len(result.strengths) >= 1

    def test_gaps_populated(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert len(result.gaps) >= 1

    def test_raw_analysis_preserved(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert result.raw_analysis == SAMPLE_LLM_RESPONSE

    def test_model_forwarded_to_llm(self):
        with patch("resume_engine.fit.complete", return_value=SAMPLE_LLM_RESPONSE) as mock:
            assess_fit(SAMPLE_RESUME, SAMPLE_JOB, model="openai")
        assert mock.call_args[1].get("model") == "openai" or (len(mock.call_args[0]) > 1 and mock.call_args[0][1] == "openai")

    def test_total_never_exceeds_100(self):
        # Simulate inflated scores
        inflated = SAMPLE_LLM_RESPONSE.replace("22/25", "25/25").replace("18/20", "20/20").replace("12/15", "15/15").replace("17/20", "20/20")
        with patch("resume_engine.fit.complete", return_value=inflated):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        assert result.total <= 100

    def test_fallback_when_no_scores_parsed(self):
        """If LLM returns garbage, fallback scores are applied."""
        garbage = "I cannot evaluate this."
        with patch("resume_engine.fit.complete", return_value=garbage):
            result = assess_fit(SAMPLE_RESUME, SAMPLE_JOB)
        # Should not blow up; total should be non-zero (ATS contributes)
        assert isinstance(result.total, int)
        assert result.total >= 0


class TestFitCLI:
    def test_fit_command_exists(self):
        from click.testing import CliRunner
        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["fit", "--help"])
        assert result.exit_code == 0
        assert "fit" in result.output.lower()
        assert "score" in result.output.lower() or "apply" in result.output.lower()

    def test_requires_job_or_job_url(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)

        runner = CliRunner()
        result = runner.invoke(main, ["fit", "--master", str(resume_file)])
        assert result.exit_code != 0
        assert "job" in result.output.lower()

    def test_basic_invocation(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)

        mock_result = FitResult(
            total=78,
            dimensions=[
                FitDimension("ATS Keyword Match", 14, 20),
                FitDimension("Required Skills Coverage", 20, 25),
                FitDimension("Seniority / Level Match", 16, 20),
                FitDimension("Industry / Domain Fit", 12, 15),
                FitDimension("Overall Assessment", 16, 20),
            ],
            verdict="Strong fit",
            recommendation="Apply",
            strengths=["Python and Kubernetes match core requirements"],
            gaps=["Minor gap in platform engineering history"],
            raw_analysis=SAMPLE_LLM_RESPONSE,
            ats_score=72,
        )

        with patch("resume_engine.fit.assess_fit", return_value=mock_result):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["fit", "--master", str(resume_file), "--job", str(job_file), "--model", "openai"],
            )

        assert result.exit_code == 0, result.output
        assert "78" in result.output
        assert "Apply" in result.output

    def test_brief_mode(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)

        mock_result = FitResult(
            total=55,
            dimensions=[
                FitDimension("ATS Keyword Match", 10, 20),
                FitDimension("Required Skills Coverage", 14, 25),
                FitDimension("Seniority / Level Match", 10, 20),
                FitDimension("Industry / Domain Fit", 8, 15),
                FitDimension("Overall Assessment", 13, 20),
            ],
            verdict="Stretch role",
            recommendation="Apply with caution",
            strengths=[],
            gaps=[],
            raw_analysis="",
            ats_score=42,
        )

        with patch("resume_engine.fit.assess_fit", return_value=mock_result):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["fit", "--master", str(resume_file), "--job", str(job_file), "--brief"],
            )

        assert result.exit_code == 0, result.output
        assert "55" in result.output

    def test_output_file_written(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)
        out_file = tmp_path / "fit-report.md"

        mock_result = FitResult(
            total=78,
            dimensions=[
                FitDimension("ATS Keyword Match", 14, 20),
                FitDimension("Required Skills Coverage", 20, 25),
                FitDimension("Seniority / Level Match", 16, 20),
                FitDimension("Industry / Domain Fit", 12, 15),
                FitDimension("Overall Assessment", 16, 20),
            ],
            verdict="Strong fit",
            recommendation="Apply",
            strengths=["Kubernetes matches requirements"],
            gaps=["No platform role history"],
            raw_analysis=SAMPLE_LLM_RESPONSE,
            ats_score=72,
        )

        with patch("resume_engine.fit.assess_fit", return_value=mock_result):
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "fit",
                    "--master", str(resume_file),
                    "--job", str(job_file),
                    "--output", str(out_file),
                ],
            )

        assert result.exit_code == 0, result.output
        assert out_file.exists()
        content = out_file.read_text()
        assert "Job Fit Report" in content
        assert "78" in content
        assert "Apply" in content
        assert "Kubernetes" in content
