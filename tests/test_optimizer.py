"""Tests for resume_engine.optimizer module."""

from __future__ import annotations

from unittest.mock import patch

from resume_engine.optimizer import explain_changes, optimize_resume

SAMPLE_RESUME = """# Jane Smith
jane@example.com | (555) 555-1234

## Summary
Detail-oriented software engineer passionate about building scalable systems.

## Experience

### Software Engineer -- Acme Corp (2021-2024)
- Responsible for maintaining the backend API
- Helped with onboarding new engineers
- Worked on database performance issues
- Managed various projects for the team

## Education
B.S. Computer Science, State University, 2021

## Skills
Python, SQL, Docker, AWS
"""


class TestOptimizerModule:
    def test_optimize_resume_calls_llm(self):
        """optimize_resume should call the LLM and return its response."""
        improved = "# Jane Smith\n- Led backend API development, improving uptime to 99.9%\n"
        with patch("resume_engine.optimizer.complete", return_value=improved) as mock_complete:
            result = optimize_resume(SAMPLE_RESUME, model="openai")

        mock_complete.assert_called_once()
        call_args = mock_complete.call_args
        prompt = call_args[0][0]
        assert "responsible for" in prompt.lower()
        assert "ollama" not in prompt  # model arg passed separately
        assert result == improved

    def test_optimize_resume_passes_model(self):
        """optimize_resume should forward the model argument to complete()."""
        with patch("resume_engine.optimizer.complete", return_value="improved") as mock_complete:
            optimize_resume(SAMPLE_RESUME, model="anthropic")

        _, kwargs = mock_complete.call_args
        assert kwargs.get("model") == "anthropic" or mock_complete.call_args[0][1] == "anthropic"

    def test_optimize_resume_prompt_contains_resume(self):
        """Prompt should include the resume text."""
        with patch("resume_engine.optimizer.complete", return_value="ok") as mock_complete:
            optimize_resume(SAMPLE_RESUME, model="ollama")

        prompt = mock_complete.call_args[0][0]
        assert "Jane Smith" in prompt
        assert "Acme Corp" in prompt

    def test_optimize_resume_no_fabrication_rule_in_prompt(self):
        """Prompt must include the no-fabrication rule."""
        with patch("resume_engine.optimizer.complete", return_value="ok") as mock_complete:
            optimize_resume(SAMPLE_RESUME, model="ollama")

        prompt = mock_complete.call_args[0][0].lower()
        assert "fabricat" in prompt

    def test_explain_changes_calls_llm(self):
        """explain_changes should call the LLM with both texts."""
        original = "- Responsible for building features"
        improved = "- Engineered core features, reducing bug rate by 30%"

        with patch(
            "resume_engine.optimizer.complete", return_value="- Replaced filler verb"
        ) as mock_complete:
            result = explain_changes(original, improved, model="openai")

        assert result == "- Replaced filler verb"
        prompt = mock_complete.call_args[0][0]
        assert "Responsible for building" in prompt
        assert "Engineered core features" in prompt

    def test_explain_changes_both_texts_in_prompt(self):
        """Both original and improved should appear in the explain prompt."""
        with patch("resume_engine.optimizer.complete", return_value="changes") as mock_complete:
            explain_changes("original text here", "improved text here", model="ollama")

        prompt = mock_complete.call_args[0][0]
        assert "original text here" in prompt
        assert "improved text here" in prompt


class TestOptimizerCLI:
    """Integration-style tests via Click test runner."""

    def test_optimize_command_exists(self):
        """optimize command should be registered."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["optimize", "--help"])
        assert result.exit_code == 0
        assert "Improve a resume" in result.output

    def test_optimize_writes_output_file(self, tmp_path):
        """optimize should write the improved resume to an output file."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)
        out_file = tmp_path / "resume-opt.md"

        improved = "# Jane Smith\n- Led backend API development\n"

        with patch("resume_engine.optimizer.optimize_resume", return_value=improved):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["optimize", str(resume_file), "--output", str(out_file), "--model", "openai"],
            )

        assert result.exit_code == 0, result.output
        assert out_file.exists()
        assert out_file.read_text() == improved

    def test_optimize_default_output_filename(self, tmp_path):
        """Without --output, should write <name>-optimized.md."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "myresume.md"
        resume_file.write_text(SAMPLE_RESUME)

        with patch("resume_engine.optimizer.optimize_resume", return_value="improved"):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["optimize", str(resume_file), "--model", "openai"],
            )

        expected = tmp_path / "myresume-optimized.md"
        assert result.exit_code == 0, result.output
        assert expected.exists()

    def test_optimize_with_diff_flag(self, tmp_path):
        """--diff flag should produce diff output in the terminal."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)

        improved = SAMPLE_RESUME.replace("Responsible for maintaining", "Maintained and scaled")

        with patch("resume_engine.optimizer.optimize_resume", return_value=improved):
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["optimize", str(resume_file), "--diff", "--model", "openai"],
            )

        assert result.exit_code == 0, result.output

    def test_optimize_with_explain_flag(self, tmp_path):
        """--explain flag should call explain_changes and print output."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        resume_file = tmp_path / "resume.md"
        resume_file.write_text(SAMPLE_RESUME)

        explanation = "- Replaced 'Responsible for' with action verb 'Maintained'"

        with patch("resume_engine.optimizer.optimize_resume", return_value="improved resume"):
            with patch("resume_engine.optimizer.explain_changes", return_value=explanation):
                runner = CliRunner()
                result = runner.invoke(
                    main,
                    ["optimize", str(resume_file), "--explain", "--model", "openai"],
                )

        assert result.exit_code == 0, result.output
        assert "Changes made" in result.output or explanation in result.output
