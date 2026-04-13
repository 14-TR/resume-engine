"""Interactive master resume builder -- guided setup from scratch.

Walks the user through creating a professional master resume via
interactive prompts. No existing resume file or LLM needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Experience:
    company: str
    title: str
    start: str
    end: str
    bullets: List[str] = field(default_factory=list)


@dataclass
class Education:
    school: str
    degree: str
    year: str


@dataclass
class ResumeData:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    website: str = ""
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[Experience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)


def render_markdown(data: ResumeData) -> str:
    """Convert ResumeData to a clean markdown master resume."""
    lines: List[str] = []

    # Header
    lines.append(f"# {data.name}")
    lines.append("")

    contact_parts = []
    if data.email:
        contact_parts.append(data.email)
    if data.phone:
        contact_parts.append(data.phone)
    if data.location:
        contact_parts.append(data.location)
    if contact_parts:
        lines.append(" | ".join(contact_parts))
        lines.append("")

    if data.linkedin:
        lines.append(f"LinkedIn: {data.linkedin}")
    if data.website:
        lines.append(f"Website: {data.website}")
    if data.linkedin or data.website:
        lines.append("")

    # Summary
    if data.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(data.summary)
        lines.append("")

    # Skills
    if data.skills:
        lines.append("## Skills")
        lines.append("")
        lines.append(", ".join(data.skills))
        lines.append("")

    # Experience
    if data.experience:
        lines.append("## Experience")
        lines.append("")
        for exp in data.experience:
            date_range = f"{exp.start} - {exp.end}"
            lines.append(f"### {exp.title} | {exp.company}")
            lines.append(f"*{date_range}*")
            lines.append("")
            for bullet in exp.bullets:
                lines.append(f"- {bullet}")
            lines.append("")

    # Education
    if data.education:
        lines.append("## Education")
        lines.append("")
        for edu in data.education:
            lines.append(f"### {edu.degree} | {edu.school}")
            lines.append(f"*{edu.year}*")
            lines.append("")

    # Certifications
    if data.certifications:
        lines.append("## Certifications")
        lines.append("")
        for cert in data.certifications:
            lines.append(f"- {cert}")
        lines.append("")

    return "\n".join(lines)
