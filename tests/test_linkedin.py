"""Tests for LinkedIn profile import module."""

import csv
import io
import json
import zipfile
from pathlib import Path

import pytest

from resume_engine.linkedin import (
    _build_markdown_from_csvs,
    _extract_certifications,
    _extract_education,
    _extract_experience,
    _extract_profile,
    _extract_skills,
    _json_ld_to_markdown,
    _read_csv,
    parse_linkedin_export,
)


# ---------------------------------------------------------------------------
# CSV parsing helpers
# ---------------------------------------------------------------------------


def make_csv(headers: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue()


class TestReadCsv:
    def test_basic_csv(self):
        content = make_csv(["Name", "Title"], [["Alice", "Engineer"]])
        rows = _read_csv(content)
        assert len(rows) == 1
        assert rows[0]["Name"] == "Alice"

    def test_skips_linkedin_note_header(self):
        content = "Notes: This is exported data\n" + make_csv(["Name"], [["Bob"]])
        rows = _read_csv(content)
        assert rows[0]["Name"] == "Bob"

    def test_empty_csv(self):
        rows = _read_csv("Name,Title\n")
        assert rows == []


class TestExtractProfile:
    def test_full_profile(self):
        files = {
            "Profile.csv": make_csv(
                ["First Name", "Last Name", "Headline", "Summary", "Geo Location"],
                [["Jane", "Smith", "Senior Engineer", "I build things.", "Denver, CO"]],
            )
        }
        result = _extract_profile(files)
        assert result is not None
        assert "Jane Smith" in result
        assert "Senior Engineer" in result
        assert "Denver, CO" in result
        assert "I build things." in result

    def test_minimal_profile(self):
        files = {
            "Profile.csv": make_csv(
                ["First Name", "Last Name"],
                [["Tom", "Jones"]],
            )
        }
        result = _extract_profile(files)
        assert result is not None
        assert "Tom Jones" in result

    def test_missing_file(self):
        result = _extract_profile({})
        assert result is None


class TestExtractExperience:
    def test_single_job(self):
        files = {
            "Positions.csv": make_csv(
                ["Title", "Company Name", "Started On", "Finished On", "Description", "Location"],
                [["Staff Engineer", "Acme Corp", "Jan 2020", "Dec 2023", "Built APIs.", "Remote"]],
            )
        }
        result = _extract_experience(files)
        assert result is not None
        assert "Staff Engineer" in result
        assert "Acme Corp" in result
        assert "Jan 2020" in result
        assert "Built APIs." in result

    def test_present_job(self):
        files = {
            "Positions.csv": make_csv(
                ["Title", "Company Name", "Started On", "Finished On", "Description", "Location"],
                [["Lead Dev", "StartupX", "Mar 2024", "", "Leading team.", ""]],
            )
        }
        result = _extract_experience(files)
        assert "Present" in result

    def test_multiline_description(self):
        files = {
            "Positions.csv": make_csv(
                ["Title", "Company Name", "Started On", "Finished On", "Description", "Location"],
                [["Engineer", "Corp", "2021", "", "Did thing A\nDid thing B", ""]],
            )
        }
        result = _extract_experience(files)
        assert "Did thing A" in result
        assert "Did thing B" in result

    def test_missing_file(self):
        result = _extract_experience({})
        assert result is None


class TestExtractEducation:
    def test_full_education(self):
        files = {
            "Education.csv": make_csv(
                ["School Name", "Degree Name", "Field Of Study", "Start Date", "End Date", "Activities and Societies", "Notes"],
                [["State University", "B.S.", "Computer Science", "2014", "2018", "Chess Club", ""]],
            )
        }
        result = _extract_education(files)
        assert result is not None
        assert "State University" in result
        assert "B.S." in result
        assert "Computer Science" in result

    def test_missing_file(self):
        result = _extract_education({})
        assert result is None


class TestExtractSkills:
    def test_skills(self):
        files = {
            "Skills.csv": make_csv(
                ["Name"],
                [["Python"], ["Docker"], ["Kubernetes"]],
            )
        }
        result = _extract_skills(files)
        assert result is not None
        assert "Python" in result
        assert "Docker" in result

    def test_missing_file(self):
        result = _extract_skills({})
        assert result is None


class TestExtractCertifications:
    def test_certifications(self):
        files = {
            "Certifications.csv": make_csv(
                ["Name", "Authority", "Started On", "Url"],
                [["AWS SAA", "Amazon", "2023", "https://aws.amazon.com/cert"]],
            )
        }
        result = _extract_certifications(files)
        assert result is not None
        assert "AWS SAA" in result
        assert "Amazon" in result

    def test_missing_file(self):
        result = _extract_certifications({})
        assert result is None


class TestBuildMarkdown:
    def test_full_export(self):
        files = {
            "Profile.csv": make_csv(
                ["First Name", "Last Name", "Headline"],
                [["Alex", "Rivera", "Python Dev"]],
            ),
            "Positions.csv": make_csv(
                ["Title", "Company Name", "Started On", "Finished On", "Description", "Location"],
                [["Engineer", "Corp", "2020", "", "Built stuff.", ""]],
            ),
            "Skills.csv": make_csv(["Name"], [["Python"], ["SQL"]]),
        }
        result = _build_markdown_from_csvs(files)
        assert "Alex Rivera" in result
        assert "Python Dev" in result
        assert "Engineer" in result
        assert "Python" in result

    def test_raises_on_empty(self):
        with pytest.raises(RuntimeError, match="Could not extract"):
            _build_markdown_from_csvs({})


class TestJsonLdToMarkdown:
    def test_person_schema(self):
        data = {
            "@type": "Person",
            "name": "Chris Lee",
            "description": "Full Stack Developer",
            "email": "chris@example.com",
            "knowsAbout": ["JavaScript", "React", "Node.js"],
        }
        result = _json_ld_to_markdown(data, "https://linkedin.com/in/chrislee")
        assert "Chris Lee" in result
        assert "Full Stack Developer" in result
        assert "JavaScript" in result

    def test_empty_data(self):
        result = _json_ld_to_markdown({}, "https://linkedin.com/in/test")
        assert isinstance(result, str)


class TestParseLinkedinExport:
    def test_parse_zip(self, tmp_path):
        zip_path = tmp_path / "linkedin-export.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            profile_csv = make_csv(
                ["First Name", "Last Name", "Headline"],
                [["Dana", "Kim", "Data Scientist"]],
            )
            zf.writestr("Profile.csv", profile_csv)
            skills_csv = make_csv(["Name"], [["Python"], ["R"]])
            zf.writestr("Skills.csv", skills_csv)

        result = parse_linkedin_export(str(zip_path))
        assert "Dana Kim" in result
        assert "Data Scientist" in result
        assert "Python" in result

    def test_parse_directory(self, tmp_path):
        profile_csv = make_csv(
            ["First Name", "Last Name", "Headline"],
            [["Jordan", "Park", "DevOps Engineer"]],
        )
        (tmp_path / "Profile.csv").write_text(profile_csv)

        result = parse_linkedin_export(str(tmp_path))
        assert "Jordan Park" in result
        assert "DevOps Engineer" in result

    def test_invalid_path(self, tmp_path):
        bad_file = tmp_path / "not-a-zip.csv"
        bad_file.write_text("hello")
        with pytest.raises(RuntimeError):
            parse_linkedin_export(str(bad_file))

    def test_empty_directory(self, tmp_path):
        with pytest.raises(RuntimeError, match="No CSV files"):
            parse_linkedin_export(str(tmp_path))
