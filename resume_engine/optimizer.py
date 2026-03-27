"""Resume optimizer -- LLM-powered resume improvement without a target job.

Unlike `tailor` (which rewrites for a specific job posting), `optimize`
makes your resume generically stronger:

- Rewrites weak bullets to lead with action verbs
- Replaces filler language with concrete phrasing
- Suggests where to add metrics (marks with [ADD METRIC])
- Tightens verbose language
- Preserves all facts -- never fabricates experience
"""

from __future__ import annotations

from .llm import complete

_OPTIMIZE_PROMPT = """You are an expert resume writer and editor. Your job is to improve the quality of this resume without targeting a specific job -- make it generically stronger for any reader.

RULES:
1. Rewrite weak bullet points to start with strong action verbs
2. Replace filler phrases (responsible for, helped with, worked on, assisted with) with direct, results-oriented language
3. Where a bullet point lacks metrics/numbers, add "[ADD METRIC]" as a placeholder with a suggested type (e.g. "[ADD METRIC: % improvement]")
4. Tighten verbose phrasing -- cut unnecessary words
5. Never fabricate experience, skills, companies, or titles -- only rephrase
6. Preserve all section headings exactly as written
7. Keep all dates, company names, and job titles unchanged
8. No em dashes -- use hyphens only
9. Output clean markdown only -- no commentary, no explanation

RESUME:
{resume}

Output the improved resume in markdown format. Nothing else."""

_EXPLAIN_PROMPT = """You reviewed a resume and produced an improved version. Now explain what you changed.

List the specific improvements made, grouped by type:
- Action verb upgrades
- Filler language replacements
- Metric placeholders added
- Phrasing tightened

Be concise. Use bullet points. No headers. No em dashes.

ORIGINAL:
{original}

IMPROVED:
{improved}

List only the actual changes made. Keep it under 200 words."""


def optimize_resume(text: str, model: str = "ollama") -> str:
    """Return an optimized version of the resume."""
    prompt = _OPTIMIZE_PROMPT.format(resume=text)
    return complete(prompt, model=model)


def explain_changes(original: str, improved: str, model: str = "ollama") -> str:
    """Return a brief explanation of what changed between original and improved."""
    prompt = _EXPLAIN_PROMPT.format(original=original, improved=improved)
    return complete(prompt, model=model)
