"""Tests for resume_engine.scorer module."""

from __future__ import annotations

import pytest

from resume_engine.scorer import (
    ScorerResult,
    _count_action_verbs,
    _count_quantified_bullets,
    _extract_section_headings,
    _find_filler,
    _word_count,
    score_resume,
)


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------

class TestExtractSectionHeadings:
    def test_markdown_headings(self):
        text = "# Summary\n\n## Experience\n\n## Education\n"
        headings = _extract_section_headings(text)
        assert "summary" in headings
        assert "experience" in headings
        assert "education" in headings

    def test_h3_heading(self):
        text = "### Skills\n\nPython, SQL\n"
        headings = _extract_section_headings(text)
        assert "skills" in headings

    def test_underline_heading(self):
        text = "Contact\n-------\n\nname@email.com\n"
        headings = _extract_section_headings(text)
        assert "contact" in headings

    def test_empty_text(self):
        assert _extract_section_headings("") == []


class TestCountQuantifiedBullets:
    def test_percentage_bullet(self):
        text = "- Reduced costs by 30%\n- Improved performance\n"
        q, total = _count_quantified_bullets(text)
        assert q == 1
        assert total == 2

    def test_dollar_amount(self):
        text = "- Generated $500k in revenue\n- Led team\n"
        q, total = _count_quantified_bullets(text)
        assert q == 1
        assert total == 2

    def test_multiple_quantified(self):
        text = "- Cut latency by 50%\n- Managed 8 engineers\n- Reduced costs 20%\n"
        q, total = _count_quantified_bullets(text)
        assert q == 3
        assert total == 3

    def test_no_bullets(self):
        q, total = _count_quantified_bullets("No bullets here.")
        assert q == 0
        assert total == 0

    def test_asterisk_bullets(self):
        text = "* Increased revenue 15%\n* Wrote documentation\n"
        q, total = _count_quantified_bullets(text)
        assert q == 1
        assert total == 2


class TestCountActionVerbs:
    def test_strong_verbs_detected(self):
        text = "- Led a team of engineers\n- Built scalable systems\n- Reduced costs\n"
        count, found = _count_action_verbs(text)
        assert count >= 2
        assert "led" in found or "built" in found

    def test_weak_verbs_not_counted(self):
        text = "- Tried to improve things\n- Was responsible for projects\n"
        count, _ = _count_action_verbs(text)
        assert count == 0

    def test_empty_text(self):
        count, found = _count_action_verbs("")
        assert count == 0
        assert found == set()


class TestFindFiller:
    def test_responsible_for(self):
        text = "Responsible for managing the team and other tasks."
        found = _find_filler(text)
        assert any("responsible for" in f for f in found)

    def test_team_player(self):
        text = "I am a team player who thinks outside the box."
        found = _find_filler(text)
        assert len(found) >= 1

    def test_clean_text(self):
        text = "Led a team of 5 engineers to deliver a product on time."
        found = _find_filler(text)
        assert found == []


class TestWordCount:
    def test_basic(self):
        assert _word_count("hello world foo") == 3

    def test_empty(self):
        assert _word_count("") == 0


# ---------------------------------------------------------------------------
# score_resume integration tests
# ---------------------------------------------------------------------------

GOOD_RESUME = """
# Contact
Jane Doe | jane@example.com | linkedin.com/in/janedoe

# Summary
Software engineer with 8 years of experience building scalable web systems.

# Experience

## Senior Engineer -- Acme Corp (2020-Present)

- Led a team of 6 engineers to deliver a new checkout system, reducing cart abandonment by 25%
- Architected microservice migration that cut deploy time by 40%
- Mentored 3 junior engineers, improving team velocity by 20%
- Reduced infrastructure costs by $120k/year through Kubernetes optimization

## Engineer -- Startup X (2018-2020)

- Built real-time analytics pipeline processing 5M events/day
- Launched A/B testing framework adopted by 4 product teams
- Improved API response time by 60% via query optimization

# Education
B.S. Computer Science, State University, 2016

# Skills
Python, Go, Kubernetes, Postgres, AWS, Docker, CI/CD

# Projects
Open-source contributions to 3 major projects with 2k+ GitHub stars
"""


