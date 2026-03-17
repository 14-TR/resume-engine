"""Tests for the resume importer module."""

from resume_engine.importer import _IMPORT_PROMPT, text_to_master_resume


class TestImportPrompt:
    def test_prompt_contains_no_em_dashes(self):
        assert "\u2014" not in _IMPORT_PROMPT  # em dash

    def test_prompt_has_text_placeholder(self):
        assert "{text}" in _IMPORT_PROMPT

    def test_prompt_formatted_correctly(self):
        result = _IMPORT_PROMPT.format(text="Sample resume text")
        assert "Sample resume text" in result
        assert "{text}" not in result


class TestTextToMasterResume:
    def test_calls_llm_and_returns_string(self, monkeypatch):
        """Verify function calls LLM with formatted prompt and returns result."""
        captured = {}

        def fake_complete(prompt, model="ollama"):
            captured["prompt"] = prompt
            captured["model"] = model
            return "# Jane Doe\njane@example.com\n\n## Summary\nExperienced engineer."

        monkeypatch.setattr("resume_engine.importer.complete", fake_complete)

        sample = "Jane Doe\njane@example.com\nSoftware Engineer at Acme Corp"
        result = text_to_master_resume(sample, model="ollama")

        assert result == "# Jane Doe\njane@example.com\n\n## Summary\nExperienced engineer."
        assert "Jane Doe" in captured["prompt"]
        assert "Acme Corp" in captured["prompt"]
        assert captured["model"] == "ollama"

    def test_strips_whitespace_from_input(self, monkeypatch):
        """Leading/trailing whitespace in raw text is stripped before sending to LLM."""
        captured = {}

        def fake_complete(prompt, model="ollama"):
            captured["prompt"] = prompt
            return "# Result"

        monkeypatch.setattr("resume_engine.importer.complete", fake_complete)

        text_to_master_resume("  \n  some resume  \n  ", model="ollama")
        assert "some resume" in captured["prompt"]
        # Should not have leading/trailing whitespace in the injected text section
        assert "  \n  some resume  \n  " not in captured["prompt"]

    def test_model_forwarded_to_llm(self, monkeypatch):
        """The --model flag is passed through to the LLM backend."""
        captured = {}

        def fake_complete(prompt, model="ollama"):
            captured["model"] = model
            return "# Result"

        monkeypatch.setattr("resume_engine.importer.complete", fake_complete)

        text_to_master_resume("some text", model="anthropic")
        assert captured["model"] == "anthropic"

    def test_prompt_references_linkedin(self):
        """Prompt should mention LinkedIn to guide users."""
        assert "linkedin" in _IMPORT_PROMPT.lower() or "LinkedIn" in _IMPORT_PROMPT


class TestImportCLI:
    """Integration tests for the import CLI command (no LLM)."""

    def test_import_help(self):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["import", "--help"])
        assert result.exit_code == 0
        assert "--text" in result.output
        assert "--stdin" in result.output
        assert "--output" in result.output
        assert "--model" in result.output

    def test_import_no_args_error(self):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["import"])
        assert result.exit_code != 0

    def test_import_both_args_error(self):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["import", "--text", "file.txt", "--stdin"])
        assert result.exit_code != 0

    def test_import_from_file(self, monkeypatch, tmp_path):
        """Test importing from a text file."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        # Patch the LLM
        monkeypatch.setattr(
            "resume_engine.importer.complete",
            lambda prompt, model="ollama": "# Jane Doe\n\n## Summary\nEngineer.",
        )

        # Create a temp input file
        input_file = tmp_path / "raw-resume.txt"
        input_file.write_text("Jane Doe\nSoftware Engineer\nAcme Corp 2020-2024")

        output_file = tmp_path / "master.md"

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["import", "--text", str(input_file), "--output", str(output_file)],
        )

        assert result.exit_code == 0, result.output
        assert output_file.exists()
        content = output_file.read_text()
        assert "Jane Doe" in content

    def test_import_from_stdin(self, monkeypatch, tmp_path):
        """Test importing from stdin."""
        from click.testing import CliRunner

        from resume_engine.cli import main

        monkeypatch.setattr(
            "resume_engine.importer.complete",
            lambda prompt, model="ollama": "# John Smith\n\n## Skills\nPython",
        )

        output_file = tmp_path / "master.md"

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["import", "--stdin", "--output", str(output_file)],
            input="John Smith\nPython developer since 2015",
        )

        assert result.exit_code == 0, result.output
        assert output_file.exists()
        content = output_file.read_text()
        assert "John Smith" in content
