"""Tests for resume_engine.interview module."""

from __future__ import annotations

from unittest.mock import patch

from resume_engine.interview import (
    InterviewPrepResult,
    _parse_followups,
    _parse_questions,
    generate_interview_prep,
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

SAMPLE_QUESTIONS_RAW = """1. Tell me about a time you led a major technical migration.
   Category: Behavioral
   STAR Framework: Situation: legacy monolith causing scaling issues | Task: migrate to microservices | Action: Led team, defined service boundaries, built migration plan | Result: 40% latency reduction at Acme Corp

2. How do you approach Kubernetes cluster optimization?
   Category: Technical
   STAR Framework: Explain experience managing Kubernetes at Acme Corp, describe specific optimizations, reference AWS EKS usage

3. Why are you interested in this platform role?
   Category: Culture Fit
   STAR Framework: Connect Acme Corp microservices work to platform focus, highlight leadership interest

4. Walk me through the CI/CD pipeline you built at Acme Corp.
   Category: Resume Deep-Dive
   STAR Framework: Situation: no automated pipeline | Task: build reliable CI/CD | Action: implemented GitHub Actions workflows | Result: faster deploy cycle
"""

SAMPLE_FOLLOWUPS_RAW = """1. You left Startup X after 3 years -- what drove that decision?
   Probing: Voluntary departure or performance issue, career growth motivation

2. Your resume shows a title jump from Software Engineer to Senior in one move -- how did that happen?
   Probing: Assessing if the promotion was earned or inflated
"""


class TestParseQuestions:
    def test_parses_basic_structure(self):
        questions = _parse_questions(SAMPLE_QUESTIONS_RAW)
        assert len(questions) == 4

    def test_question_numbers_correct(self):
        questions = _parse_questions(SAMPLE_QUESTIONS_RAW)
        assert questions[0].number == 1
        assert questions[3].number == 4

    def test_question_text_extracted(self):
        questions = _parse_questions(SAMPLE_QUESTIONS_RAW)
        assert (
            "migration" in questions[0].question.lower() or "led" in questions[0].question.lower()
        )

    def test_categories_extracted(self):
        questions = _parse_questions(SAMPLE_QUESTIONS_RAW)
        categories = [q.category for q in questions]
        assert "Behavioral" in categories
        assert "Technical" in categories
        assert "Culture Fit" in categories
        assert "Resume Deep-Dive" in categories

    def test_star_framework_extracted(self):
        questions = _parse_questions(SAMPLE_QUESTIONS_RAW)
        # First question has a detailed STAR framework
        assert questions[0].framework != ""
        assert "latency" in questions[0].framework or "Acme" in questions[0].framework

    def test_empty_input_returns_empty_list(self):
        assert _parse_questions("") == []

    def test_partial_structure_still_parsed(self):
        partial = "1. What is your experience with Python?\n   Category: Technical\n"
        questions = _parse_questions(partial)
        assert len(questions) >= 1
        assert questions[0].category == "Technical"


class TestParseFollowups:
    def test_parses_followup_count(self):
        followups = _parse_followups(SAMPLE_FOLLOWUPS_RAW)
        assert len(followups) == 2

    def test_followup_numbers(self):
        followups = _parse_followups(SAMPLE_FOLLOWUPS_RAW)
        assert followups[0].number == 1
        assert followups[1].number == 2

    def test_probing_extracted(self):
        followups = _parse_followups(SAMPLE_FOLLOWUPS_RAW)
        assert followups[0].probing != ""
        assert (
            "departure" in followups[0].probing.lower()
            or "voluntary" in followups[0].probing.lower()
        )

    def test_empty_input_returns_empty(self):
        assert _parse_followups("") == []


class TestGenerateInterviewPrep:
    def test_calls_llm_with_resume_and_job(self):
        with patch("resume_engine.interview.complete", return_value=SAMPLE_QUESTIONS_RAW) as mock:
            generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB, model="openai")

        mock.assert_called_once()
        prompt = mock.call_args[0][0]
        assert "Jane Smith" in prompt
        assert "Senior Backend Engineer" in prompt

    def test_passes_count_to_prompt(self):
        with patch("resume_engine.interview.complete", return_value=SAMPLE_QUESTIONS_RAW) as mock:
            generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB, model="openai", count=15)

        prompt = mock.call_args[0][0]
        assert "15" in prompt

    def test_returns_interviewprepresult(self):
        with patch("resume_engine.interview.complete", return_value=SAMPLE_QUESTIONS_RAW):
            result = generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB)

        assert isinstance(result, InterviewPrepResult)
        assert isinstance(result.questions, list)

    def test_no_followups_by_default(self):
        with patch("resume_engine.interview.complete", return_value=SAMPLE_QUESTIONS_RAW) as mock:
            result = generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB)

        # Should only call LLM once (no followups call)
        assert mock.call_count == 1
        assert result.followups == []

    def test_with_followups_calls_llm_twice(self):
        call_responses = [SAMPLE_QUESTIONS_RAW, SAMPLE_FOLLOWUPS_RAW]
        with patch("resume_engine.interview.complete", side_effect=call_responses) as mock:
            result = generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB, with_followups=True)

        assert mock.call_count == 2
        assert len(result.followups) >= 1

    def test_raw_output_preserved(self):
        with patch("resume_engine.interview.complete", return_value=SAMPLE_QUESTIONS_RAW):
            result = generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB)

        assert result.raw_questions == SAMPLE_QUESTIONS_RAW

    def test_model_forwarded(self):
        with patch("resume_engine.interview.complete", return_value=SAMPLE_QUESTIONS_RAW) as mock:
            generate_interview_prep(SAMPLE_RESUME, SAMPLE_JOB, model="anthropic")

        call_kwargs = mock.call_args
        assert "anthropic" in str(call_kwargs)


