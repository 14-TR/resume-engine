"""Job fit assessment -- should I apply? LLM + ATS combined analysis.

Evaluates resume-to-job compatibility across five dimensions:
  - ATS keyword match        (20 pts)
  - Required skills coverage (25 pts)
  - Seniority/level match    (20 pts)
  - Industry/domain fit      (15 pts)
  - Overall LLM assessment   (20 pts)

Returns a composite 0-100 fit score with a hire recommendation and
a concise list of strengths, gaps, and a plain-English verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from .ats import analyze as ats_analyze
from .llm import complete

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FitDimension:
    name: str
    score: int
    max_score: int
    notes: List[str] = field(default_factory=list)

    @property
    def pct(self) -> int:
        return round(self.score / self.max_score * 100) if self.max_score > 0 else 0


@dataclass
class FitResult:
    total: int
    dimensions: List[FitDimension]
    verdict: str  # "Strong fit" | "Moderate fit" | "Stretch role" | "Poor fit"
    recommendation: str  # "Apply" | "Apply with caution" | "Skip"
    strengths: List[str]
    gaps: List[str]
    raw_analysis: str
    ats_score: int


# ---------------------------------------------------------------------------
# LLM prompt
# ---------------------------------------------------------------------------

_FIT_PROMPT = """You are a senior career advisor. Evaluate how well this candidate's resume matches the job posting.

Assess four dimensions (be specific, reference real items from the resume and job):

1. REQUIRED SKILLS COVERAGE (25 pts)
   - How many required skills/qualifications does the candidate actually have?
   - Penalize hard mismatches (e.g. job requires 5+ years, candidate has 2)
   - Reward partial matches (e.g. related tech, transferable skills)
   Score: X/25

2. SENIORITY AND LEVEL MATCH (20 pts)
   - Does the candidate's experience level match the role level?
   - Consider: years of experience, scope of past work, management/lead history
   Score: X/20

3. INDUSTRY AND DOMAIN FIT (15 pts)
   - Has the candidate worked in a similar domain/industry?
   - Relevant context: same vertical, similar company size, comparable tech stack
   Score: X/15

4. OVERALL ASSESSMENT (20 pts)
   - Holistic judgment: narrative arc, career progression fit, red flags
   - Does this role make sense as the candidate's next step?
   Score: X/20

Then provide:
STRENGTHS:
- [bullet: specific strength from resume that maps to this job]
- [bullet]
- [bullet]

GAPS:
- [bullet: specific gap or risk]
- [bullet]

VERDICT: [one sentence plain-English verdict -- no em dashes, use hyphens only]

RECOMMENDATION: Apply | Apply with caution | Skip

RULES:
- Be honest and direct -- job seekers need accurate signal, not false hope
- Reference specific items from resume and job (company names, skills, years)
- No em dashes -- use hyphens only
- Keep each bullet under 20 words

RESUME:
{resume}

