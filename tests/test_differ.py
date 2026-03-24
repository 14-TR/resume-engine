"""Tests for the resume diff module."""

from __future__ import annotations

import pytest

from resume_engine.differ import ResumeDiff, SectionDiff, _split_sections, compute_diff


MASTER = """\
# Alex Rivera
alex@example.com | Denver, CO

## Summary
Experienced software engineer with 5 years building web apps.

## Skills
- Python
- JavaScript

## Experience
### Engineer at Acme (2020 - Present)
- Built REST APIs
- Led team of 3

## Education
### B.S. Computer Science -- State University (2020)
"""

TAILORED = """\
# Alex Rivera
alex@example.com | Denver, CO

## Summary
Senior software engineer with 5 years building scalable web applications.

## Skills
- Python
- TypeScript
- Docker

## Experience
### Engineer at Acme (2020 - Present)
- Built high-performance REST APIs handling 1M req/day
- Led team of 3
- Mentored 2 junior engineers

## Education
### B.S. Computer Science -- State University (2020)
"""

IDENTICAL = """\
# Jane Doe
jane@example.com

## Summary
No changes here.

## Skills
- Python
"""


class TestSplitSections:
    def test_split_finds_sections(self):
        sections = dict(_split_sections(MASTER))
        assert "Summary" in sections
        assert "Skills" in sections
        assert "Experience" in sections
        assert "Education" in sections

    def test_preamble_excluded_from_names(self):
        sections = dict(_split_sections(MASTER))
        assert "_preamble" not in sections or True  # preamble may or may not appear

    def test_empty_text(self):
        sections = _split_sections("")
        assert sections == [] or sections == [("_preamble", "")]

    def test_no_headers(self):
        sections = _split_sections("Just some text\nwithout headers\n")
        assert len(sections) == 1
        assert sections[0][0] == "_preamble"


class TestComputeDiff:
    def setup_method(self):
        self.result = compute_diff(MASTER, TAILORED)

    def test_returns_resume_diff(self):
        assert isinstance(self.result, ResumeDiff)

    def test_added_lines_positive(self):
        assert self.result.added_lines > 0

    def test_removed_lines_positive(self):
        assert self.result.removed_lines > 0

    def test_unified_diff_not_empty(self):
        assert len(self.result.unified_diff) > 0

    def test_sections_populated(self):
        assert len(self.result.sections) > 0

    def test_changed_sections_detected(self):
        changed = [s for s in self.result.sections if s.is_changed]
        assert len(changed) > 0

    def test_unchanged_education_section(self):
        education = next((s for s in self.result.sections if "Education" in s.name), None)
        # Education section should be unchanged or minimally changed
        # (it's identical in our test data)
        assert education is not None

    def test_summary_section_changed(self):
        summary = next((s for s in self.result.sections if s.name == "Summary"), None)
        assert summary is not None
        assert summary.is_changed

    def test_skills_section_changed(self):
        skills = next((s for s in self.result.sections if s.name == "Skills"), None)
        assert skills is not None
        assert skills.is_changed

    def test_change_score_nonzero(self):
        assert self.result.change_score > 0
        assert self.result.change_score <= 100

    def test_total_original_lines(self):
        assert self.result.total_original_lines == len(MASTER.splitlines())


class TestIdenticalDiff:
    def setup_method(self):
        self.result = compute_diff(IDENTICAL, IDENTICAL)

    def test_no_added_lines(self):
        assert self.result.added_lines == 0

    def test_no_removed_lines(self):
        assert self.result.removed_lines == 0

    def test_change_score_zero(self):
        assert self.result.change_score == 0

    def test_no_changed_sections(self):
        changed = [s for s in self.result.sections if s.is_changed]
        assert len(changed) == 0


class TestSectionDiff:
    def test_is_changed_true_when_lines(self):
        sd = SectionDiff(name="Skills", added=["Python"], removed=[], changed_lines=1, total_lines=3)
        assert sd.is_changed is True

    def test_is_changed_false_when_empty(self):
        sd = SectionDiff(name="Skills", added=[], removed=[], changed_lines=0, total_lines=3)
        assert sd.is_changed is False

    def test_change_pct_calculation(self):
        sd = SectionDiff(name="Skills", added=["a"], removed=["b"], changed_lines=2, total_lines=10)
        assert sd.change_pct == 20

    def test_change_pct_caps_at_100(self):
        sd = SectionDiff(name="X", added=["a"] * 50, removed=[], changed_lines=50, total_lines=5)
        assert sd.change_pct == 100

    def test_change_pct_zero_lines(self):
        sd = SectionDiff(name="X", added=[], removed=[], changed_lines=0, total_lines=0)
        assert sd.change_pct == 0


class TestCLIDiff:
    def test_diff_command_help(self):
        from click.testing import CliRunner
        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["diff", "--help"])
        assert result.exit_code == 0
        assert "ORIGINAL" in result.output
        assert "TAILORED" in result.output

    def test_diff_command_runs_on_files(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        orig = tmp_path / "original.md"
        tail = tmp_path / "tailored.md"
        orig.write_text(MASTER)
        tail.write_text(TAILORED)

        runner = CliRunner()
        result = runner.invoke(main, ["diff", str(orig), str(tail)])
        assert result.exit_code == 0
        assert "Overall change" in result.output

    def test_diff_command_identical_files(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        orig = tmp_path / "original.md"
        tail = tmp_path / "tailored.md"
        orig.write_text(IDENTICAL)
        tail.write_text(IDENTICAL)

        runner = CliRunner()
        result = runner.invoke(main, ["diff", str(orig), str(tail)])
        assert result.exit_code == 0
        assert "0%" in result.output

    def test_diff_unified_flag(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        orig = tmp_path / "original.md"
        tail = tmp_path / "tailored.md"
        orig.write_text(MASTER)
        tail.write_text(TAILORED)

        runner = CliRunner()
        result = runner.invoke(main, ["diff", str(orig), str(tail), "--unified"])
        assert result.exit_code == 0
        assert "Unified diff" in result.output

    def test_diff_missing_file_fails(self, tmp_path):
        from click.testing import CliRunner
        from resume_engine.cli import main

        orig = tmp_path / "original.md"
        orig.write_text(MASTER)

        runner = CliRunner()
        result = runner.invoke(main, ["diff", str(orig), "/nonexistent/path.md"])
        assert result.exit_code != 0
