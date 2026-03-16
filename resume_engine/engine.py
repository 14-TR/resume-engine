"""Core tailoring engine -- LLM-powered resume customization."""

from .llm import complete

_BASE_TAILOR_PROMPT = """You are an expert resume writer. Given a master resume and a job posting, create a tailored version of the resume that:

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
{template_section}
MASTER RESUME:
{master}

JOB POSTING:
{job}

Output the tailored resume in markdown format. Nothing else."""

_BASE_COVER_PROMPT = """You are an expert cover letter writer. Given a resume and job posting, write a compelling cover letter that:

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


def tailor_resume(
    master_text: str, job_text: str, model: str = "ollama", template: str = "default"
) -> str:
    """Tailor a master resume to a specific job posting."""
    from .templates import get_template_instructions

    template_instr = get_template_instructions(template)
    if template_instr:
        template_section = f"\nLAYOUT STYLE INSTRUCTIONS:\n{template_instr}\n\n"
    else:
        template_section = ""

    prompt = _BASE_TAILOR_PROMPT.format(
        master=master_text,
        job=job_text,
        template_section=template_section,
    )
    return complete(prompt, model=model)


def generate_cover_letter(
    master_text: str, job_text: str, model: str = "ollama", template: str = "default"
) -> str:
    """Generate a cover letter for a job posting."""
    from .templates import get_template_instructions

    template_instr = get_template_instructions(template) if template else ""
    # Cover letters don't use structural layout templates, but pass tone/style hints if available
    style_hint = (
        f"\nSTYLE NOTE: Align tone and formality with the {template} resume style if applicable.\n"
        if template_instr
        else ""
    )
    prompt = (
        _BASE_COVER_PROMPT.format(
            master=master_text,
            job=job_text,
        )
        + style_hint
    )
    return complete(prompt, model=model)


_BASE_IMPORT_PROMPT = """You are an expert resume writer and career coach. Your task is to convert raw, unformatted resume text into a clean, structured master resume in markdown format.

A master resume is a COMPLETE career document -- it includes everything, not tailored to any specific job. The user will use it as a source to tailor resumes for individual applications.

CONVERSION RULES:
- Preserve all real content (experience, skills, education, projects, certifications)
- Structure with clear markdown sections: Summary, Skills, Experience, Education, Projects (if any), Certifications (if any)
- Format experience as: ### Job Title -- Company, City ST (Year - Year)
- Use bullet points for achievements under each role
- No em dashes (use hyphens instead)
- Keep contact info on the first line(s)
- Preserve dates accurately
- Do NOT fabricate, invent, or hallucinate any details
- If the input is already well-formatted, clean it up and standardize the structure

RAW RESUME TEXT:
{raw_text}

Output the structured master resume in clean markdown format. Nothing else."""


def import_resume(raw_text: str, model: str = "ollama") -> str:
    """Convert raw resume text to a structured master resume in markdown."""
    prompt = _BASE_IMPORT_PROMPT.format(raw_text=raw_text)
    return complete(prompt, model=model)
