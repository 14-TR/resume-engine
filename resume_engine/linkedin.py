"""LinkedIn profile import -- fetch public profile URL or parse LinkedIn data export."""

import csv
import io
import json
import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Public URL scraper
# ---------------------------------------------------------------------------

def scrape_linkedin_profile(url: str) -> str:
    """
    Attempt to scrape a LinkedIn public profile URL and return markdown.

    LinkedIn aggressively blocks scrapers, so this may return a partial
    result or raise RuntimeError with instructions for the manual export path.

    Args:
        url: LinkedIn profile URL (https://www.linkedin.com/in/username/)

    Returns:
        Markdown-formatted resume text.

    Raises:
        RuntimeError: If LinkedIn blocks the request or profile is private.
    """
    import httpx

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30, headers=headers)
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error fetching LinkedIn profile: {e}") from e

    if resp.status_code == 999 or "authwall" in resp.url.path:
        raise RuntimeError(
            "LinkedIn requires authentication to view this profile.\n"
            "Use --linkedin-export with a LinkedIn data export instead.\n"
            "See: https://14-tr.github.io/resume-engine/linkedin-import/"
        )

    if resp.status_code != 200:
        raise RuntimeError(
            f"LinkedIn returned HTTP {resp.status_code}.\n"
            "If the profile is private, use --linkedin-export instead."
        )

    html = resp.text

    # Detect auth wall
    if "Sign in" in html and "authwall" in html:
        raise RuntimeError(
            "LinkedIn auth wall detected -- the profile is not publicly accessible.\n"
            "Use --linkedin-export with a downloaded LinkedIn data export.\n"
            "Download at: https://www.linkedin.com/mypreferences/d/download-my-data"
        )

    return _parse_linkedin_html(html, url)


def _parse_linkedin_html(html: str, url: str) -> str:
    """Parse LinkedIn profile HTML into markdown resume."""
    # Strip scripts/styles
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)

    # Extract JSON-LD structured data (LinkedIn embeds profile data here)
    json_ld_matches = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    profile_data = {}
    for match in json_ld_matches:
        try:
            data = json.loads(match.strip())
            if isinstance(data, dict) and data.get("@type") in ("Person", "ProfilePage"):
                profile_data = data
                break
        except (json.JSONDecodeError, ValueError):
            continue

    if profile_data:
        return _json_ld_to_markdown(profile_data, url)

    # Fall back to plain text extraction
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()

    if len(clean) < 200:
        raise RuntimeError(
            "Could not extract profile content from LinkedIn.\n"
            "Use --linkedin-export with a LinkedIn data export instead."
        )

    # Return a basic markdown wrapper around extracted text
    profile_url_slug = url.rstrip("/").split("/")[-1]
    return (
        f"# LinkedIn Profile: {profile_url_slug}\n\n"
        f"_Source: {url}_\n\n"
        f"{clean[:4000]}"
    )


def _json_ld_to_markdown(data: dict, url: str) -> str:
    """Convert JSON-LD Person schema to markdown resume."""
    lines = []

    name = data.get("name", "")
    if name:
        lines.append(f"# {name}")

    headline = data.get("description", "") or data.get("jobTitle", "")

    contact_parts = []
    if url:
        contact_parts.append(url)
    email = data.get("email", "")
    if email:
        contact_parts.append(email)

    if contact_parts:
        lines.append(" | ".join(contact_parts))

    if headline:
        lines.append(f"\n{headline}")

    lines.append("")

    # Works for / experience
    works = data.get("worksFor", [])
    if isinstance(works, dict):
        works = [works]
    if works:
        lines.append("## Experience")
        for w in works:
            org = w.get("name", "")
            title = w.get("jobTitle", "")
            if org or title:
                lines.append(f"\n### {title} -- {org}")

    # Alumni of / education
    alumni = data.get("alumniOf", [])
    if isinstance(alumni, dict):
        alumni = [alumni]
    if alumni:
        lines.append("\n## Education")
        for a in alumni:
            school = a.get("name", "")
            degree = a.get("award", "") or a.get("description", "")
            if school:
                entry = f"\n**{school}**"
                if degree:
                    entry += f" -- {degree}"
                lines.append(entry)

    # Skills
    skills = data.get("knowsAbout", [])
    if skills:
        if isinstance(skills, str):
            skills = [skills]
        lines.append("\n## Skills")
        lines.append(", ".join(str(s) for s in skills[:30]))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LinkedIn data export parser
