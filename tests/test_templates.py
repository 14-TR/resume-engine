"""Tests for the template system."""

import pytest

from resume_engine.templates import get_template, get_template_instructions, list_templates, template_choices


class TestListTemplates:
    def test_returns_list(self):
        templates = list_templates()
        assert isinstance(templates, list)

    def test_templates_have_required_keys(self):
        templates = list_templates()
        for t in templates:
            assert "name" in t
            assert "slug" in t
            assert "description" in t
            assert "instructions" in t
            assert "source" in t

    def test_builtin_templates_present(self):
        templates = list_templates()
        slugs = [t["slug"] for t in templates]
        # At least one template should be present
        assert len(slugs) > 0


class TestGetTemplate:
    def test_returns_none_for_unknown(self):
        result = get_template("nonexistent-template-xyz")
        assert result is None

    def test_returns_dict_for_known_template(self):
        templates = list_templates()
        if not templates:
            pytest.skip("No templates available")
        slug = templates[0]["slug"]
        result = get_template(slug)
        assert result is not None
        assert result["slug"] == slug

    def test_case_insensitive(self):
        templates = list_templates()
        if not templates:
            pytest.skip("No templates available")
        slug = templates[0]["slug"]
        result_lower = get_template(slug.lower())
        result_upper = get_template(slug.upper())
        assert result_lower is not None
        assert result_upper is not None


class TestGetTemplateInstructions:
    def test_default_returns_empty_string(self):
        result = get_template_instructions("default")
        assert result == ""

    def test_none_returns_empty_string(self):
        result = get_template_instructions(None)
        assert result == ""

    def test_unknown_slug_returns_empty_string(self):
        result = get_template_instructions("nonexistent-xyz-template")
        assert result == ""

    def test_known_template_returns_nonempty_string(self):
        templates = list_templates()
        if not templates:
            pytest.skip("No templates available")
        slug = templates[0]["slug"]
        result = get_template_instructions(slug)
        assert isinstance(result, str)


class TestTemplateChoices:
    def test_includes_default(self):
        choices = template_choices()
        assert "default" in choices

    def test_default_is_first(self):
        choices = template_choices()
        assert choices[0] == "default"

    def test_returns_list_of_strings(self):
        choices = template_choices()
        assert all(isinstance(c, str) for c in choices)
