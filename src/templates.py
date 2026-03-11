"""Template system for resume-engine -- different resume styles and layouts."""

import re
from pathlib import Path
from typing import Optional

# Built-in templates directory (bundled with the package)
_BUILTIN_DIR = Path(__file__).parent.parent / "templates"

# User templates directory (~/.resume-engine/templates/)
_USER_DIR = Path.home() / ".resume-engine" / "templates"


def _search_dirs() -> list[Path]:
    """Return directories to search (user first, built-in second)."""
    dirs = []
    if _USER_DIR.exists():
        dirs.append(_USER_DIR)
    if _BUILTIN_DIR.exists():
        dirs.append(_BUILTIN_DIR)
    return dirs


def _parse_template_file(path: Path) -> dict:
    """Parse a template .md file with optional YAML-like front matter."""
    content = path.read_text()
    name = path.stem.capitalize()
    description = ""
    instructions = content

    fm = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if fm:
        for line in fm.group(1).splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                description = line.split(":", 1)[1].strip()
        instructions = fm.group(2).strip()

    return {
        "name": name,
        "slug": path.stem.lower(),
        "description": description,
        "instructions": instructions,
        "path": str(path),
        "source": "user" if _USER_DIR in path.parents else "built-in",
    }


def list_templates() -> list[dict]:
    """Return all available templates sorted by name."""
    seen: dict[str, dict] = {}
    for d in _search_dirs():
        for path in sorted(d.glob("*.md")):
            slug = path.stem.lower()
            if slug not in seen:  # user templates shadow built-ins
                seen[slug] = _parse_template_file(path)
    return sorted(seen.values(), key=lambda t: t["name"])


def get_template(slug: str) -> Optional[dict]:
    """Get a template by slug (case-insensitive). Returns None if not found."""
    slug = slug.lower()
    for d in _search_dirs():
        path = d / f"{slug}.md"
        if path.exists():
            return _parse_template_file(path)
    return None


def get_template_instructions(slug: str) -> str:
    """Return layout instructions string for a template slug.

    Returns empty string for 'default', None, or unknown slugs.
    """
    if not slug or slug.lower() in ("default", "none"):
        return ""
    t = get_template(slug)
    return t["instructions"] if t else ""


def template_choices() -> list[str]:
    """Return valid slug list for CLI choices (includes 'default')."""
    return ["default"] + [t["slug"] for t in list_templates()]
