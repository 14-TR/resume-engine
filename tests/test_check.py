"""Tests for the system health check module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from resume_engine.check import (
    check_anthropic_key,
    check_ollama,
    check_openai_key,
    check_pandoc,
    check_pdflatex,
    run_checks,
)


class TestCheckOllama:
    def test_ok_when_reachable(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "qwen2.5:14b"}, {"name": "llama3.2:3b"}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = check_ollama()

        assert result["ok"] is True
        assert "qwen2.5:14b" in result["models"]
        assert "llama3.2:3b" in result["models"]

    def test_fail_when_unreachable(self):
        import httpx

        with patch("httpx.get", side_effect=httpx.ConnectError("connection refused")):
            result = check_ollama()

        assert result["ok"] is False
        assert "error" in result

    def test_ok_with_no_models_pulled(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            result = check_ollama()

        assert result["ok"] is True
        assert result["models"] == []

    def test_uses_custom_ollama_url(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_URL", "http://192.168.1.5:11434")
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp) as mock_get:
            result = check_ollama()

        assert "192.168.1.5" in result["url"]
        called_url = mock_get.call_args[0][0]
        assert "192.168.1.5" in called_url


class TestCheckPandoc:
    def test_ok_when_installed(self):
        with patch("shutil.which", return_value="/usr/local/bin/pandoc"):
            mock_result = MagicMock()
            mock_result.stdout = "pandoc 3.2.1\nCompiled with...\n"
            with patch("subprocess.run", return_value=mock_result):
                result = check_pandoc()

        assert result["ok"] is True
        assert "pandoc" in result["version"]

    def test_fail_when_not_installed(self):
        with patch("shutil.which", return_value=None):
            result = check_pandoc()

        assert result["ok"] is False
        assert "not found" in result["error"]

    def test_fail_when_subprocess_raises(self):
        with patch("shutil.which", return_value="/usr/local/bin/pandoc"):
            with patch("subprocess.run", side_effect=FileNotFoundError("no such file")):
                result = check_pandoc()

        assert result["ok"] is False


class TestCheckPdflatex:
    def test_ok_when_installed(self):
        with patch("shutil.which", return_value="/usr/bin/pdflatex"):
            mock_result = MagicMock()
            mock_result.stdout = "pdfTeX 3.141592...\n"
            with patch("subprocess.run", return_value=mock_result):
                result = check_pdflatex()

        assert result["ok"] is True

    def test_fail_when_not_installed(self):
        with patch("shutil.which", return_value=None):
            result = check_pdflatex()

        assert result["ok"] is False
        assert "hint" not in result or result.get("ok") is False


class TestCheckOpenAIKey:
    def test_ok_with_valid_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-abcdefghijklmno1234")
        result = check_openai_key()
        assert result["ok"] is True
        assert "masked" in result
        assert "sk-" in result["masked"]

    def test_fail_when_not_set(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = check_openai_key()
        assert result["ok"] is False
        assert "not set" in result["error"]

    def test_fail_when_invalid_format(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "invalid-key-format")
        result = check_openai_key()
        assert result["ok"] is False
        assert "valid key" in result["error"]

    def test_mask_hides_middle(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-abcdefghijklmno1234")
        result = check_openai_key()
        assert "..." in result["masked"]
        assert "abcdefghijklmno" not in result["masked"]


class TestCheckAnthropicKey:
    def test_ok_with_valid_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-abcdefghijklmno1234")
        result = check_anthropic_key()
        assert result["ok"] is True
        assert "masked" in result

    def test_fail_when_not_set(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = check_anthropic_key()
        assert result["ok"] is False

    def test_fail_when_invalid_format(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "not-a-real-key")
        result = check_anthropic_key()
        assert result["ok"] is False

    def test_prefix_validation(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-something")
        result = check_anthropic_key()
        assert result["ok"] is True


class TestRunChecks:
    def test_returns_list_of_dicts(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            with patch("shutil.which", return_value=None):
                results = run_checks()

        assert isinstance(results, list)
        assert len(results) == 5
        for r in results:
            assert "name" in r
            assert "category" in r
            assert "ok" in r

    def test_all_checks_have_detail_field(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"models": [{"name": "test:latest"}]}
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.get", return_value=mock_resp):
            with patch("shutil.which", return_value=None):
                results = run_checks()

        for r in results:
            assert "detail" in r

    def test_failing_checks_include_hint(self):
        with patch("httpx.get", side_effect=Exception("unreachable")):
            with patch("shutil.which", return_value=None):
                results = run_checks()

        failing = [r for r in results if not r["ok"]]
        for r in failing:
            assert "hint" in r, f"Check '{r['name']}' is failing but has no hint"
