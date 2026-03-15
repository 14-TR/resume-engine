from __future__ import annotations
"""CLI entry point for resume-engine."""

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def _load_master(master: str | None, linkedin_url: str | None, linkedin_export: str | None) -> str:
    """Load master resume text from a file, LinkedIn URL, or LinkedIn export."""
    sources = [s for s in [master, linkedin_url, linkedin_export] if s]
    if len(sources) == 0:
        raise click.UsageError(
            "Provide --master, --linkedin-url, or --linkedin-export as the resume source."
        )
    if len(sources) > 1:
        raise click.UsageError("Use only one of --master, --linkedin-url, or --linkedin-export.")

    if linkedin_url:
        from .linkedin import scrape_linkedin_profile

        console.print("[dim]Fetching LinkedIn profile...[/dim]")
        return scrape_linkedin_profile(linkedin_url)

    if linkedin_export:
        from .linkedin import parse_linkedin_export

        console.print("[dim]Parsing LinkedIn export...[/dim]")
        return parse_linkedin_export(linkedin_export)

    with open(master) as f:  # type: ignore[arg-type]
        return f.read()


@click.group()
@click.version_option(version="0.2.0")
def main():
    """AI-powered resume tailoring CLI."""
    pass


@main.command()
@click.option("--master", default=None, help="Path to master resume (markdown)")
@click.option(
    "--linkedin-url", default=None, help="LinkedIn profile URL to import as master resume"
)
@click.option("--linkedin-export", default=None, help="LinkedIn data export ZIP or directory")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--output", default="tailored-resume.md", help="Output file path")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
@click.option("--format", "fmt", default="md", type=click.Choice(["md", "pdf"]))
@click.option(
    "--interactive",
    "interactive",
    is_flag=True,
    default=False,
    help="Ask gap-filling questions before tailoring",
)
@click.option(
    "--template", default=None, help="Resume template/style (run `templates list` to see options)"
)
def tailor(
    master, linkedin_url, linkedin_export, job, job_url, output, model, fmt, interactive, template
):
    """Tailor a resume to a specific job posting."""
    from .engine import tailor_resume

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")

    console.print(Panel("[bold]resume-engine[/bold] -- tailoring resume", style="blue"))

    # Load master resume
    master_text = _load_master(master, linkedin_url, linkedin_export)
    console.print(f"[dim]Loaded master resume: {len(master_text)} chars[/dim]")

    # Load job posting
    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    console.print(f"[dim]Loaded job posting: {len(job_text)} chars[/dim]")

    # Interactive gap-filling
    if interactive:
        from .interactive import analyze_gaps, ask_questions, enrich_master

        console.print("[dim]Analyzing resume gaps...[/dim]")
        questions = analyze_gaps(master_text, job_text, model=model)
        if questions:
            answers = ask_questions(questions, console)
            master_text = enrich_master(master_text, answers)
        else:
            console.print("[dim]No gaps identified -- proceeding with tailoring.[/dim]")

    # Tailor
    result = tailor_resume(master_text, job_text, model=model, template=template)

    # Output
    # Determine final paths
    md_output = output if output.endswith(".md") else output
    with open(md_output, "w") as f:
        f.write(result)
    console.print(f"[green]Tailored resume (markdown) written to {md_output}[/green]")

    if fmt == "pdf":
        from .pdf import markdown_to_pdf, md_path_to_pdf_path

        pdf_output = md_path_to_pdf_path(md_output)
        try:
            console.print("[dim]Converting to PDF via pandoc...[/dim]")
            markdown_to_pdf(md_output, pdf_output)
            console.print(f"[green]PDF written to {pdf_output}[/green]")
        except RuntimeError as e:
            console.print(f"[yellow]PDF conversion failed: {e}[/yellow]")
            console.print("[yellow]Markdown output is still available.[/yellow]")


