"""Tests for resume_engine.config module."""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    """Redirect config file to a temp directory for every test."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    # Force reload of the module-level paths
    import importlib

    import resume_engine.config as cfg_mod

    importlib.reload(cfg_mod)
    yield cfg_mod
    importlib.reload(cfg_mod)  # restore for other tests


# ---------------------------------------------------------------------------
# Basic get/set
# ---------------------------------------------------------------------------


class TestConfigSetGet:
    def test_get_missing_returns_none(self, isolated_config):
        assert isolated_config.get("model") is None

    def test_get_missing_returns_default(self, isolated_config):
        assert isolated_config.get("model", "ollama") == "ollama"

    def test_set_and_get(self, isolated_config):
        isolated_config.set_value("model", "openai")
        assert isolated_config.get("model") == "openai"

    def test_set_anthropic(self, isolated_config):
        isolated_config.set_value("model", "anthropic")
        assert isolated_config.get("model") == "anthropic"

    def test_set_format_pdf(self, isolated_config):
        isolated_config.set_value("format", "pdf")
        assert isolated_config.get("format") == "pdf"

    def test_set_free_form_output(self, isolated_config):
        isolated_config.set_value("output", "/tmp/my-resume.md")
        assert isolated_config.get("output") == "/tmp/my-resume.md"

    def test_set_free_form_outdir(self, isolated_config):
        isolated_config.set_value("outdir", "./my-apps")
        assert isolated_config.get("outdir") == "./my-apps"

    def test_set_template(self, isolated_config):
        isolated_config.set_value("template", "technical")
        assert isolated_config.get("template") == "technical"

    def test_load_returns_dict(self, isolated_config):
        isolated_config.set_value("model", "openai")
        data = isolated_config.load()
        assert isinstance(data, dict)
        assert data["model"] == "openai"

    def test_overwrite_existing(self, isolated_config):
        isolated_config.set_value("model", "openai")
        isolated_config.set_value("model", "anthropic")
        assert isolated_config.get("model") == "anthropic"

    def test_multiple_keys(self, isolated_config):
        isolated_config.set_value("model", "openai")
        isolated_config.set_value("format", "pdf")
        data = isolated_config.load()
        assert data["model"] == "openai"
        assert data["format"] == "pdf"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestConfigValidation:
    def test_unknown_key_raises(self, isolated_config):
        with pytest.raises(ValueError, match="Unknown config key"):
            isolated_config.set_value("nonexistent", "value")

    def test_invalid_model_value_raises(self, isolated_config):
        with pytest.raises(ValueError, match="Invalid value"):
            isolated_config.set_value("model", "gpt-4")

    def test_invalid_format_value_raises(self, isolated_config):
        with pytest.raises(ValueError, match="Invalid value"):
            isolated_config.set_value("format", "docx")


# ---------------------------------------------------------------------------
# Unset + reset
# ---------------------------------------------------------------------------


class TestConfigUnsetReset:
    def test_unset_existing(self, isolated_config):
        isolated_config.set_value("model", "openai")
        removed = isolated_config.unset_value("model")
        assert removed is True
        assert isolated_config.get("model") is None

    def test_unset_missing_returns_false(self, isolated_config):
        removed = isolated_config.unset_value("model")
        assert removed is False

    def test_reset_clears_all(self, isolated_config):
        isolated_config.set_value("model", "openai")
        isolated_config.set_value("format", "pdf")
        isolated_config.reset()
        assert isolated_config.get("model") is None
        assert isolated_config.get("format") is None

    def test_reset_no_file_no_error(self, isolated_config):
        isolated_config.reset()  # no file exists -- should not raise


# ---------------------------------------------------------------------------
# apply_defaults
# ---------------------------------------------------------------------------


class TestApplyDefaults:
    def test_fills_none_values(self, isolated_config):
        isolated_config.set_value("model", "openai")
        params = {"model": None, "fmt": "md"}
        result = isolated_config.apply_defaults(params)
        assert result["model"] == "openai"
        assert result["fmt"] == "md"

    def test_does_not_override_explicit(self, isolated_config):
        isolated_config.set_value("model", "openai")
        params = {"model": "anthropic"}
        result = isolated_config.apply_defaults(params)
        assert result["model"] == "anthropic"

    def test_empty_config_leaves_params_unchanged(self, isolated_config):
        params = {"model": None, "fmt": "md"}
        result = isolated_config.apply_defaults(params)
        assert result == params


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestConfigCLI:
    def test_config_list(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["config", "list"])
        assert result.exit_code == 0
        assert "model" in result.output

    def test_config_get_not_set(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["config", "get", "model"])
        assert result.exit_code == 0
        assert "not set" in result.output

    def test_config_set_and_get_cli(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        set_result = runner.invoke(main, ["config", "set", "model", "openai"])
        assert set_result.exit_code == 0
        assert "openai" in set_result.output

        get_result = runner.invoke(main, ["config", "get", "model"])
        assert get_result.exit_code == 0
        assert "openai" in get_result.output

    def test_config_set_invalid_key(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["config", "set", "badkey", "val"])
        assert result.exit_code != 0

    def test_config_set_invalid_value(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["config", "set", "model", "gpt-5"])
        assert result.exit_code != 0

    def test_config_unset_cli(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        runner.invoke(main, ["config", "set", "format", "pdf"])
        result = runner.invoke(main, ["config", "unset", "format"])
        assert result.exit_code == 0
        assert "Unset" in result.output

    def test_config_get_unknown_key(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["config", "get", "badkey"])
        assert result.exit_code != 0

    def test_config_help(self, isolated_config):
        from click.testing import CliRunner

        from resume_engine.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "set" in result.output
        assert "get" in result.output
        assert "list" in result.output
        assert "unset" in result.output