WEAK_RESUME = """
## Work History

Responsible for various tasks at several companies. Helped with projects.
Was in charge of a team. Worked on different systems and so on.
Assisted with many initiatives. Team player and self-starter.
"""


class TestScoreResume:
    def test_returns_scorer_result(self):
        result = score_resume(GOOD_RESUME)
        assert isinstance(result, ScorerResult)

    def test_good_resume_high_score(self):
        result = score_resume(GOOD_RESUME)
        assert result.total >= 60, f"Expected score >= 60, got {result.total}"

    def test_weak_resume_lower_score(self):
        good = score_resume(GOOD_RESUME)
        weak = score_resume(WEAK_RESUME)
        assert good.total > weak.total, "Good resume should score higher than weak resume"

    def test_section_completeness(self):
        result = score_resume(GOOD_RESUME)
        sections_dim = next(d for d in result.dimensions if d.name == "Section Completeness")
        assert sections_dim.score >= 15

    def test_quantified_achievements(self):
        result = score_resume(GOOD_RESUME)
        quant_dim = next(d for d in result.dimensions if d.name == "Quantified Achievements")
        assert quant_dim.score >= 15

    def test_action_verb_usage(self):
        result = score_resume(GOOD_RESUME)
        verb_dim = next(d for d in result.dimensions if d.name == "Action Verb Usage")
        assert verb_dim.score >= 10

    def test_weak_resume_filler_penalty(self):
        result = score_resume(WEAK_RESUME)
        filler_dim = next(d for d in result.dimensions if d.name == "Filler / Weak Language")
        assert filler_dim.score < 15

    def test_total_is_sum_of_dimensions(self):
        result = score_resume(GOOD_RESUME)
        assert result.total == sum(d.score for d in result.dimensions)

    def test_max_score_100(self):
        result = score_resume(GOOD_RESUME)
        assert sum(d.max_score for d in result.dimensions) == 100

    def test_word_count_populated(self):
        result = score_resume(GOOD_RESUME)
        assert result.word_count > 100

    def test_bullet_count_populated(self):
        result = score_resume(GOOD_RESUME)
        assert result.bullet_count > 0

    def test_empty_resume(self):
        result = score_resume("")
        assert result.total >= 0
        assert result.total <= 100

    def test_found_sections_populated(self):
        result = score_resume(GOOD_RESUME)
        assert len(result.found_sections) >= 3

    def test_suggestions_on_weak_resume(self):
        result = score_resume(WEAK_RESUME)
        all_sug = [s for d in result.dimensions for s in d.suggestions]
        assert len(all_sug) >= 1


# ---------------------------------------------------------------------------
# CLI integration (no LLM)
# ---------------------------------------------------------------------------

class TestScoreCLI:
    def test_score_command_help(self, tmp_path):
        """score --help returns zero exit code."""
        import subprocess, sys
        result = subprocess.run(
            [sys.executable, "-m", "resume_engine.cli", "score", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/tr-mini/Desktop/resume-engine",
        )
        assert result.returncode == 0
        assert "quality" in result.stdout.lower() or "score" in result.stdout.lower()

    def test_score_command_runs(self, tmp_path):
        """score command runs on a temp file."""
        import subprocess, sys
        resume = tmp_path / "resume.md"
        resume.write_text(GOOD_RESUME)
        result = subprocess.run(
            [sys.executable, "-m", "resume_engine.cli", "score", str(resume)],
            capture_output=True,
            text=True,
            cwd="/Users/tr-mini/Desktop/resume-engine",
        )
        assert result.returncode == 0
        assert "/100" in result.stdout

    def test_score_brief_flag(self, tmp_path):
        """--brief flag produces shorter output without table."""
        import subprocess, sys
        resume = tmp_path / "resume.md"
        resume.write_text(GOOD_RESUME)
        result = subprocess.run(
            [sys.executable, "-m", "resume_engine.cli", "score", str(resume), "--brief"],
            capture_output=True,
            text=True,
            cwd="/Users/tr-mini/Desktop/resume-engine",
        )
        assert result.returncode == 0
        assert "/100" in result.stdout
