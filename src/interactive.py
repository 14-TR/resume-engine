"""Interactive mode -- gap analysis and user Q&A before tailoring."""
import json
import re
from .llm import complete

GAP_ANALYSIS_PROMPT = """You are a resume expert reviewing a master resume against a job posting.

Identify 2-5 specific gaps or missing details that would strengthen this application.
Focus on:
- Missing quantified achievements (e.g., "managed X people", "increased revenue by Y%")
- Skills mentioned in the job posting that are not clearly demonstrated in the resume
- Missing contact/profile info (LinkedIn, GitHub, portfolio) if relevant to the role
- Dates or durations that are vague or missing
- Certifications or education details that could be filled in

Return a JSON array of question objects. Each object has:
- "field": short identifier (snake_case)
- "question": the question to ask the user (be specific, reference the job)
- "hint": brief example of a good answer (optional, keep under 15 words)

Return ONLY valid JSON. No markdown fences. No explanation. Example:
[
  {{"field": "team_size", "question": "How many engineers did you manage at Acme Corp?", "hint": "e.g. 6 direct reports across 2 squads"}},
  {{"field": "github_url", "question": "What is your GitHub profile URL?", "hint": "e.g. https://github.com/yourname"}}
]

MASTER RESUME:
{master}

JOB POSTING:
{job}

Return the JSON array now:"""


def analyze_gaps(master_text: str, job_text: str, model: str = "ollama") -> list[dict]:
    """Ask LLM to identify gaps in the resume relative to the job posting."""
    prompt = GAP_ANALYSIS_PROMPT.format(master=master_text, job=job_text)
    raw = complete(prompt, model=model)

    # Strip markdown fences if LLM wrapped it anyway
    raw = raw.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()

    try:
        questions = json.loads(raw)
        if not isinstance(questions, list):
            return []
        # Validate shape
        valid = []
        for q in questions:
            if isinstance(q, dict) and "field" in q and "question" in q:
                valid.append(q)
        return valid[:5]  # Cap at 5 questions
    except (json.JSONDecodeError, ValueError):
        return []


def ask_questions(questions: list[dict], console) -> dict[str, str]:
    """Present questions to the user and collect answers. Returns field -> answer map."""
    import click
    answers = {}
    console.print("\n[bold yellow]Interactive mode[/bold yellow] -- answer a few questions to strengthen your resume.\n")
    console.print("[dim]Press Enter to skip any question.[/dim]\n")

    for i, q in enumerate(questions, 1):
        hint = q.get("hint", "")
        prompt_text = f"[{i}/{len(questions)}] {q['question']}"
        if hint:
            prompt_text += f"\n    [dim]({hint})[/dim]"

        console.print(prompt_text)
        answer = click.prompt("    Your answer", default="", show_default=False).strip()
        if answer:
            answers[q["field"]] = answer
        console.print("")

    return answers


def enrich_master(master_text: str, answers: dict[str, str]) -> str:
    """Append user-provided answers as supplemental context to the master resume."""
    if not answers:
        return master_text

    additions = "\n\n## Supplemental Details (for this application)\n\n"
    for field, value in answers.items():
        label = field.replace("_", " ").title()
        additions += f"- {label}: {value}\n"

    return master_text + additions
