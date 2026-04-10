"""Tests for resume_engine.cover_scorer module."""

from __future__ import annotations

import json

from resume_engine.cover_scorer import (
    CoverDimension,
    CoverScorerResult,
    _check_generic_opener,
    _count_specificity,
    _count_value_verbs,
    _detect_company_name,
    _detect_role_name,
    _find_filler,
    _first_sentence,
    _word_count,
    score_cover_letter,
)

# ---------------------------------------------------------------------------
# Sample cover letters
# ---------------------------------------------------------------------------

STRONG_COVER = """Dear Hiring Team,

When I shipped the payment processing service at FinTech Inc., I reduced transaction
failures by 43% and scaled throughput to 2 million requests per day. That same focus
on reliability is exactly what the Senior Backend Engineer role at Acme Corp demands.

At FinTech Inc., I led a team of 6 engineers migrating our monolithic payment system
to microservices on AWS. We cut infrastructure costs by $120k per year and reduced P99
latency from 800ms to 95ms. I architected the core Go services, owned the Kubernetes
deployment pipeline, and defined the SLAs still in use today.

I am drawn to Acme's engineering culture and open-source work on distributed tracing.
I have contributed to OpenTelemetry and bring practical distributed systems depth.

Looking forward to talking with your team.

Jane Smith
"""

WEAK_COVER = """Dear Hiring Manager,

I am writing to express my interest in this position. I am a highly motivated and
passionate team player who is detail-oriented and a self-starter. I believe I would
be a great fit for this role.

I am responsible for various tasks at my current job including working on different
projects. I have been assisting my manager with several initiatives and helped with
the team's various goals.

I am very excited to learn and grow in this opportunity. This role would allow me to
develop my skills and gain experience. I strongly believe that I would make a great
addition to your team.

Please do not hesitate to contact me. Thank you for your time and consideration.

Sincerely,
John Doe
"""

MEDIUM_COVER = """Dear Hiring Manager,

I am a backend engineer with 5 years of experience building distributed systems.
I am applying for the Senior Software Engineer position.

In my current role at TechCorp, I built several Python microservices that improved
system reliability. I worked on reducing latency and helped grow the platform's
user base.

I am excited about this opportunity and believe I could contribute to your team.
Please consider my application.

Best regards,
Alex
"""


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestWordCount:
    def test_basic(self):
        assert _word_count("hello world") == 2

    def test_empty(self):
        assert _word_count("") == 0

    def test_multiline(self):
        assert _word_count("line one\nline two") == 4


class TestFirstSentence:
    def test_period_terminated(self):
        text = "I built a great system. And then I did more things."
        result = _first_sentence(text)
        assert "I built a great system" in result

    def test_with_salutation(self):
        text = "Dear Hiring Manager,\n\nI built a system. More stuff."
        result = _first_sentence(text)
        # Should skip the salutation
        assert result  # non-empty

    def test_empty(self):
        result = _first_sentence("")
        assert result == ""


class TestGenericOpener:
    def test_i_am_writing(self):
        assert _check_generic_opener("I am writing to express my interest") is True

    def test_i_am_applying(self):
        assert _check_generic_opener("I am applying for this position") is True

    def test_i_am_excited(self):
        assert _check_generic_opener("I am excited to apply") is True

    def test_my_name_is(self):
        assert _check_generic_opener("My name is Jane Smith") is True

    def test_strong_opener(self):
        assert _check_generic_opener("When I shipped the API, I reduced latency by 40%.") is False

    def test_specific_claim(self):
        assert (
            _check_generic_opener("I built the payment system that processes 1M requests daily.")
            is False
        )


class TestCountSpecificity:
    def test_percentage(self):
        text = "Reduced failures by 43% and saved $120k."
        assert _count_specificity(text) >= 2

    def test_dollar_amount(self):
        assert _count_specificity("We saved $50,000 per year.") >= 1

    def test_team_size(self):
        assert _count_specificity("Led a team of 6 engineers.") >= 1

    def test_no_metrics(self):
        assert _count_specificity("I worked on various projects.") == 0

    def test_multiplier(self):
        assert _count_specificity("Increased throughput 10x.") >= 1


