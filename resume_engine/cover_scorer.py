"""Cover letter quality scorer -- no LLM required.

Analyzes a cover letter across multiple dimensions and returns a composite
health score with actionable suggestions.

Dimensions:
  - Opening hook             (20 pts)  -- grabs attention, not generic
  - Company/role specificity (25 pts)  -- names company, role, specific reasons
  - Value proposition        (25 pts)  -- what you bring, not just what you want
  - Length & conciseness     (15 pts)  -- 250-400 words is the sweet spot
  - Filler / weak language   (15 pts)  -- no cliches, generic phrases

Total: 100 pts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GENERIC_OPENERS = [
    r"^I am (writing|reaching out|applying|excited)",
    r"^I would like to (apply|express|introduce)",
    r"^Please (accept|consider|find)",
    r"^My name is",
    r"^I am a (highly|very|passionate|motivated|dedicated|driven|results-driven)",
    r"^I saw (your|this|the) (job|posting|listing|opening|ad|position|role)",
    r"^This letter is",
    r"^I am (interested in|very interested in)",
]

FILLER_PHRASES = [
    r"\bI am (very |extremely |highly |truly )?(passionate|motivated|dedicated|committed|driven|enthusiastic) (about|to)\b",
    r"\bteam player\b",
    r"\bthink outside (the )?box\b",
    r"\bgo-getter\b",
    r"\bhard worker\b",
    r"\bself-starter\b",
    r"\bresults-driven\b",
    r"\bdetail-oriented\b",
    r"\bdynamic\b",
    r"\bsynergy\b",
    r"\bresponsible for\b",
    r"\bworked on\b",
    r"\bhelped (with|to)\b",
    r"\bassisted (with|in)\b",
    r"\bvarious\b",
    r"\betc\b",
    r"\bwould be (a great|an excellent|a perfect) (fit|match|addition|candidate)\b",
    r"\bI believe I (would|will|could|can) (be|make)\b",
    r"\bstrongly (believe|feel|think) (that )?I\b",
    r"\bplease (do not hesitate|feel free) to\b",
    r"\bthank you for (your time|considering|reviewing)\b",
]

VALUE_VERB_PATTERNS = [
    r"\b(built|created|designed|developed|engineered|architected|launched|shipped)\b",
    r"\b(led|managed|directed|oversaw|owned|drove|championed)\b",
    r"\b(increased|grew|expanded|scaled|improved|optimized|accelerated|boosted)\b",
    r"\b(reduced|cut|eliminated|streamlined|simplified|automated|saved)\b",
    r"\b(delivered|achieved|exceeded|generated|produced|deployed)\b",
]

SPECIFICITY_MARKERS = [
    r"\b\d+\s*%",
    r"\$\s*\d+",
    r"\b\d+\s*(users?|customers?|clients?|team members?|engineers?|employees?|people)\b",
    r"\b\d+\s*(years?|months?)\b",
    r"\b\d+[kKmMbB]\b",
    r"\b\d+x\b",
]

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class CoverDimension:
    name: str
    score: int
    max_score: int
    suggestions: List[str] = field(default_factory=list)

    @property
    def pct(self) -> int:
        return int(round(self.score / self.max_score * 100)) if self.max_score else 0


@dataclass
class CoverScorerResult:
    total: int
    dimensions: List[CoverDimension] = field(default_factory=list)
    word_count: int = 0
    filler_matches: List[str] = field(default_factory=list)
    specificity_count: int = 0
    value_verb_count: int = 0
    has_company_name: bool = False
    has_role_name: bool = False
    generic_opener: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _word_count(text: str) -> int:
    return len(text.split())


def _strip_header(text: str) -> str:
    """Strip salutation / address lines from the top."""
    lines = text.strip().splitlines()
    body_lines = []
    skip_re = re.compile(
        r"^(dear |to whom|hiring manager|[a-z]+ [0-9]+,?\s*$|[a-z]+ [0-9]+\s+[0-9]{4}|sincerely|best regards|regards,|yours,)",
        re.IGNORECASE,
    )
    for line in lines:
        if not skip_re.match(line.strip()):
            body_lines.append(line)
    return "\n".join(body_lines)


def _first_sentence(text: str) -> str:
    """Return the first sentence of the body."""
    body = _strip_header(text).strip()
    # Match up to first period, !, or ?
    m = re.match(r"(.+?[.!?])\s", body, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fall back to first line
    first_line = body.splitlines()[0].strip() if body.splitlines() else ""
    return first_line


def _check_generic_opener(first_sentence: str) -> bool:
    """Return True if the opener is generic/weak."""
    for pat in GENERIC_OPENERS:
        if re.match(pat, first_sentence, re.IGNORECASE):
            return True
    return False


def _count_specificity(text: str) -> int:
    """Count quantified/specific markers in the text."""
    count = 0
    for pat in SPECIFICITY_MARKERS:
        count += len(re.findall(pat, text, re.IGNORECASE))
    return count


def _count_value_verbs(text: str) -> int:
    """Count value-demonstrating verbs."""
    count = 0
    for pat in VALUE_VERB_PATTERNS:
        count += len(re.findall(pat, text, re.IGNORECASE))
    return count


def _find_filler(text: str) -> List[str]:
    """Return list of filler phrases found."""
    found = []
    lower = text.lower()
    for pattern in FILLER_PHRASES:
        m = re.search(pattern, lower)
        if m:
            found.append(m.group(0).strip())
    return found


def _detect_company_name(text: str) -> bool:
    """Heuristic: text has a proper-noun company reference beyond 'the company'."""
    # Any capitalized multi-word name or well-known company pattern
    patterns = [
        r"\bat\s+[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*",  # "at Acme Corp"
        r"\b[A-Z][A-Za-z]+(?:'s)?\s+(team|product|platform|mission|company|organization|engineering|culture)\b",
    ]
    for pat in patterns:
        if re.search(pat, text):
            return True
    return False


def _detect_role_name(text: str) -> bool:
    """Check if the cover letter references a specific role title."""
    role_patterns = [
        r"\b(senior|junior|lead|principal|staff|mid(-level)?)\s+\w+\s+(engineer|developer|designer|manager|analyst|scientist|architect)\b",
        r"\b(software|backend|frontend|full.?stack|data|machine learning|ml|ai|platform|infrastructure|devops|cloud|mobile|ios|android)\s+(engineer|developer|architect)\b",
        r"\b(product|engineering|project|program|technical)\s+(manager|director|lead|head)\b",
        r"\b(UX|UI|design|product)\s+(designer|researcher|lead|manager)\b",
        r"\bthe\s+([\w\s]+?)?\s+(role|position|opportunity)\b",
        r"\bapplying for.*?(position|role|job|opening)\b",
    ]
    lower = text.lower()
    for pat in role_patterns:
        if re.search(pat, lower):
            return True
    return False


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------


def _score_opening_hook(text: str) -> tuple[CoverDimension, bool]:
    first = _first_sentence(text)
    generic = _check_generic_opener(first)

    if not first:
        score = 0
        suggestions = ["Cover letter body appears empty. Add a compelling opening."]
    elif generic:
        score = 5
        suggestions = [
            'Your opening is generic (starts with "I am writing..." or similar). '
            "Lead with a specific achievement, a bold claim, or a direct connection "
            'to the company. Example: "When I shipped X at Y, I reduced Z by 40%..." '
            "or name-drop something specific about the company first."
        ]
    else:
        # Check if opener has numbers or a named company/project
        has_hook = bool(
            re.search(r"\d+|built|shipped|led|launched|reduced|grew|created|designed", first, re.IGNORECASE)
        )
        score = 20 if has_hook else 14
        suggestions = (
            []
            if has_hook
            else [
                "Opening is non-generic but could be stronger. "
                "Add a specific metric or named project to make it memorable."
            ]
        )

    return CoverDimension(
        name="Opening Hook",
        score=score,
        max_score=20,
        suggestions=suggestions,
    ), generic


def _score_specificity(text: str, has_company: bool, has_role: bool) -> CoverDimension:
    specific_count = _count_specificity(text)
    score = 0
    suggestions = []

    # Company mention
    if has_company:
        score += 10
    else:
        suggestions.append(
            "Name the company you are applying to. Generic letters that omit the "
            "company name are easy to spot and less persuasive."
        )

    # Role mention
    if has_role:
        score += 8
    else:
        suggestions.append(
            "Reference the specific role title in your letter. "
            "It shows intent and helps ATS parsing."
        )

    # Quantified specifics
    if specific_count >= 3:
        score += 7
    elif specific_count >= 1:
        score += 4
        suggestions.append(
            f"Only {specific_count} specific metric(s) found. "
            "Add more numbers (percentages, team sizes, impact) to be concrete."
        )
    else:
        suggestions.append(
            "No specific metrics found. Include at least 2-3 quantified achievements "
            "(e.g. 'grew revenue by 30%', 'managed a team of 8')."
        )

    return CoverDimension(
        name="Company / Role Specificity",
        score=min(score, 25),
        max_score=25,
        suggestions=suggestions,
    )


def _score_value_proposition(text: str) -> tuple[CoverDimension, int]:
    verb_count = _count_value_verbs(text)
    specific_count = _count_specificity(text)

    # Penalize "I want" heavy letters vs "I bring/built/delivered" letters
    want_patterns = [
        r"\bI (want|hope|wish|am looking) to\b",
        r"\bI am seeking\b",
        r"\bthis (role|position|opportunity) (would|will) (allow|help|enable|let) me\b",
        r"\bI (could|would) (learn|grow|develop|gain)\b",
    ]
    want_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in want_patterns)

    score = 0
    suggestions = []

    if verb_count >= 5:
        score += 15
    elif verb_count >= 2:
        score += 10
        suggestions.append(
            f"Only {verb_count} action verbs demonstrating value. "
            "Use more verbs like: built, led, reduced, launched, scaled."
        )
    else:
        score += 3
        suggestions.append(
            "Your letter focuses more on what you want than what you bring. "
            "Lead with concrete contributions: 'I built X', 'I reduced Y by Z%'."
        )

    if specific_count >= 2:
        score += 10
    elif specific_count == 1:
        score += 5
        suggestions.append(
            "Add more quantified achievements to the value proposition section."
        )
    else:
        suggestions.append(
            "No numbers or metrics in your value case. Add at least 2 concrete results."
        )

    if want_count > 2:
        score = max(0, score - 5)
        suggestions.append(
            f"Your letter has {want_count} 'what I want/hope/seek' phrases. "
            "Reframe to focus on what you bring, not what you want to gain."
        )

    return CoverDimension(
        name="Value Proposition",
        score=min(score, 25),
        max_score=25,
        suggestions=suggestions,
    ), verb_count


def _score_length(text: str) -> tuple[CoverDimension, int]:
    wc = _word_count(text)
    suggestions = []

    if wc < 100:
        score = 3
        suggestions.append(
            f"Cover letter is very short ({wc} words). Aim for 250-400 words."
        )
    elif wc < 200:
        score = 8
        suggestions.append(
            f"Cover letter is short ({wc} words). Aim for 250-400 words "
            "to fully convey your fit."
        )
    elif wc <= 400:
        score = 15  # Sweet spot
    elif wc <= 550:
        score = 10
        suggestions.append(
            f"Cover letter is a bit long ({wc} words). Trim to 250-400 words -- "
            "hiring managers skim, so every sentence must earn its place."
        )
    else:
        score = 4
        suggestions.append(
            f"Cover letter is too long ({wc} words). Cut to under 400 words. "
            "Remove generic statements and keep only your strongest 3-4 points."
        )

    return CoverDimension(
        name="Length & Conciseness",
        score=score,
        max_score=15,
        suggestions=suggestions,
    ), wc


def _score_filler(text: str) -> tuple[CoverDimension, list]:
    matches = _find_filler(text)
    unique = list(dict.fromkeys(matches))

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
            f"Filler or cliche language detected: {quoted}. "
            "Replace with specific, results-driven language. "
            "Say what you actually did, not how you felt about doing it."
        )

    return CoverDimension(
        name="Filler / Weak Language",
        score=score,
        max_score=15,
        suggestions=suggestions,
    ), unique


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_cover_letter(text: str) -> CoverScorerResult:
    """Score a cover letter and return a CoverScorerResult."""
    has_company = _detect_company_name(text)
    has_role = _detect_role_name(text)

    opening_dim, generic_opener = _score_opening_hook(text)
    specificity_dim = _score_specificity(text, has_company, has_role)
    value_dim, verb_count = _score_value_proposition(text)
    length_dim, wc = _score_length(text)
    filler_dim, filler_list = _score_filler(text)

    dimensions = [opening_dim, specificity_dim, value_dim, length_dim, filler_dim]
    total = sum(d.score for d in dimensions)

    return CoverScorerResult(
        total=total,
        dimensions=dimensions,
        word_count=wc,
        filler_matches=filler_list,
        specificity_count=_count_specificity(text),
        value_verb_count=verb_count,
        has_company_name=has_company,
        has_role_name=has_role,
        generic_opener=generic_opener,
    )