@main.command()
@click.option("--master", default=None, help="Path to master resume (markdown)")
@click.option(
    "--linkedin-url", default=None, help="LinkedIn profile URL to import as master resume"
)
@click.option("--linkedin-export", default=None, help="LinkedIn data export ZIP or directory")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--output", default="cover-letter.md", help="Output file path")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
@click.option("--format", "fmt", default="md", type=click.Choice(["md", "pdf"]))
@click.option(
    "--interactive",
    "interactive",
    is_flag=True,
    default=False,
    help="Ask gap-filling questions before writing",
)
@click.option(
    "--template",
    default=None,
    help="Cover letter template/style (run `templates list` to see options)",
)
def cover(
    master, linkedin_url, linkedin_export, job, job_url, output, model, fmt, interactive, template
):
    """Generate a cover letter for a job posting."""
    from .engine import generate_cover_letter

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")

    console.print(Panel("[bold]resume-engine[/bold] -- generating cover letter", style="blue"))

    master_text = _load_master(master, linkedin_url, linkedin_export)

    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    # Interactive gap-filling
    if interactive:
        from .interactive import analyze_gaps, ask_questions, enrich_master

        console.print("[dim]Analyzing resume gaps...[/dim]")
        questions = analyze_gaps(master_text, job_text, model=model)
        if questions:
            answers = ask_questions(questions, console)
            master_text = enrich_master(master_text, answers)
        else:
            console.print("[dim]No gaps identified -- proceeding.[/dim]")

    result = generate_cover_letter(master_text, job_text, model=model, template=template)

    with open(output, "w") as f:
        f.write(result)
    console.print(f"[green]Cover letter (markdown) written to {output}[/green]")

    if fmt == "pdf":
        from .pdf import markdown_to_pdf, md_path_to_pdf_path

        pdf_output = md_path_to_pdf_path(output)
        try:
            console.print("[dim]Converting to PDF via pandoc...[/dim]")
            markdown_to_pdf(output, pdf_output)
            console.print(f"[green]PDF written to {pdf_output}[/green]")
        except RuntimeError as e:
            console.print(f"[yellow]PDF conversion failed: {e}[/yellow]")


@main.command()
@click.option("--master", default=None, help="Path to master resume (markdown)")
@click.option(
    "--linkedin-url", default=None, help="LinkedIn profile URL to import as master resume"
)
@click.option("--linkedin-export", default=None, help="LinkedIn data export ZIP or directory")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--outdir", default="./application", help="Output directory")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
@click.option("--format", "fmt", default="md", type=click.Choice(["md", "pdf"]))
@click.option(
    "--template",
    default=None,
    help="Resume/cover letter template/style (run `templates list` to see options)",
)
def package(master, linkedin_url, linkedin_export, job, job_url, outdir, model, fmt, template):
    """Generate full application package (resume + cover letter)."""
    import os

    os.makedirs(outdir, exist_ok=True)

    console.print(Panel("[bold]resume-engine[/bold] -- full application package", style="blue"))

    master_text = _load_master(master, linkedin_url, linkedin_export)

    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")

    from .engine import generate_cover_letter, tailor_resume

    resume = tailor_resume(master_text, job_text, model=model, template=template)
    resume_md = os.path.join(outdir, "resume.md")
    with open(resume_md, "w") as f:
        f.write(resume)
    console.print("[green]Resume (markdown) written[/green]")

    letter = generate_cover_letter(master_text, job_text, model=model, template=template)
    cover_md = os.path.join(outdir, "cover-letter.md")
    with open(cover_md, "w") as f:
        f.write(letter)
    console.print("[green]Cover letter (markdown) written[/green]")

    if fmt == "pdf":
        from .pdf import markdown_to_pdf, md_path_to_pdf_path

        try:
            console.print("[dim]Converting to PDF via pandoc...[/dim]")
            markdown_to_pdf(resume_md, md_path_to_pdf_path(resume_md))
            markdown_to_pdf(cover_md, md_path_to_pdf_path(cover_md))
            console.print("[green]PDFs generated[/green]")
        except RuntimeError as e:
            console.print(f"[yellow]PDF conversion failed: {e}[/yellow]")

    console.print(f"\n[bold green]Application package ready in {outdir}/[/bold green]")


