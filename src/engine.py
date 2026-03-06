"""Core tailoring engine — LLM-powered resume customization."""
import json
from .llm import complete

TAILOR_PROMPT = """You are an expert resume writer. Given a master resume and a job posting, create a tailored version of the resume that:

1. Emphasizes experience and skills most relevant to the job
2. Reorders sections to put the most relevant content first
3. Mirrors key terminology from the job posting (ATS optimization)
4. Removes or de-emphasizes irrelevant experience
5. Keeps it honest -- never fabricate experience

IMPORTANT FORMATTING RULES:
- Output clean markdown only
- No em dashes (use hyphens instead)
- Keep it to 1-2 pages worth of content
- Use bullet points for achievements
- Lead each bullet with a strong action verb
- Include quantified results where possible

MASTER RESUME:
{master}

JOB POSTING:
{job}

Output the tailored resume in markdown format. Nothing else."""

COVER_PROMPT = """You are an expert cover letter writer. Given a resume and job posting, write a compelling cover letter that:

1. Opens with genuine enthusiasm for the specific role
2. Connects 2-3 key experiences directly to job requirements
3. Shows you understand the company/team's mission
4. Closes with a clear call to action
5. Keeps it under 400 words

IMPORTANT FORMATTING RULES:
- No em dashes (use hyphens instead)
- Professional but human tone
- No generic filler phrases

RESUME:
{master}

JOB POSTING:
{job}

Output the cover letter in markdown format. Nothing else."""


def tailor_resume(master_text: str, job_text: str, model: str = "ollama") -> str:
    """Tailor a master resume to a specific job posting."""
    prompt = TAILOR_PROMPT.format(master=master_text, job=job_text)
    return complete(prompt, model=model)


def generate_cover_letter(master_text: str, job_text: str, model: str = "ollama") -> str:
    """Generate a cover letter for a job posting."""
    prompt = COVER_PROMPT.format(master=master_text, job=job_text)
    return complete(prompt, model=model)