# ---------------------------------------------------------------------------

def parse_linkedin_export(export_path: str) -> str:
    """
    Parse a LinkedIn data export (ZIP or directory) into markdown resume text.

    LinkedIn lets you download your data at:
    https://www.linkedin.com/mypreferences/d/download-my-data

    The export contains CSV files: Profile.csv, Positions.csv, Education.csv,
    Skills.csv, Certifications.csv, etc.

    Args:
        export_path: Path to the LinkedIn export ZIP file or extracted directory.

    Returns:
        Markdown-formatted resume text.

    Raises:
        RuntimeError: If the export cannot be parsed.
    """
    path = Path(export_path)

    if path.suffix.lower() == ".zip":
        return _parse_linkedin_zip(path)
    elif path.is_dir():
        return _parse_linkedin_dir(path)
    else:
        raise RuntimeError(
            f"Expected a LinkedIn export ZIP file or extracted directory, got: {export_path}\n"
            "Download your LinkedIn data at: "
            "https://www.linkedin.com/mypreferences/d/download-my-data"
        )


def _parse_linkedin_zip(zip_path: Path) -> str:
    """Parse a LinkedIn export ZIP file."""
    import zipfile

    if not zipfile.is_zipfile(zip_path):
        raise RuntimeError(f"Not a valid ZIP file: {zip_path}")

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        files: dict[str, str] = {}
        for name in names:
            if name.endswith(".csv"):
                key = Path(name).name
                with zf.open(name) as f:
                    files[key] = f.read().decode("utf-8", errors="replace")

    return _build_markdown_from_csvs(files)


def _parse_linkedin_dir(dir_path: Path) -> str:
    """Parse an extracted LinkedIn export directory."""
    files: dict[str, str] = {}
    for csv_file in dir_path.glob("*.csv"):
        files[csv_file.name] = csv_file.read_text(encoding="utf-8", errors="replace")
    if not files:
        raise RuntimeError(f"No CSV files found in {dir_path}")
    return _build_markdown_from_csvs(files)


def _read_csv(content: str) -> list[dict]:
    """Read CSV content, skipping LinkedIn's extra header lines."""
    lines = content.strip().splitlines()
    # LinkedIn CSVs sometimes have a "Notes:" header line before the actual CSV
    # Skip any leading lines that start with "Note" (LinkedIn export notes)
    start = 0
    for i, line in enumerate(lines):
        if not line.startswith("Note"):
            start = i
            break
    clean_content = "\n".join(lines[start:])
    reader = csv.DictReader(io.StringIO(clean_content))
    return [row for row in reader]


def _build_markdown_from_csvs(files: dict[str, str]) -> str:
    """Build a markdown resume from LinkedIn CSV export files."""
    sections: list[str] = []

    # Profile
    profile = _extract_profile(files)
    if profile:
        sections.append(profile)

    # Experience
    experience = _extract_experience(files)
    if experience:
        sections.append(experience)

    # Education
    education = _extract_education(files)
    if education:
        sections.append(education)

    # Skills
    skills = _extract_skills(files)
    if skills:
        sections.append(skills)

    # Certifications
    certs = _extract_certifications(files)
    if certs:
        sections.append(certs)

    if not sections:
        raise RuntimeError(
            "Could not extract any profile data from the LinkedIn export.\n"
            "Make sure the export contains Profile.csv, Positions.csv, or similar files."
        )

    return "\n\n".join(sections)