@main.command()
@click.option("--resume", required=True, help="Path to resume (markdown) to analyze")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option(
    "--tailored", default=None, help="Path to tailored resume for before/after comparison"
)
@click.option("--top", default=30, show_default=True, help="Number of keywords to analyze")
def ats(resume, job, job_url, tailored, top):
    """Analyze ATS keyword match score between resume and job posting."""

    from .ats import analyze

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")

    console.print(Panel("[bold]resume-engine[/bold] — ATS keyword analysis", style="blue"))

    with open(resume) as f:
        resume_text = f.read()

    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    # Analyze original resume
    result = analyze(resume_text, job_text, top_n=top)
    score = result["score"]

    # Score color
    if score >= 70:
        score_style = "bold green"
    elif score >= 45:
        score_style = "bold yellow"
    else:
        score_style = "bold red"

    console.print(
        f"\n[bold]Original resume match score:[/bold] [{score_style}]{score}%[/{score_style}] ({result['matched_count']}/{result['total_keywords']} keywords)"
    )

    # Show matched keywords
    if result["matched"]:
        matched_str = "  ".join(f"[green]{k}[/green]" for k in result["matched"])
        console.print("\n[bold]Matched keywords:[/bold]")
        console.print(f"  {matched_str}")

    # Show missing keywords
    if result["missing"]:
        missing_str = "  ".join(f"[red]{k}[/red]" for k in result["missing"])
        console.print("\n[bold]Missing keywords:[/bold]")
        console.print(f"  {missing_str}")

    # Before/after comparison if tailored resume provided
    if tailored:
        with open(tailored) as f:
            tailored_text = f.read()

        tailored_result = analyze(tailored_text, job_text, top_n=top)
        tailored_score = tailored_result["score"]

        if tailored_score >= 70:
            t_style = "bold green"
        elif tailored_score >= 45:
            t_style = "bold yellow"
        else:
            t_style = "bold red"

        delta = tailored_score - score
        delta_str = f"+{delta}%" if delta >= 0 else f"{delta}%"
        delta_style = "green" if delta > 0 else ("red" if delta < 0 else "dim")

        console.print(
            f"\n[bold]Tailored resume match score:[/bold] [{t_style}]{tailored_score}%[/{t_style}] ({tailored_result['matched_count']}/{tailored_result['total_keywords']} keywords)  [{delta_style}]{delta_str}[/{delta_style}]"
        )

        # Show newly matched keywords
        newly_matched = [k for k in tailored_result["matched"] if k in result["missing"]]
        if newly_matched:
            console.print("\n[bold]Newly matched by tailoring:[/bold]")
            console.print("  " + "  ".join(f"[green]{k}[/green]" for k in newly_matched))

        still_missing = [k for k in tailored_result["missing"]]
        if still_missing:
            console.print("\n[bold]Still missing:[/bold]")
            console.print("  " + "  ".join(f"[red]{k}[/red]" for k in still_missing))

    console.print("")


@main.command()
@click.option("--master", required=True, help="Path to master resume (markdown)")
@click.option("--jobs-dir", default=None, help="Directory of job posting files (.txt or .md)")
@click.option(
    "--manifest", default=None, help="JSON manifest file listing jobs (see docs for format)"
)
@click.option("--outdir", default="./batch-output", show_default=True, help="Root output directory")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
@click.option("--format", "fmt", default="md", type=click.Choice(["md", "pdf"]))
@click.option(
    "--template", default=None, help="Resume template/style (run `templates list` to see options)"
)
@click.option(
    "--with-cover", is_flag=True, default=False, help="Also generate a cover letter for each job"
)
def batch(master, jobs_dir, manifest, outdir, model, fmt, template, with_cover):
    """Tailor resume to multiple jobs at once.

    Jobs can be supplied as a directory of .txt/.md files (--jobs-dir)
    or as a JSON manifest (--manifest).

    Manifest format example:

    \b
      [
        {"name": "acme-corp",  "job": "jobs/acme.txt"},
        {"name": "startup-x",  "job_url": "https://example.com/jobs/123"}
      ]

    Each job gets its own subfolder in --outdir containing resume.md
    (and cover-letter.md if --with-cover).
    """
    from rich.panel import Panel

    from .batch import load_jobs_from_dir, load_jobs_from_manifest, print_summary, run_batch

    if not jobs_dir and not manifest:
        raise click.UsageError("Provide either --jobs-dir or --manifest")
    if jobs_dir and manifest:
        raise click.UsageError("Use --jobs-dir OR --manifest, not both")

    console.print(Panel("[bold]resume-engine[/bold] -- batch mode", style="blue"))

    with open(master) as f:
        master_text = f.read()
    console.print(f"[dim]Master resume: {len(master_text)} chars[/dim]")

    if jobs_dir:
        jobs = load_jobs_from_dir(jobs_dir)
        console.print(f"[dim]Found {len(jobs)} job(s) in {jobs_dir}[/dim]")
    else:
        jobs = load_jobs_from_manifest(manifest)
        console.print(f"[dim]Loaded {len(jobs)} job(s) from manifest[/dim]")

    if not jobs:
        console.print("[yellow]No jobs found -- nothing to do.[/yellow]")
        raise SystemExit(0)

    action = "resume + cover letter" if with_cover else "resume"
    console.print(f"[dim]Generating {action} for each job. Output: {outdir}/[/dim]\n")

    results = run_batch(
        master_text=master_text,
        jobs=jobs,
        outdir=outdir,
        model=model,
        fmt=fmt,
        template=template,
        with_cover=with_cover,
        console=console,
    )

    console.print("")
    print_summary(results, console, fmt=fmt, with_cover=with_cover)
    console.print(f"\n[bold green]Output directory: {outdir}/[/bold green]")


