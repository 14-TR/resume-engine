"""Resume quality scorer -- no LLM required.

Analyzes a master resume across multiple dimensions and returns a composite
health score with actionable suggestions.

Dimensions:
  - Section completeness  (25 pts)
  - Quantified achievements (25 pts)
  - Action verb usage       (20 pts)
  - Length & density        (15 pts)
  - Filler / weak language  (15 pts)

Total: 100 pts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EXPECTED_SECTIONS = [
    "summary",
    "experience",
    "education",
    "skills",
    "contact",
]

OPTIONAL_SECTIONS = [
    "projects",
    "certifications",
    "awards",
    "volunteer",
    "publications",
]

STRONG_ACTION_VERBS = {
    "achieved", "accelerated", "architected", "automated", "built",
    "championed", "collaborated", "created", "cut", "decreased",
    "defined", "delivered", "deployed", "designed", "developed",
    "drove", "eliminated", "engineered", "established", "exceeded",
    "executed", "expanded", "facilitated", "generated", "grew",
    "identified", "implemented", "improved", "increased", "integrated",
    "launched", "led", "managed", "mentored", "migrated",
    "negotiated", "optimized", "oversaw", "partnered", "piloted",
    "planned", "produced", "reduced", "refactored", "resolved",
    "scaled", "shipped", "simplified", "spearheaded", "streamlined",
    "trained", "transformed", "unified",
}

FILLER_PHRASES = [
    r"\bresponsible for\b",
    r"\bwas in charge of\b",
    r"\bworked on\b",
    r"\bhelped (with|to)\b",
    r"\bassisted (with|in)\b",
    r"\bvarious\b",
    r"\bseveral\b",
    r"\bmany\b",
    r"\ba lot of\b",
    r"\betc\b",
    r"\band so on\b",
    r"\bteam player\b",
    r"\bhard worker\b",
    r"\bgo-getter\b",
    r"\bthink outside the box\b",
    r"\bsynergy\b",
    r"\bself-starter\b",
    r"\bpassionate (about)?\b",
    r"\bdetail-oriented\b",
    r"\bdynamic\b",
]


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class DimensionResult:
    name: str
    score: int
    max_score: int
    suggestions: List[str] = field(default_factory=list)

    @property
    def pct(self) -> int:
        return int(round(self.score / self.max_score * 100)) if self.max_score else 0


@dataclass
class ScorerResult:
    total: int  # 0-100
    dimensions: List[DimensionResult] = field(default_factory=list)
    found_sections: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    quantified_count: int = 0
    bullet_count: int = 0
    action_verb_count: int = 0
    filler_matches: List[str] = field(default_factory=list)
    word_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_section_headings(text: str) -> List[str]:
    """Return lowercase section heading names found in text."""
    heading_re = re.compile(r"^#+\s+(.+)$|^(.+)\n[=\-]{3,}$", re.MULTILINE)
    headings = []
    for m in heading_re.finditer(text):
        h = (m.group(1) or m.group(2) or "").strip().lower()
        if h:
            headings.append(h)
    return headings


def _count_quantified_bullets(text: str) -> tuple[int, int]:
    """Return (quantified_bullets, total_bullets)."""
    bullet_re = re.compile(r"^[\s]*[-*+]\s+(.+)$", re.MULTILINE)
    bullets = bullet_re.findall(text)
    quantified = sum(
        1 for b in bullets if re.search(r"\d+[%x]?|\$\d+|\d+\s*(k|m|b)\b", b, re.IGNORECASE)
    )
    return quantified, len(bullets)


def _count_action_verbs(text: str) -> tuple[int, set[str]]:
    """Return (count, set of found action verbs)."""
    bullet_re = re.compile(r"^[\s]*[-*+]\s+([A-Z][a-z]+)", re.MULTILINE)
    starts = [m.group(1).lower() for m in bullet_re.finditer(text)]
    found = {v for v in starts if v in STRONG_ACTION_VERBS}
    return len(found), found


def _find_filler(text: str) -> List[str]:
    """Return list of filler phrases found."""
    found = []
    lower = text.lower()
    for pattern in FILLER_PHRASES:
        m = re.search(pattern, lower)
        if m:
            found.append(m.group(0).strip())
    return found


def _word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------

def _score_sections(text: str) -> DimensionResult:
    headings = _extract_section_headings(text)

    found = []
    missing = []
    for sec in EXPECTED_SECTIONS:
        # Fuzzy: any heading containing the key term
        if any(sec in h for h in headings):
            found.append(sec)
        else:
            missing.append(sec)

    score = int(round(len(found) / len(EXPECTED_SECTIONS) * 25))
    suggestions = []
    if missing:
        suggestions.append(
            f"Missing required section(s): {', '.join(missing)}. "
            "Add these headings to your resume."
        )

    # Bonus sections (informational only)
    found_optional = [s for s in OPTIONAL_SECTIONS if any(s in h for h in headings)]

    return DimensionResult(
        name="Section Completeness",
        score=score,
        max_score=25,
        suggestions=suggestions,
    ), found, missing, found_optional  # type: ignore[return-value]


def _score_quantified(text: str) -> DimensionResult:
    quantified, total = _count_quantified_bullets(text)

    if total == 0:
        score = 0
        pct = 0
    else:
        pct = quantified / total
        score = int(round(min(pct * 2, 1.0) * 25))  # 50% quantified = full marks

    suggestions = []
    if total == 0:
        suggestions.append(
            "No bullet points found. Use bullet points under each role to describe achievements."
        )
    elif pct < 0.3:
        suggestions.append(
            f"Only {quantified}/{total} bullet points have numbers/metrics. "
            "Aim for at least 50% of bullets to include quantified results "
            "(e.g. 'Reduced deploy time by 40%')."
        )
    elif pct < 0.5:
        suggestions.append(
            f"{quantified}/{total} bullets are quantified -- good start. "
            "Try to add metrics to more bullets (percentages, dollar amounts, counts)."
        )

    return DimensionResult(
        name="Quantified Achievements",
        score=score,
        max_score=25,
        suggestions=suggestions,
    )


def _score_action_verbs(text: str) -> DimensionResult:
    count, found_verbs = _count_action_verbs(text)
    _, total_bullets = _count_quantified_bullets(text)

    # Want at least 10 distinct strong verbs for full marks
    score = int(round(min(count / 10, 1.0) * 20))

    suggestions = []
    if count == 0:
        suggestions.append(
            "No strong action verbs detected at the start of bullet points. "
            "Begin bullets with verbs like: Led, Built, Increased, Launched, Reduced."
        )
    elif count < 5:
        suggestions.append(
            f"Only {count} distinct strong action verb(s) found. "
            "Vary your language -- use verbs like: "
            + ", ".join(sorted(STRONG_ACTION_VERBS - found_verbs)[:8])
            + "."
        )

    return DimensionResult(
        name="Action Verb Usage",
        score=score,
        max_score=20,
        suggestions=suggestions,
    )


def _score_length(text: str) -> DimensionResult:
    wc = _word_count(text)
    suggestions = []

    # Ideal range: 400-800 words for a one-page resume
    if wc < 200:
        score = 5
        suggestions.append(
            f"Resume is very short ({wc} words). Aim for 400-800 words to provide enough detail."
        )
    elif wc < 350:
        score = 10
        suggestions.append(
            f"Resume is on the short side ({wc} words). Consider adding more detail to key roles."
        )
    elif wc <= 900:
        score = 15
    elif wc <= 1200:
        score = 10
        suggestions.append(
            f"Resume is quite long ({wc} words). Trim to 400-800 words for best ATS results."
        )
    else:
        score = 5
        suggestions.append(
            f"Resume is very long ({wc} words). Cut to 400-800 words -- focus on last 10 years."
        )

    return DimensionResult(
        name="Length & Density",
        score=score,
        max_score=15,
        suggestions=suggestions,
    )


def _score_filler(text: str) -> DimensionResult:
    matches = _find_filler(text)
    unique = list(dict.fromkeys(matches))  # dedupe while preserving order

    if len(unique) == 0:
        score = 15
    elif len(unique) <= 2:
        score = 10
    elif len(unique) <= 4:
        score = 5
    else:
        score = 0

    suggestions = []
    if unique:
        quoted = ", ".join(f'"{p}"' for p in unique[:6])
        suggestions.append(
            f"Weak or filler language detected: {quoted}. "
            "Replace with specific, results-driven language."
        )

    return DimensionResult(
        name="Filler / Weak Language",
        score=score,
        max_score=15,
        suggestions=suggestions,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_resume(text: str) -> ScorerResult:
    """Score a resume and return a ScorerResult."""

    section_dim, found_sections, missing_sections, _ = _score_sections(text)  # type: ignore[misc]
    quant_dim = _score_quantified(text)
    verb_dim = _score_action_verbs(text)
    length_dim = _score_length(text)
    filler_dim = _score_filler(text)

    dimensions = [section_dim, quant_dim, verb_dim, length_dim, filler_dim]
    total = sum(d.score for d in dimensions)

    quantified, total_bullets = _count_quantified_bullets(text)
    verb_count, _ = _count_action_verbs(text)

    return ScorerResult(
        total=total,
        dimensions=dimensions,
        found_sections=found_sections,
        missing_sections=missing_sections,
        quantified_count=quantified,
        bullet_count=total_bullets,
        action_verb_count=verb_count,
        filler_matches=_find_filler(text),
        word_count=_word_count(text),
    )