def _extract_profile(files: dict[str, str]) -> Optional[str]:
    """Extract basic profile info from Profile.csv."""
    content = files.get("Profile.csv", "")
    if not content:
        return None

    rows = _read_csv(content)
    if not rows:
        return None

    row = rows[0]
    name_parts = [row.get("First Name", "").strip(), row.get("Last Name", "").strip()]
    name = " ".join(p for p in name_parts if p)

    headline = row.get("Headline", "").strip()
    summary = row.get("Summary", "").strip()
    location = row.get("Geo Location", "").strip() or row.get("Location", "").strip()

    lines = []
    if name:
        lines.append(f"# {name}")

    contact_parts = []
    if location:
        contact_parts.append(location)
    email = row.get("Email Address", "").strip()
    if email:
        contact_parts.append(email)
    if contact_parts:
        lines.append(" | ".join(contact_parts))

    if headline:
        lines.append(f"\n{headline}")

    if summary:
        lines.append(f"\n## Summary\n\n{summary}")

    return "\n".join(lines) if lines else None


def _extract_experience(files: dict[str, str]) -> Optional[str]:
    """Extract work experience from Positions.csv."""
    content = files.get("Positions.csv", "")
    if not content:
        return None

    rows = _read_csv(content)
    if not rows:
        return None

    lines = ["## Experience"]
    for row in rows:
        title = row.get("Title", "").strip()
        company = row.get("Company Name", "").strip()
        started = row.get("Started On", "").strip()
        finished = row.get("Finished On", "").strip() or "Present"
        description = row.get("Description", "").strip()
        location = row.get("Location", "").strip()

        if not title and not company:
            continue

        header = f"\n### {title}"
        if company:
            header += f" -- {company}"
        if location:
            header += f", {location}"
        lines.append(header)

        if started:
            lines.append(f"_{started} - {finished}_")

        if description:
            # Turn description into bullets if it has newlines
            desc_lines = [d.strip() for d in description.splitlines() if d.strip()]
            for d in desc_lines:
                if not d.startswith("-"):
                    d = f"- {d}"
                lines.append(d)

    return "\n".join(lines) if len(lines) > 1 else None


def _extract_education(files: dict[str, str]) -> Optional[str]:
    """Extract education from Education.csv."""
    content = files.get("Education.csv", "")
    if not content:
        return None

    rows = _read_csv(content)
    if not rows:
        return None

    lines = ["## Education"]
    for row in rows:
        school = row.get("School Name", "").strip()
        degree = row.get("Degree Name", "").strip()
        field = row.get("Field Of Study", "").strip()
        started = row.get("Start Date", "").strip()
        ended = row.get("End Date", "").strip()
        activities = row.get("Activities and Societies", "").strip()
        notes = row.get("Notes", "").strip()

        if not school:
            continue

        header = f"\n**{school}**"
        if degree:
            header += f" -- {degree}"
            if field:
                header += f" in {field}"
        elif field:
            header += f" -- {field}"
        lines.append(header)

        if started or ended:
            period = f"_{started} - {ended}_" if started and ended else f"_{started or ended}_"
            lines.append(period)

        if activities:
            lines.append(f"Activities: {activities}")
        if notes:
            lines.append(notes)

    return "\n".join(lines) if len(lines) > 1 else None


def _extract_skills(files: dict[str, str]) -> Optional[str]:
    """Extract skills from Skills.csv."""
    content = files.get("Skills.csv", "")
    if not content:
        return None

    rows = _read_csv(content)
    if not rows:
        return None

    skill_names = [row.get("Name", "").strip() for row in rows if row.get("Name", "").strip()]
    if not skill_names:
        return None

    return f"## Skills\n\n{', '.join(skill_names)}"


def _extract_certifications(files: dict[str, str]) -> Optional[str]:
    """Extract certifications from Certifications.csv."""
    content = files.get("Certifications.csv", "")
    if not content:
        return None

    rows = _read_csv(content)
    if not rows:
        return None

    lines = ["## Certifications"]
    for row in rows:
        name = row.get("Name", "").strip()
        authority = row.get("Authority", "").strip()
        started = row.get("Started On", "").strip()
        url = row.get("Url", "").strip()

        if not name:
            continue

        entry = f"- **{name}**"
        if authority:
            entry += f" -- {authority}"
        if started:
            entry += f" ({started})"
        if url:
            entry += f" [{url}]"
        lines.append(entry)

    return "\n".join(lines) if len(lines) > 1 else None