class TestInterviewCLI:
    def test_interview_command_exists(self):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["interview", "--help"])
        assert result.exit_code == 0
        assert "interview" in result.output.lower()
        assert "STAR" in result.output

    def test_requires_job_or_job_url(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)

        runner = CliRunner()
        result = runner.invoke(main, ["interview", "--master", str(resume_file)])
        assert result.exit_code != 0
        assert "job" in result.output.lower()

    def test_basic_invocation(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)

        with patch(
            "resume_engine.interview.generate_interview_prep",
            return_value=InterviewPrepResult(
                questions=_parse_questions(SAMPLE_QUESTIONS_RAW),
                raw_questions=SAMPLE_QUESTIONS_RAW,
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "interview",
                    "--master",
                    str(resume_file),
                    "--job",
                    str(job_file),
                    "--model",
                    "openai",
                ],
            )

        assert result.exit_code == 0, result.output
        assert "Interview Questions" in result.output

    def test_output_file_written(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)
        out_file = tmp_path / "prep.md"

        with patch(
            "resume_engine.interview.generate_interview_prep",
            return_value=InterviewPrepResult(
                questions=_parse_questions(SAMPLE_QUESTIONS_RAW),
                raw_questions=SAMPLE_QUESTIONS_RAW,
            ),
        ):
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "interview",
                    "--master",
                    str(resume_file),
                    "--job",
                    str(job_file),
                    "--output",
                    str(out_file),
                    "--model",
                    "openai",
                ],
            )

        assert result.exit_code == 0, result.output
        assert out_file.exists()
        content = out_file.read_text()
        assert "Interview Prep" in content

    def test_with_followups_flag(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)

        prep_result = InterviewPrepResult(
            questions=_parse_questions(SAMPLE_QUESTIONS_RAW),
            followups=_parse_followups(SAMPLE_FOLLOWUPS_RAW),
            raw_questions=SAMPLE_QUESTIONS_RAW,
            raw_followups=SAMPLE_FOLLOWUPS_RAW,
        )

        with patch(
            "resume_engine.interview.generate_interview_prep",
            return_value=prep_result,
        ) as mock_gen:
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "interview",
                    "--master",
                    str(resume_file),
                    "--job",
                    str(job_file),
                    "--with-followups",
                    "--model",
                    "openai",
                ],
            )

        assert result.exit_code == 0, result.output
        # with_followups=True should be passed to generate_interview_prep
        call_kwargs = mock_gen.call_args
        assert call_kwargs[1].get("with_followups") is True or True in call_kwargs[0]

    def test_count_option_forwarded(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        job_file = tmp_path / "job.txt"
        job_file.write_text(SAMPLE_JOB)

        with patch(
            "resume_engine.interview.generate_interview_prep",
            return_value=InterviewPrepResult(raw_questions="ok"),
        ) as mock_gen:
            runner = CliRunner()
            runner.invoke(
                main,
                [
                    "interview",
                    "--master",
                    str(resume_file),
                    "--job",
                    str(job_file),
                    "--count",
                    "15",
                    "--model",
                    "openai",
                ],
            )

        call_kwargs = mock_gen.call_args
        assert call_kwargs[1].get("count") == 15 or 15 in call_kwargs[0]
