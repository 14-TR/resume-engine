"""Import arbitrary resume text and convert to a structured master resume markdown."""

from .llm import complete

_IMPORT_PROMPT = """You are an expert resume writer. The user has provided raw resume text -- this could be \
pasted from LinkedIn, copied from a PDF, or exported from any source.

Your job is to convert this raw text into a clean, well-structured master resume in markdown format.

The master resume should:
1. Include ALL information from the source (this is the superset -- keep everything)
2. Use standard markdown resume sections: Summary, Skills, Experience, Education, Projects, Certifications (as applicable)
3. Format experience as: `### Job Title -- Company, City ST (Start Year - End Year)`
4. Use bullet points for achievements/responsibilities under each role
5. Lead each bullet with a strong action verb
6. Preserve all dates, company names, titles, and metrics exactly as given
7. Clean up any formatting artifacts (page numbers, headers, repeated names, etc.)
8. Keep skills organized by category if categories are discernible

IMPORTANT FORMATTING RULES:
- No em dashes (use hyphens or double hyphens instead)
- Clean markdown only, no HTML
- Start with: `# Full Name`
- Second line: contact info (email | phone | location | linkedin | github -- whatever is available)

RAW RESUME TEXT:
{text}

Output the structured master resume in markdown. Nothing else."""


def text_to_master_resume(text: str, model: str = "ollama") -> str:
    """Convert arbitrary resume text to structured master resume markdown.

    Args:
        text: Raw resume text from any source (LinkedIn copy-paste, PDF text, old resume, etc.)
        model: LLM provider to use (ollama, openai, anthropic)

    Returns:
        Structured master resume in markdown format
    """
    prompt = _IMPORT_PROMPT.format(text=text.strip())
    return complete(prompt, model=model)
