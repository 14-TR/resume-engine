"""Grounded output validation for tailored resumes and cover letters."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Iterable

COMMON_SECTION_WORDS = {
    "summary", "experience", "skills", "education", "projects", "certifications",
    "contact", "professional", "technical", "leadership", "employment", "history",
    "highlights", "resume", "letter", "dear", "sincerely", "regards", "phone",
    "email", "linkedin", "city", "state", "remote", "hybrid", "present",
}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "of", "on", "or", "that", "the", "to", "with", "using", "used", "built",
    "led", "managed", "developed", "delivered", "supported", "improved", "created",
}
TITLE_WORDS = {
    "engineer", "developer", "manager", "director", "lead", "analyst", "architect",
    "consultant", "specialist", "associate", "intern", "principal", "staff", "senior",
    "junior", "president", "coordinator", "designer", "administrator", "owner",
}
SKILL_PHRASES = [
    "python", "java", "javascript", "typescript", "go", "aws", "azure", "gcp",
    "kubernetes", "docker", "terraform", "sql", "postgresql", "mysql", "react",
    "node", "django", "flask", "fastapi", "graphql", "rest", "machine learning",
    "ai", "llm", "ollama", "openai", "anthropic", "click", "rich", "httpx",
    "git", "github actions", "linux", "agile", "scrum", "ci/cd",
]


@dataclass
class ValidationIssue:
    severity: str
    category: str
    message: str
    evidence: str = ""
    suggestion: str = ""


@dataclass
class ValidationTargetResult:
    label: str
    score: int
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class ValidationReport:
    targets: list[ValidationTargetResult]


def _normalize_token(token: str) -> str:
    return re.sub(r"[^a-z0-9+/#.-]", "", token.lower()).strip(".-")


def _tokenize(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9][A-Za-z0-9+/#.-]*", text)
    return [_normalize_token(tok) for tok in raw if _normalize_token(tok)]


def _meaningful_tokens(text: str) -> set[str]:
    return {
        tok for tok in _tokenize(text)
        if len(tok) > 2 and tok not in STOPWORDS and not tok.isdigit()
    }


def _extract_bullets(text: str) -> list[str]:
    return [ln.strip()[2:].strip() for ln in text.splitlines() if ln.strip().startswith('- ')]


def _extract_date_ranges(text: str) -> set[str]:
    patterns = [
        r"\b(?:19|20)\d{2}\s*[-/]\s*(?:19|20)\d{2}\b",
        r"\b(?:19|20)\d{2}\s*[-/]\s*(?:Present|Current|Now)\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2}\s*[-/]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2}\s*[-/]\s*(?:Present|Current|Now)\b",
    ]
    values = set()
    for pattern in patterns:
        values.update(m.group(0).strip() for m in re.finditer(pattern, text, re.IGNORECASE))
    return values


def _extract_companies(text: str) -> set[str]:
    companies = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for pattern in [
            r"--\s*([^()|]+?)\s*(?:\(|$)",
            r"\bat\s+([A-Z][A-Za-z0-9&.,'/-]+(?:\s+[A-Z][A-Za-z0-9&.,'/-]+){0,4})",
        ]:
            for match in re.finditer(pattern, stripped):
                candidate = match.group(1).strip(" -|,")
                if candidate and len(candidate) > 2:
                    companies.add(candidate)
    return companies


def _extract_titles(text: str) -> set[str]:
    titles = set()
    for line in text.splitlines():
        stripped = line.strip().lstrip('#').strip()
        if not stripped:
            continue
        if '--' in stripped:
            left = stripped.split('--', 1)[0].strip()
            if any(word in left.lower() for word in TITLE_WORDS):
                titles.add(left)
        elif re.search(r"\b(?:as|role:?|title:?)\b", stripped, re.IGNORECASE):
            if any(word in stripped.lower() for word in TITLE_WORDS):
                titles.add(stripped)
    return titles


def _extract_capitalized_phrases(text: str) -> set[str]:
    phrases = set()
    for match in re.finditer(r"\b[A-Z][A-Za-z0-9&./+-]+(?:\s+[A-Z][A-Za-z0-9&./+-]+){0,3}\b", text):
        phrase = match.group(0).strip()
        normalized = phrase.lower()
        if normalized in COMMON_SECTION_WORDS:
            continue
        if len(phrase) <= 2:
            continue
        phrases.add(phrase)
    return phrases


def _extract_skill_mentions(text: str) -> set[str]:
    lower = text.lower()
    found = set()
    for phrase in SKILL_PHRASES:
        if phrase in lower:
            found.add(phrase)
    return found


def _line_similarity(line: str, candidates: Iterable[str]) -> float:
    best = 0.0
    normalized = line.strip().lower()
    for candidate in candidates:
        score = SequenceMatcher(None, normalized, candidate.strip().lower()).ratio()
        if score > best:
            best = score
    return best


def _issue_weight(issue: ValidationIssue) -> int:
    return {"high": 18, "medium": 10, "low": 4}.get(issue.severity, 6)


def _dedupe_issues(issues: list[ValidationIssue]) -> list[ValidationIssue]:
    seen = set()
    result = []
    for issue in issues:
        key = (issue.category, issue.message, issue.evidence)
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result


def validate_text(master_text: str, job_text: str, output_text: str, label: str) -> ValidationTargetResult:
    issues: list[ValidationIssue] = []

    master_tokens = _meaningful_tokens(master_text)
    job_tokens = _meaningful_tokens(job_text)
    grounded_tokens = master_tokens | job_tokens
    master_bullets = _extract_bullets(master_text)

    master_dates = _extract_date_ranges(master_text)
    output_dates = _extract_date_ranges(output_text)
    for value in sorted(output_dates - master_dates):
        issues.append(ValidationIssue(
            severity="high",
            category="date drift",
            message="Output includes a date range not found in the master resume.",
            evidence=value,
            suggestion="Verify the role dates against the source resume.",
        ))

    master_companies = _extract_companies(master_text)
    allowed_companies = {c.lower() for c in master_companies} | {c.lower() for c in _extract_companies(job_text)}
    for company in sorted(_extract_companies(output_text)):
        if company.lower() not in allowed_companies:
            issues.append(ValidationIssue(
                severity="high",
                category="company drift",
                message="Output mentions a company not grounded in the source inputs.",
                evidence=company,
                suggestion="Keep employer names anchored to the master resume and target employer only.",
            ))

    master_titles = _extract_titles(master_text)
    job_titles = _extract_titles(job_text)
    allowed_titles = {t.lower() for t in master_titles | job_titles}
    for title in sorted(_extract_titles(output_text)):
        if title.lower() not in allowed_titles:
            issues.append(ValidationIssue(
                severity="medium",
                category="title drift",
                message="Output includes a role title that does not appear in the source inputs.",
                evidence=title,
                suggestion="Check whether the wording should match the original title more closely.",
            ))

    allowed_phrases = {p.lower() for p in _extract_capitalized_phrases(master_text)} | {p.lower() for p in _extract_capitalized_phrases(job_text)}
    for phrase in sorted(_extract_capitalized_phrases(output_text)):
        lower = phrase.lower()
        if lower not in allowed_phrases and lower not in COMMON_SECTION_WORDS:
            issues.append(ValidationIssue(
                severity="low",
                category="new proper noun",
                message="Output introduces a named entity not seen in the source inputs.",
                evidence=phrase,
                suggestion="Confirm this name is real and supported before sending.",
            ))

    for bullet in _extract_bullets(output_text):
        similarity = _line_similarity(bullet, master_bullets)
        novel = [tok for tok in _meaningful_tokens(bullet) if tok not in grounded_tokens]
        has_metric = bool(re.search(r"\b\d+(?:[%+,]|\s*(?:million|billion|k|x|years?|months?))", bullet, re.IGNORECASE))
        if has_metric and novel:
            issues.append(ValidationIssue(
                severity="high",
                category="unsupported claim",
                message="Bullet introduces metrics or specifics not grounded in the source inputs.",
                evidence=bullet,
                suggestion="Only keep metrics that exist in the master resume or can be verified.",
            ))
        elif similarity < 0.33 and len(novel) >= 3:
            issues.append(ValidationIssue(
                severity="medium",
                category="suspicious rewrite",
                message="Bullet departs substantially from the closest source bullet.",
                evidence=bullet,
                suggestion="Compare this line to the source and trim invented detail.",
            ))

    output_skills = _extract_skill_mentions(output_text)
    allowed_skills = _extract_skill_mentions(master_text) | _extract_skill_mentions(job_text)
    for skill in sorted(output_skills - allowed_skills):
        issues.append(ValidationIssue(
            severity="medium",
            category="unsupported skill",
            message="Output claims a skill not found in the master resume or job posting.",
            evidence=skill,
            suggestion="Remove or verify the skill before using this output.",
        ))

    issues = _dedupe_issues(issues)
    penalty = sum(_issue_weight(issue) for issue in issues)
    score = max(0, 100 - penalty)
    return ValidationTargetResult(label=label, score=score, issues=issues)


def validate_outputs(
    master_text: str,
    job_text: str,
    tailored_resume_text: str | None = None,
    cover_letter_text: str | None = None,
) -> ValidationReport:
    targets: list[ValidationTargetResult] = []
    if tailored_resume_text:
        targets.append(validate_text(master_text, job_text, tailored_resume_text, label="resume"))
    if cover_letter_text:
        targets.append(validate_text(master_text, job_text, cover_letter_text, label="cover-letter"))
    return ValidationReport(targets=targets)
