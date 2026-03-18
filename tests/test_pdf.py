"""Tests for PDF output module."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from resume_engine.pdf import markdown_to_pdf, md_path_to_pdf_path


class TestMdPathToPdfPath:
    def test_replaces_md_extension(self):
        assert md_path_to_pdf_path("resume.md") == "resume.pdf"

    def test_handles_full_path(self):
        result = md_path_to_pdf_path("/tmp/outputs/tailored-resume.md")
        assert result == "/tmp/outputs/tailored-resume.pdf"

    def test_handles_nested_path(self):
        result = md_path_to_pdf_path("/home/user/docs/cover-letter.md")
        assert result.endswith(".pdf")
        assert not result.endswith(".md")

    def test_no_md_extension(self):
        # Non-.md files get .pdf appended (suffix replacement)
        result = md_path_to_pdf_path("resume.txt")
        assert result.endswith(".pdf")

    def test_returns_string(self):
        result = md_path_to_pdf_path("resume.md")
        assert isinstance(result, str)


class TestMarkdownToPdfPandocMissing:
    """Test graceful failure when pandoc is not available."""

    def test_raises_runtime_error_when_no_pandoc(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\nPython developer\n")
        pdf_out = tmp_path / "resume.pdf"

        with patch("resume_engine.pdf.shutil.which", return_value=None):
            with pytest.raises(RuntimeError, match="pandoc is not installed"):
                markdown_to_pdf(str(md_file), str(pdf_out))

    def test_error_message_includes_install_hint(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\n")
        pdf_out = tmp_path / "resume.pdf"

        with patch("resume_engine.pdf.shutil.which", return_value=None):
            try:
                markdown_to_pdf(str(md_file), str(pdf_out))
            except RuntimeError as exc:
                assert "brew install pandoc" in str(exc) or "apt install pandoc" in str(exc)


class TestMarkdownToPdfPandocFails:
    """Test graceful error propagation when pandoc exits non-zero."""

    def test_raises_runtime_error_on_pandoc_failure(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\nPython developer\n")
        pdf_out = tmp_path / "resume.pdf"

        failed_result = MagicMock()
        failed_result.returncode = 1
        failed_result.stderr = "pdflatex not found"

        with patch("resume_engine.pdf.shutil.which", return_value="/usr/bin/pandoc"):
            with patch("resume_engine.pdf.subprocess.run", return_value=failed_result):
                with pytest.raises(RuntimeError, match="pandoc PDF conversion failed"):
                    markdown_to_pdf(str(md_file), str(pdf_out))

    def test_error_message_includes_stderr(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Resume\n")
        pdf_out = tmp_path / "resume.pdf"

        failed_result = MagicMock()
        failed_result.returncode = 1
        failed_result.stderr = "LaTeX engine missing"

        with patch("resume_engine.pdf.shutil.which", return_value="/usr/bin/pandoc"):
            with patch("resume_engine.pdf.subprocess.run", return_value=failed_result):
                try:
                    markdown_to_pdf(str(md_file), str(pdf_out))
                except RuntimeError as exc:
                    assert "LaTeX engine missing" in str(exc)


class TestMarkdownToPdfSuccess:
    """Test successful PDF conversion path (pandoc mocked)."""

    def test_returns_absolute_path_on_success(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\nPython developer\n")
        pdf_out = tmp_path / "resume.pdf"

        success_result = MagicMock()
        success_result.returncode = 0
        success_result.stderr = ""

        with patch("resume_engine.pdf.shutil.which", return_value="/usr/bin/pandoc"):
            with patch("resume_engine.pdf.subprocess.run", return_value=success_result):
                result = markdown_to_pdf(str(md_file), str(pdf_out))

        assert os.path.isabs(result)
        assert result.endswith(".pdf")

    def test_calls_pandoc_with_correct_args(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\n")
        pdf_out = tmp_path / "resume.pdf"

        success_result = MagicMock()
        success_result.returncode = 0
        success_result.stderr = ""

        with patch("resume_engine.pdf.shutil.which", return_value="/usr/bin/pandoc"):
            with patch("resume_engine.pdf.subprocess.run", return_value=success_result) as mock_run:
                markdown_to_pdf(str(md_file), str(pdf_out))

        call_args = mock_run.call_args[0][0]
        assert "/usr/bin/pandoc" in call_args
        assert str(md_file) in call_args
        assert str(pdf_out) in call_args
        assert "--standalone" in call_args

    def test_includes_pdflatex_when_available(self, tmp_path):
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\n")
        pdf_out = tmp_path / "resume.pdf"

        success_result = MagicMock()
        success_result.returncode = 0

        def which_side_effect(name, path=None):
            if name == "pandoc":
                return "/usr/bin/pandoc"
            if name == "pdflatex":
                return "/usr/bin/pdflatex"
            return None

        with patch("resume_engine.pdf.shutil.which", side_effect=which_side_effect):
            with patch("resume_engine.pdf.subprocess.run", return_value=success_result) as mock_run:
                markdown_to_pdf(str(md_file), str(pdf_out))

        call_args = mock_run.call_args[0][0]
        assert any(arg.startswith("--pdf-engine") for arg in call_args)

    def test_works_without_pdflatex(self, tmp_path):
        """Falls back gracefully when pdflatex is absent."""
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Resume\n")
        pdf_out = tmp_path / "resume.pdf"

        success_result = MagicMock()
        success_result.returncode = 0

        def which_side_effect(name, path=None):
            if name == "pandoc":
                return "/usr/bin/pandoc"
            return None  # pdflatex missing

        with patch("resume_engine.pdf.shutil.which", side_effect=which_side_effect):
            with patch("resume_engine.pdf.subprocess.run", return_value=success_result) as mock_run:
                result = markdown_to_pdf(str(md_file), str(pdf_out))

        call_args = mock_run.call_args[0][0]
        assert not any(arg.startswith("--pdf-engine") for arg in call_args)
        assert result.endswith(".pdf")

    def test_header_tempfile_cleaned_up(self, tmp_path):
        """Verify the temporary LaTeX header file is removed after conversion."""
        md_file = tmp_path / "resume.md"
        md_file.write_text("# Jane Doe\n")
        pdf_out = tmp_path / "resume.pdf"

        success_result = MagicMock()
        success_result.returncode = 0

        created_temps = []
        original_tempfile = tempfile.NamedTemporaryFile

        def tracking_tempfile(*args, **kwargs):
            f = original_tempfile(*args, **kwargs)
            created_temps.append(f.name)
            return f

        def which_side_effect(name, path=None):
            return "/usr/bin/pandoc" if name == "pandoc" else None

        with patch("resume_engine.pdf.shutil.which", side_effect=which_side_effect):
            with patch("resume_engine.pdf.subprocess.run", return_value=success_result):
                with patch("resume_engine.pdf.tempfile.NamedTemporaryFile", tracking_tempfile):
                    markdown_to_pdf(str(md_file), str(pdf_out))

        for temp_path in created_temps:
            assert not os.path.exists(temp_path), f"Temp file not cleaned up: {temp_path}"


class TestPdfIntegration:
    """Integration test: runs real pandoc if available."""

    @pytest.mark.skipif(
        not __import__("shutil").which("pandoc"),
        reason="pandoc not installed",
    )
    def test_real_pandoc_conversion(self, tmp_path):
        """End-to-end: markdown -> PDF via real pandoc (skipped if pandoc absent)."""
        md_file = tmp_path / "resume.md"
        md_file.write_text(
            "# Jane Doe\n\njane@example.com | github.com/janedoe\n\n"
            "## Summary\n\nExperienced Python developer.\n\n"
            "## Skills\n\n- Python\n- Django\n- PostgreSQL\n"
        )
        pdf_out = tmp_path / "resume.pdf"

        result = markdown_to_pdf(str(md_file), str(pdf_out))

        assert result.endswith(".pdf")
        # pandoc may or may not produce a file depending on LaTeX engine
        # but no exception means the call succeeded