class TestCountValueVerbs:
    def test_built(self):
        assert _count_value_verbs("I built a system.") >= 1

    def test_led(self):
        assert _count_value_verbs("I led the team.") >= 1

    def test_reduced(self):
        assert _count_value_verbs("I reduced latency.") >= 1

    def test_no_verbs(self):
        assert _count_value_verbs("I am interested in the role.") == 0

    def test_multiple_verbs(self):
        text = "I built, launched, and scaled the system. I led the team and reduced costs."
        assert _count_value_verbs(text) >= 4


class TestDetectCompanyName:
    def test_at_company(self):
        assert _detect_company_name("I worked at Acme Corp.") is True

    def test_no_company(self):
        assert _detect_company_name("I am interested in this role.") is False

    def test_company_team(self):
        assert _detect_company_name("Acme's engineering team is world-class.") is True


class TestDetectRoleName:
    def test_senior_backend(self):
        assert _detect_role_name("I am applying for the Senior Backend Engineer role.") is True

    def test_software_engineer(self):
        assert _detect_role_name("The Software Engineer position interests me.") is True

    def test_product_manager(self):
        assert _detect_role_name("I want to become a Product Manager.") is True

    def test_no_role(self):
        assert _detect_role_name("I want to join your team.") is False


class TestFindFiller:
    def test_team_player(self):
        result = _find_filler("I am a team player and self-starter.")
        assert len(result) >= 1

    def test_responsible_for(self):
        result = _find_filler("I was responsible for the project.")
        assert any("responsible for" in r for r in result)

    def test_no_filler(self):
        result = _find_filler("I built the system and reduced latency by 40%.")
        assert len(result) == 0

    def test_multiple_filler(self):
        text = "I am a passionate team player and detail-oriented self-starter."
        result = _find_filler(text)
        assert len(result) >= 2


# ---------------------------------------------------------------------------
# Integration tests: score_cover_letter
# ---------------------------------------------------------------------------


class TestScoreCoverLetter:
    def test_returns_result_type(self):
        result = score_cover_letter(STRONG_COVER)
        assert isinstance(result, CoverScorerResult)

    def test_score_range(self):
        result = score_cover_letter(STRONG_COVER)
        assert 0 <= result.total <= 100

    def test_five_dimensions(self):
        result = score_cover_letter(STRONG_COVER)
        assert len(result.dimensions) == 5

    def test_dimension_types(self):
        result = score_cover_letter(STRONG_COVER)
        for dim in result.dimensions:
            assert isinstance(dim, CoverDimension)
            assert 0 <= dim.score <= dim.max_score

    def test_dimension_max_scores(self):
        result = score_cover_letter(STRONG_COVER)
        maxes = {d.name: d.max_score for d in result.dimensions}
        assert maxes["Opening Hook"] == 20
        assert maxes["Company / Role Specificity"] == 25
        assert maxes["Value Proposition"] == 25
        assert maxes["Length & Conciseness"] == 15
        assert maxes["Filler / Weak Language"] == 15

    def test_total_equals_sum(self):
        result = score_cover_letter(STRONG_COVER)
        assert result.total == sum(d.score for d in result.dimensions)

    def test_word_count(self):
        result = score_cover_letter(STRONG_COVER)
        assert result.word_count > 0

    def test_strong_cover_scores_high(self):
        result = score_cover_letter(STRONG_COVER)
        assert result.total >= 65, f"Strong cover scored {result.total}, expected >= 65"

    def test_weak_cover_scores_low(self):
        result = score_cover_letter(WEAK_COVER)
        assert result.total <= 40, f"Weak cover scored {result.total}, expected <= 40"

    def test_strong_beats_weak(self):
        strong = score_cover_letter(STRONG_COVER)
        weak = score_cover_letter(WEAK_COVER)
        assert strong.total > weak.total

    def test_weak_has_filler(self):
        result = score_cover_letter(WEAK_COVER)
        assert len(result.filler_matches) > 0

    def test_strong_has_value_verbs(self):
        result = score_cover_letter(STRONG_COVER)
        assert result.value_verb_count > 0

    def test_strong_has_metrics(self):
        result = score_cover_letter(STRONG_COVER)
        assert result.specificity_count > 0

    def test_weak_generic_opener(self):
        result = score_cover_letter(WEAK_COVER)
        assert result.generic_opener is True

    def test_strong_not_generic_opener(self):
        result = score_cover_letter(STRONG_COVER)
        assert result.generic_opener is False

    def test_empty_cover_letter(self):
        result = score_cover_letter("")
        assert isinstance(result, CoverScorerResult)
        assert result.total >= 0

    def test_pct_property(self):
        dim = CoverDimension(name="Test", score=15, max_score=20)
        assert dim.pct == 75

    def test_pct_zero_max(self):
        dim = CoverDimension(name="Test", score=0, max_score=0)
        assert dim.pct == 0

    def test_suggestions_are_strings(self):
        result = score_cover_letter(WEAK_COVER)
        for dim in result.dimensions:
            for sug in dim.suggestions:
                assert isinstance(sug, str)
                assert len(sug) > 0

    def test_medium_cover_mid_range(self):
        result = score_cover_letter(MEDIUM_COVER)
        assert 20 <= result.total <= 80, f"Medium cover scored {result.total}, expected 20-80"

    def test_no_em_dashes_in_suggestions(self):
        """Suggestions must not contain em dashes."""
        for cover in [STRONG_COVER, WEAK_COVER, MEDIUM_COVER]:
            result = score_cover_letter(cover)
            for dim in result.dimensions:
                for sug in dim.suggestions:
                    assert "\u2014" not in sug, f"Em dash found in suggestion: {sug!r}"

    def test_has_company_name_attribute(self):
        result = score_cover_letter(STRONG_COVER)
        assert isinstance(result.has_company_name, bool)

    def test_has_role_name_attribute(self):
        result = score_cover_letter(STRONG_COVER)
        assert isinstance(result.has_role_name, bool)


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


