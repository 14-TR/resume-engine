"""Resume diff module -- compare master vs tailored resume with rich output."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class SectionDiff:
    """Diff result for a single resume section."""

    name: str
    added: List[str]
    removed: List[str]
    changed_lines: int
    total_lines: int

    @property
    def is_changed(self) -> bool:
        return bool(self.added or self.removed)

    @property
    def change_pct(self) -> int:
        if self.total_lines == 0:
            return 0
        return min(100, round(100 * self.changed_lines / self.total_lines))


@dataclass
class ResumeDiff:
    """Full diff result between two resume texts."""

    sections: List[SectionDiff]
    added_lines: int
    removed_lines: int
    total_original_lines: int
    unified_diff: List[str]

    @property
    def change_score(self) -> int:
        """0-100 percentage of lines changed."""
        if self.total_original_lines == 0:
            return 0
        changed = self.added_lines + self.removed_lines
        return min(100, round(100 * changed / max(self.total_original_lines, 1)))


_SECTION_RE = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)


def _split_sections(text: str) -> List[Tuple[str, str]]:
    """Split markdown text into (section_name, content) pairs."""
    lines = text.splitlines(keepends=True)
    sections: List[Tuple[str, str]] = []
    current_name = "_preamble"
    current_lines: List[str] = []

    for line in lines:
        m = _SECTION_RE.match(line.rstrip())
        if m:
            if current_lines:
                sections.append((current_name, "".join(current_lines)))
            current_name = m.group(1).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_name, "".join(current_lines)))

    return sections


def compute_diff(original: str, tailored: str) -> ResumeDiff:
    """Compute a structured diff between original and tailored resume."""
    orig_lines = original.splitlines(keepends=True)
    tail_lines = tailored.splitlines(keepends=True)

    # Unified diff for raw output
    unified = list(
        difflib.unified_diff(
            orig_lines,
            tail_lines,
            fromfile="original",
            tofile="tailored",
            lineterm="",
        )
    )

    # Count totals
    added = [l for l in unified if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in unified if l.startswith("-") and not l.startswith("---")]

    # Section-by-section diff
    orig_sections = dict(_split_sections(original))
    tail_sections = dict(_split_sections(tailored))

    all_section_names: List[str] = []
    seen = set()
    for name in list(orig_sections.keys()) + list(tail_sections.keys()):
        if name not in seen:
            all_section_names.append(name)
            seen.add(name)

    section_diffs: List[SectionDiff] = []
    for name in all_section_names:
        if name == "_preamble":
            continue
        orig_text = orig_sections.get(name, "")
        tail_text = tail_sections.get(name, "")

        orig_sec_lines = orig_text.splitlines(keepends=True)
        tail_sec_lines = tail_text.splitlines(keepends=True)

        sec_unified = list(
            difflib.unified_diff(orig_sec_lines, tail_sec_lines, lineterm="")
        )
        sec_added = [l for l in sec_unified if l.startswith("+") and not l.startswith("+++")]
        sec_removed = [l for l in sec_unified if l.startswith("-") and not l.startswith("---")]

        section_diffs.append(
            SectionDiff(
                name=name,
                added=[l[1:] for l in sec_added],
                removed=[l[1:] for l in sec_removed],
                changed_lines=len(sec_added) + len(sec_removed),
                total_lines=max(len(orig_sec_lines), 1),
            )
        )

    return ResumeDiff(
        sections=section_diffs,
        added_lines=len(added),
        removed_lines=len(removed),
        total_original_lines=len(orig_lines),
        unified_diff=unified,
    )


def _bar(pct: int, width: int = 20) -> str:
    """Render a simple ASCII bar."""
    filled = round(width * pct / 100)
    return "[" + "#" * filled + "-" * (width - filled) + "]"
