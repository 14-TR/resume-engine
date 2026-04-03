"""Tests for resume_engine.init -- master resume builder."""

from __future__ import annotations

from resume_engine.init import Education, Experience, ResumeData, render_markdown


class TestRenderMarkdown:
    """Test markdown rendering from ResumeData."""

    def test_minimal(self):
        """Name-only resume renders valid markdown."""
        data = ResumeData(name="Alice Smith")
        md = render_markdown(data)
        assert "# Alice Smith" in md

    def test_full_resume(self):
        """All fields render into markdown."""
        data = ResumeData(
            name="Bob Jones",
            email="bob@example.com",
            phone="555-1234",
            location="Denver, CO",
            linkedin="https://linkedin.com/in/bob",
            website="https://bob.dev",
            summary="Experienced engineer with 5 years in cloud systems.",
            skills=["Python", "AWS", "Docker"],
            experience=[
                Experience(
                    company="Acme Corp",
                    title="Senior Engineer",
                    start="Jan 2020",
                    end="Present",
                    bullets=[
                        "Led migration of 50 microservices to Kubernetes",
                        "Reduced deploy time by 40% with CI/CD pipeline",
                    ],
                ),
                Experience(
                    company="StartupX",
                    title="Software Engineer",
                    start="Jun 2017",
                    end="Dec 2019",
                    bullets=["Built REST API handling 10K req/s"],
                ),
            ],
            education=[
                Education(
                    school="State University",
                    degree="B.S. Computer Science",
                    year="2017",
                ),
            ],
            certifications=["AWS Solutions Architect", "CKA"],
        )

        md = render_markdown(data)

        # Header
        assert "# Bob Jones" in md
        assert "bob@example.com" in md
        assert "555-1234" in md
        assert "Denver, CO" in md
        assert "LinkedIn: https://linkedin.com/in/bob" in md
        assert "Website: https://bob.dev" in md

        # Sections
        assert "## Summary" in md
        assert "Experienced engineer" in md
        assert "## Skills" in md
        assert "Python, AWS, Docker" in md
        assert "## Experience" in md
        assert "### Senior Engineer | Acme Corp" in md
        assert "*Jan 2020 - Present*" in md
        assert "- Led migration of 50 microservices" in md
        assert "### Software Engineer | StartupX" in md
        assert "## Education" in md
        assert "### B.S. Computer Science | State University" in md
        assert "*2017*" in md
        assert "## Certifications" in md
        assert "- AWS Solutions Architect" in md
        assert "- CKA" in md

    def test_no_optional_fields(self):
        """Sections with no data are omitted."""
        data = ResumeData(name="Jane Doe", email="jane@test.com")
        md = render_markdown(data)

        assert "# Jane Doe" in md
        assert "jane@test.com" in md
        assert "## Summary" not in md
        assert "## Skills" not in md
        assert "## Experience" not in md
        assert "## Education" not in md
        assert "## Certifications" not in md

    def test_experience_no_bullets(self):
        """Experience with no bullets renders cleanly."""
        data = ResumeData(
            name="Test User",
            experience=[
                Experience(
                    company="SomeCo",
                    title="Intern",
                    start="May 2023",
                    end="Aug 2023",
                    bullets=[],
                ),
            ],
        )
        md = render_markdown(data)
        assert "### Intern | SomeCo" in md
        assert "*May 2023 - Aug 2023*" in md

    def test_skills_comma_separated(self):
        """Skills render as comma-separated list."""
        data = ResumeData(name="X", skills=["A", "B", "C"])
        md = render_markdown(data)
        assert "A, B, C" in md

    def test_contact_line_formatting(self):
        """Contact line uses pipe separators."""
        data = ResumeData(name="Y", email="y@t.com", phone="111", location="NYC")
        md = render_markdown(data)
        assert "y@t.com | 111 | NYC" in md

    def test_no_em_dashes(self):
        """Output never contains em dashes."""
        data = ResumeData(
            name="Z",
            summary="A very experienced person who does things well.",
            experience=[
                Experience(
                    company="Co",
                    title="Lead",
                    start="2020",
                    end="2023",
                    bullets=["Managed a team of 5 engineers"],
                ),
            ],
        )
        md = render_markdown(data)
        assert "\u2014" not in md  # em dash
        assert "\u2013" not in md  # en dash

    def test_multiple_education(self):
        """Multiple education entries render."""
        data = ResumeData(
            name="Multi",
            education=[
                Education(school="MIT", degree="M.S. AI", year="2022"),
                Education(school="State U", degree="B.S. CS", year="2020"),
            ],
        )
        md = render_markdown(data)
        assert "### M.S. AI | MIT" in md
        assert "### B.S. CS | State U" in md


class TestResumeDataDefaults:
    """Test ResumeData initialization."""

    def test_defaults(self):
        data = ResumeData()
        assert data.name == ""
        assert data.skills == []
        assert data.experience == []
        assert data.education == []
        assert data.certifications == []