class TestCoverScoreCLI:
    def test_cover_score_command_registered(self):
        """cover-score command should be registered in main CLI."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["cover-score", "--help"])
        assert result.exit_code == 0
        assert "cover" in result.output.lower()

    def test_cover_score_runs_on_file(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        cover_file = tmp_path / "cover.md"
        cover_file.write_text(STRONG_COVER)

        runner = CliRunner()
        result = runner.invoke(main, ["cover-score", str(cover_file)])
        assert result.exit_code == 0
        assert "100" in result.output or "/100" in result.output

    def test_cover_score_brief_flag(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        cover_file = tmp_path / "cover.md"
        cover_file.write_text(STRONG_COVER)

        runner = CliRunner()
        result = runner.invoke(main, ["cover-score", str(cover_file), "--brief"])
        assert result.exit_code == 0
        # Brief mode should not show the full dimension table
        assert "Suggestions" not in result.output

    def test_cover_score_json_flag(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        cover_file = tmp_path / "cover.md"
        cover_file.write_text(STRONG_COVER)

        runner = CliRunner()
        result = runner.invoke(main, ["cover-score", str(cover_file), "--json"])
        assert result.exit_code == 0

        payload = json.loads(result.output)
        assert payload["cover_letter"] == str(cover_file)
        assert payload["total"] >= 85
        assert payload["grade"]["letter"] == "A"
        assert len(payload["dimensions"]) == 5

    def test_cover_score_json_with_brief_flag(self, tmp_path):
        from click.testing import CliRunner

        from resume_engine.cli import main

        cover_file = tmp_path / "cover.md"
        cover_file.write_text(WEAK_COVER)

        runner = CliRunner()
        result = runner.invoke(main, ["cover-score", str(cover_file), "--brief", "--json"])
        assert result.exit_code == 0

        payload = json.loads(result.output)
        assert payload["cover_letter"] == str(cover_file)
        assert payload["total"] < 50
        assert payload["grade"]["letter"] == "D"

    def test_cover_score_missing_file(self):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["cover-score", "/nonexistent/path.md"])
        assert result.exit_code != 0
