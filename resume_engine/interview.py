"""Interview prep generator -- LLM-powered question bank from resume + job posting.

Generates a tailored set of interview questions with STAR-method answer
frameworks, drawing on the candidate's actual experience and the job
requirements.

Categories generated:
  - Behavioral (situational/competency based)
  - Technical (role-specific skills and tools)
  - Culture fit / motivation
  - Resume deep-dives (likely follow-up questions on listed experience)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from .llm import complete

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_INTERVIEW_PROMPT = """You are a senior hiring manager and career coach. Given a resume and job posting, generate a focused set of interview questions the candidate is LIKELY to face.

For each question, provide:
1. The question itself
2. Category: Behavioral | Technical | Culture Fit | Resume Deep-Dive
3. A brief STAR-method answer framework tailored to this candidate's actual background

RULES:
- Generate exactly {count} questions spread across all 4 categories
- Technical questions must reference the actual tech stack from the job posting
- Resume Deep-Dive questions must reference specific items from the candidate's resume (companies, projects, dates)
- STAR frameworks must reference the candidate's real experience -- never make up companies or roles
- If a category has no relevant material, skip it and add more to another
- Be specific -- not generic "tell me about yourself" questions
- No em dashes -- use hyphens only
- Output ONLY a numbered list of questions in this exact format:

1. [Question text]
   Category: Behavioral
   STAR Framework: [Situation type to use] | [Task to describe] | [Action to highlight] | [Result to emphasize]

2. [Question text]
   Category: Technical
   STAR Framework: [what to explain and demonstrate]

(continue for all {count} questions)

RESUME:
{resume}

JOB POSTING:
{job}"""

_FOLLOWUP_PROMPT = """You are a senior interviewer. Based on this resume, generate {count} likely follow-up questions specifically about listed experience, gaps, or career transitions.

For each, note what concern the interviewer is probing.

RULES:
- Reference specific items from the resume (company names, dates, titles, projects)
- Flag potential red flags an interviewer might probe (short tenures, gaps, title changes)
- No em dashes -- use hyphens only
- Output ONLY a numbered list in this exact format:

1. [Question text]
   Probing: [what the interviewer is trying to assess]

RESUME:
{resume}"""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


@dataclass
class InterviewQuestion:
    number: int
    question: str
    category: str
    framework: str


@dataclass
class FollowupQuestion:
    number: int
    question: str
    probing: str


@dataclass
class InterviewPrepResult:
    questions: List[InterviewQuestion] = field(default_factory=list)
    followups: List[FollowupQuestion] = field(default_factory=list)
    raw_questions: str = ""
    raw_followups: str = ""


def _parse_questions(text: str) -> List[InterviewQuestion]:
    """Parse structured question output into InterviewQuestion objects."""
    questions = []
    # Split on numbered entries: "1. " at start of line
    blocks = re.split(r"\n(?=\d+\.\s)", text.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Extract number + question
        num_match = re.match(r"^(\d+)\.\s+(.+?)(?:\n|$)", block, re.DOTALL)
        if not num_match:
            continue
        number = int(num_match.group(1))
        question_lines = []
        # Collect question lines until Category: appears
        for line in block.split("\n"):
            stripped = line.strip()
            if re.match(r"^Category:", stripped, re.IGNORECASE):
                break
            if re.match(r"^\d+\.\s", stripped):
                question_lines.append(re.sub(r"^\d+\.\s+", "", stripped))
            elif stripped:
                question_lines.append(stripped)
        question_text = " ".join(question_lines).strip()

        # Extract Category
        cat_match = re.search(r"Category:\s*(.+)", block, re.IGNORECASE)
        category = cat_match.group(1).strip() if cat_match else "General"

        # Extract STAR Framework
        star_match = re.search(
            r"STAR Framework:\s*(.+?)(?:\n\d+\.|$)", block, re.IGNORECASE | re.DOTALL
        )
        framework = star_match.group(1).strip() if star_match else ""

        if question_text:
            questions.append(
                InterviewQuestion(
                    number=number,
                    question=question_text,
                    category=category,
                    framework=framework,
                )
            )

    return questions


def _parse_followups(text: str) -> List[FollowupQuestion]:
    """Parse follow-up questions output."""
    followups = []
    blocks = re.split(r"\n(?=\d+\.\s)", text.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        num_match = re.match(r"^(\d+)\.\s+(.+?)(?:\n|$)", block, re.DOTALL)
        if not num_match:
            continue
        number = int(num_match.group(1))

        question_lines = []
        for line in block.split("\n"):
            stripped = line.strip()
            if re.match(r"^Probing:", stripped, re.IGNORECASE):
                break
            if re.match(r"^\d+\.\s", stripped):
                question_lines.append(re.sub(r"^\d+\.\s+", "", stripped))
            elif stripped:
                question_lines.append(stripped)
        question_text = " ".join(question_lines).strip()

        probing_match = re.search(
            r"Probing:\s*(.+?)(?:\n\d+\.|$)", block, re.IGNORECASE | re.DOTALL
        )
        probing = probing_match.group(1).strip() if probing_match else ""

        if question_text:
            followups.append(
                FollowupQuestion(
                    number=number,
                    question=question_text,
                    probing=probing,
                )
            )

    return followups


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_interview_prep(
    resume_text: str,
    job_text: str,
    model: str = "ollama",
    count: int = 10,
    with_followups: bool = False,
) -> InterviewPrepResult:
    """Generate interview questions + STAR frameworks from resume and job posting."""
    prompt = _INTERVIEW_PROMPT.format(resume=resume_text, job=job_text, count=count)
    raw_questions = complete(prompt, model=model)

    raw_followups = ""
    followups = []

    if with_followups:
        fp = _FOLLOWUP_PROMPT.format(resume=resume_text, count=5)
        raw_followups = complete(fp, model=model)
        followups = _parse_followups(raw_followups)

    return InterviewPrepResult(
        questions=_parse_questions(raw_questions),
        followups=followups,
        raw_questions=raw_questions,
        raw_followups=raw_followups,
    )
