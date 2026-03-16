"""Tests for import_resume engine function."""

from unittest.mock import patch


class TestImportResumePrompt:
    def test_import_resume_calls_complete(self):
        """import_resume should call complete with raw text in the prompt."""
        from resume_engine.engine import import_resume

        with patch("resume_engine.engine.complete") as mock_complete:
            mock_complete.return_value = "# Jane Doe\nPython developer"
            result = import_resume("Jane Doe -- Python -- 5 years", model="ollama")

        assert mock_complete.call_count == 1
        call_args = mock_complete.call_args
        prompt = call_args[0][0]
        assert "Jane Doe" in prompt
        assert "Python" in prompt
        assert call_args[1]["model"] == "ollama" or call_args[0][1] == "ollama"
        assert result == "# Jane Doe\nPython developer"

    def test_import_resume_prompt_has_no_em_dash_instruction(self):
        """Prompt should include the no-em-dash rule."""
        import inspect

        from resume_engine import engine

        source = inspect.getsource(engine)
        assert "No em dashes" in source or "no em dashes" in source.lower()

    def test_import_resume_default_model(self):
        """Default model should be ollama."""
        from resume_engine.engine import import_resume

        with patch("resume_engine.engine.complete") as mock_complete:
            mock_complete.return_value = "# Test"
            import_resume("raw text")

        call_args = mock_complete.call_args
        # model param may be positional or keyword
        model_arg = (
            call_args[1].get("model") if call_args[1] else None
        ) or (call_args[0][1] if len(call_args[0]) > 1 else None)
        assert model_arg == "ollama"