JOB POSTING:
{job}"""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_score(text: str, label: str, max_pts: int) -> int:
    """Extract a score like 'Score: 18/25' from LLM output."""
    # Try 'Score: X/max' near the label
    pattern = rf"(?i){re.escape(label)}.*?score:\s*(\d+)/{max_pts}"
    m = re.search(pattern, text, re.DOTALL)
    if m:
        return min(int(m.group(1)), max_pts)

    # Try generic 'Score: X/max' anywhere
    pattern2 = rf"Score:\s*(\d+)/{max_pts}"
    for m2 in re.finditer(pattern2, text, re.IGNORECASE):
        return min(int(m2.group(1)), max_pts)

    return 0


def _parse_bullets(text: str, section: str) -> List[str]:
    """Extract bullet items under a section header."""
    pattern = rf"(?i){re.escape(section)}:\s*\n((?:\s*[-*]\s*.+\n?)+)"
    m = re.search(pattern, text)
    if not m:
        return []
    raw = m.group(1)
    items = []
    for line in raw.splitlines():
        stripped = line.strip().lstrip("-*").strip()
        if stripped:
            items.append(stripped)
    return items


def _parse_verdict(text: str) -> str:
    m = re.search(r"(?i)VERDICT:\s*(.+)", text)
    if m:
        return m.group(1).strip().rstrip(".")
    return ""


def _parse_recommendation(text: str) -> str:
    m = re.search(r"(?i)RECOMMENDATION:\s*(Apply with caution|Apply|Skip)", text)
    if m:
        return m.group(1).strip()
    # Fuzzy fallback
    lower = text.lower()
    if "skip" in lower:
        return "Skip"
    if "caution" in lower:
        return "Apply with caution"
    if "apply" in lower:
        return "Apply"
    return "Apply with caution"


def _verdict_from_score(total: int) -> str:
    if total >= 80:
        return "Strong fit"
    elif total >= 65:
        return "Moderate fit"
    elif total >= 45:
        return "Stretch role"
    else:
        return "Poor fit"


def _notes_from_text(raw: str, section_label: str) -> List[str]:
    """Extract any note lines appearing after a section header."""
    pattern = rf"(?i){re.escape(section_label)}.*?\n((?:[^A-Z\n].*\n)*)"
    m = re.search(pattern, raw, re.DOTALL)
    if not m:
        return []
    lines = [
        ln.strip()
        for ln in m.group(1).splitlines()
        if ln.strip() and not ln.strip().startswith("Score")
    ]
    return lines[:3]


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------


def assess_fit(
    resume_text: str,
    job_text: str,
    model: str = "ollama",
    ats_top_n: int = 30,
) -> FitResult:
    """Run full fit assessment: ATS + LLM analysis."""

    # --- ATS dimension ---
    ats_result = ats_analyze(resume_text, job_text, top_n=ats_top_n)
    ats_pct = ats_result["score"]  # 0-100
    ats_pts = round(ats_pct * 20 / 100)  # scale to 20pts

    ats_dim = FitDimension(
        name="ATS Keyword Match",
        score=ats_pts,
        max_score=20,
        notes=[
            f"Matched {ats_result['matched_count']}/{ats_result['total_keywords']} keywords",
        ],
    )

    # --- LLM dimensions ---
    prompt = _FIT_PROMPT.format(resume=resume_text, job=job_text)
    raw = complete(prompt, model=model)

    skills_pts = _parse_score(raw, "REQUIRED SKILLS COVERAGE", 25)
    seniority_pts = _parse_score(raw, "SENIORITY AND LEVEL MATCH", 20)
    domain_pts = _parse_score(raw, "INDUSTRY AND DOMAIN FIT", 15)
    overall_pts = _parse_score(raw, "OVERALL ASSESSMENT", 20)

    # Fallback: if all zeros (LLM didn't follow format), estimate from recommendation
    if skills_pts + seniority_pts + domain_pts + overall_pts == 0:
        rec = _parse_recommendation(raw)
        if rec == "Apply":
            skills_pts, seniority_pts, domain_pts, overall_pts = 20, 16, 12, 16
        elif rec == "Apply with caution":
            skills_pts, seniority_pts, domain_pts, overall_pts = 14, 12, 8, 12
        else:
            skills_pts, seniority_pts, domain_pts, overall_pts = 8, 8, 6, 8

    dimensions = [
        ats_dim,
        FitDimension(name="Required Skills Coverage", score=skills_pts, max_score=25),
        FitDimension(name="Seniority / Level Match", score=seniority_pts, max_score=20),
        FitDimension(name="Industry / Domain Fit", score=domain_pts, max_score=15),
        FitDimension(name="Overall Assessment", score=overall_pts, max_score=20),
    ]

    total = sum(d.score for d in dimensions)
    total = min(total, 100)

    verdict_llm = _parse_verdict(raw)
    verdict = verdict_llm if verdict_llm else _verdict_from_score(total)

    recommendation = _parse_recommendation(raw)

    strengths = _parse_bullets(raw, "STRENGTHS")
    gaps = _parse_bullets(raw, "GAPS")

    return FitResult(
        total=total,
        dimensions=dimensions,
        verdict=verdict,
        recommendation=recommendation,
        strengths=strengths,
        gaps=gaps,
        raw_analysis=raw,
        ats_score=ats_pct,
    )