@main.command("import")
@click.option("--text", "text_file", default=None, help="Path to raw resume text file (any format)")
@click.option(
    "--output", default="master-resume.md", show_default=True, help="Output markdown file path"
)
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
@click.option("--stdin", "from_stdin", is_flag=True, default=False, help="Read raw text from stdin")
def import_resume(text_file, output, model, from_stdin):
    """Convert raw resume text to a structured master resume markdown.

    Accepts resume text from any source: LinkedIn copy-paste, exported PDFs,
    old resume documents, or any plain-text format. The LLM restructures it
    into a clean master resume ready for tailoring.

    \b
    Examples:
      # From a file (e.g. LinkedIn PDF export text)
      resume-engine import --text linkedin-export.txt --output master-resume.md

      # From stdin (paste directly)
      pbpaste | resume-engine import --stdin --output master-resume.md --model openai
    """
    import sys

    from .importer import text_to_master_resume

    if not text_file and not from_stdin:
        raise click.UsageError("Provide --text <file> or --stdin to read from stdin")
    if text_file and from_stdin:
        raise click.UsageError("Use --text OR --stdin, not both")

    console.print(Panel("[bold]resume-engine[/bold] -- importing resume", style="blue"))

    if from_stdin:
        console.print("[dim]Reading from stdin...[/dim]")
        raw_text = sys.stdin.read()
    else:
        with open(text_file) as f:
            raw_text = f.read()

    console.print(f"[dim]Input: {len(raw_text)} chars -- converting to master resume...[/dim]")

    result = text_to_master_resume(raw_text, model=model)

    with open(output, "w") as f:
        f.write(result)

    console.print(f"[green]Master resume written to {output}[/green]")
    console.print(
        "[dim]Tip: review and fill any gaps, then use `resume-engine tailor` to target specific jobs.[/dim]"
    )


@main.group()
def templates():
    """Manage and list resume templates."""
    pass


@templates.command("list")
def templates_list():
    """List all available resume templates."""
    from rich.table import Table

    from .templates import list_templates

    tmpl_list = list_templates()

    table = Table(title="Available Templates", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold", width=14)
    table.add_column("Slug", style="dim", width=12)
    table.add_column("Description")
    table.add_column("Source", width=10)

    for t in tmpl_list:
        source_style = "[dim]user[/dim]" if t["source"] == "user" else "[green]built-in[/green]"
        table.add_row(t["name"], t["slug"], t["description"], source_style)

    console.print(table)
    console.print(
        "\n[dim]Use with:[/dim] python -m src.cli tailor --template technical --master resume.md --job job.txt",
    )


@templates.command("show")
@click.argument("name")
def templates_show(name):
    """Show the formatting instructions for a template."""
    from .templates import get_template, get_template_instructions

    t = get_template(name)
    if t is None:
        from .templates import template_choices

        available = ", ".join(template_choices()[1:])  # skip "default"
        console.print(f"[red]Unknown template '{name}'. Available: {available}[/red]")
        raise SystemExit(1)
    console.print(f"\n[bold cyan]{t['name']}[/bold cyan] ({t['slug']}) - {t['description']}\n")
    console.print(get_template_instructions(t["slug"]))
    console.print("")


if __name__ == "__main__":
    main()
