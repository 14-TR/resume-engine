"""CLI entry point for resume-engine."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def _cfg_default(key: str, fallback=None):
    """Return config default for a key, used as Click option defaults."""
    from .config import get as cfg_get

    return cfg_get(key, fallback)


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
@click.version_option(version="0.3.1")
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
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option(
    "--format",
    "fmt",
    default=lambda: _cfg_default("format", "md"),
    type=click.Choice(["md", "pdf"]),
)
@click.option(
    "--interactive",
    "interactive",
    is_flag=True,
    default=False,
    help="Ask gap-filling questions before tailoring",
)
@click.option(
    "--template",
    default=lambda: _cfg_default("template"),
    help="Resume template/style (run `templates list` to see options)",
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
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option(
    "--format",
    "fmt",
    default=lambda: _cfg_default("format", "md"),
    type=click.Choice(["md", "pdf"]),
)
@click.option(
    "--interactive",
    "interactive",
    is_flag=True,
    default=False,
    help="Ask gap-filling questions before writing",
)
@click.option(
    "--template",
    default=lambda: _cfg_default("template"),
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
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option(
    "--format",
    "fmt",
    default=lambda: _cfg_default("format", "md"),
    type=click.Choice(["md", "pdf"]),
)
@click.option(
    "--template",
    default=lambda: _cfg_default("template"),
    help="Resume/cover letter template/style (run `templates list` to see options)",
)
@click.option(
    "--validate-report/--no-validate-report",
    default=False,
    help="Generate a grounded validation report alongside the package outputs.",
)
def package(
    master,
    linkedin_url,
    linkedin_export,
    job,
    job_url,
    outdir,
    model,
    fmt,
    template,
    validate_report,
):
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

    if validate_report:
        from .validate import validate_outputs

        report = validate_outputs(
            master_text=master_text,
            job_text=job_text,
            tailored_resume_text=resume,
            cover_letter_text=letter,
        )
        validation_path = os.path.join(outdir, "validation-report.md")
        md_lines = ["# Validation Report\n"]

        for target in report.targets:
            md_lines.append(f"## {target.label.title()}\n")
            md_lines.append(f"Trust score: {target.score}/100\n")
            if not target.issues:
                md_lines.append("- No obvious grounding problems detected.\n")
                continue
            for issue in target.issues:
                md_lines.append(
                    f"- **{issue.severity.upper()} | {issue.category}:** {issue.message}\n"
                )
                if issue.evidence:
                    md_lines.append(f"  - Evidence: `{issue.evidence}`\n")
                if issue.suggestion:
                    md_lines.append(f"  - Suggestion: {issue.suggestion}\n")

        with open(validation_path, "w") as f:
            f.writelines(md_lines)
        console.print(f"[green]Validation report written to {validation_path}[/green]")

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

    console.print(Panel("[bold]resume-engine[/bold] -- ATS keyword analysis", style="blue"))

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
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option(
    "--format",
    "fmt",
    default=lambda: _cfg_default("format", "md"),
    type=click.Choice(["md", "pdf"]),
)
@click.option(
    "--template",
    default=lambda: _cfg_default("template"),
    help="Resume template/style (run `templates list` to see options)",
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
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
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


@main.command()
def check():
    """Check that resume-engine dependencies are installed and configured."""
    from rich.table import Table

    from .check import run_checks

    console.print(Panel("[bold]resume-engine[/bold] -- system check", style="blue"))

    results = run_checks()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Check", style="bold", width=22)
    table.add_column("Category", width=26)
    table.add_column("Status", width=8)
    table.add_column("Details")

    all_required_ok = True
    for r in results:
        status = "[green]OK[/green]" if r["ok"] else "[red]FAIL[/red]"
        detail = r.get("detail", "")
        hint = r.get("hint", "")
        detail_str = detail if r["ok"] else f"[red]{detail}[/red]"
        if hint and not r["ok"]:
            detail_str += f"\n  [dim]Hint: {hint}[/dim]"
        table.add_row(r["name"], r["category"], status, detail_str)
        if not r["ok"] and "optional" not in r["category"].lower():
            all_required_ok = False

    console.print(table)
    console.print("")

    if all_required_ok:
        console.print(
            "[bold green]All required checks passed.[/bold green] resume-engine is ready to use."
        )
    else:
        console.print(
            "[bold yellow]Some required checks failed.[/bold yellow] "
            "Run [bold]resume-engine check[/bold] after fixing the issues above."
        )
        raise SystemExit(1)


@main.command()
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit with a non-zero status if any required checks fail",
)
def doctor(strict):
    """Diagnose local setup issues before you tailor or export."""
    from .doctor import run_diagnostics, summarize_results

    status_styles = {"pass": "green", "warn": "yellow", "fail": "red"}
    status_labels = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}

    console.print(Panel("[bold]resume-engine[/bold] - environment doctor", style="blue"))
    results = run_diagnostics()
    for result in results:
        label = status_labels[result.status]
        console.print(
            f"[{status_styles[result.status]}]{label}[/{status_styles[result.status]}] {result.name}: {result.detail}"
        )

    passed, warned, failed = summarize_results(results)
    console.print(f"[bold]Summary:[/bold] {passed} passed, {warned} warning(s), {failed} failed")

    if strict and failed:
        raise click.ClickException("Doctor found required setup failures.")


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
        "\n[dim]Use with:[/dim] resume-engine tailor --template technical --master resume.md --job job.txt",
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


@main.command("diff")
@click.argument("original", type=click.Path(exists=True))
@click.argument("tailored", type=click.Path(exists=True))
@click.option(
    "--unified", "show_unified", is_flag=True, default=False, help="Show raw unified diff output"
)
@click.option(
    "--sections",
    "show_sections",
    is_flag=True,
    default=True,
    help="Show section-by-section summary (default)",
)
def diff_cmd(original, tailored, show_unified, show_sections):
    """Show a diff between original and tailored resume.

    Highlights what changed section by section so you can see what the AI
    added, removed, or restructured.

    \b
    Examples:
      resume-engine diff master-resume.md tailored-resume.md
      resume-engine diff master-resume.md tailored-resume.md --unified
    """
    from rich.table import Table

    from .differ import compute_diff

    with open(original) as f:
        orig_text = f.read()
    with open(tailored) as f:
        tail_text = f.read()

    result = compute_diff(orig_text, tail_text)

    console.print("")
    console.print(
        Panel(
            f"[bold]Comparing:[/bold] {original}  [dim]vs[/dim]  {tailored}",
            style="blue",
        )
    )

    # Overall stats
    score = result.change_score
    if score >= 60:
        score_style = "bold green"
    elif score >= 25:
        score_style = "bold yellow"
    else:
        score_style = "bold cyan"

    console.print(
        f"\n[bold]Overall change:[/bold]  [{score_style}]{score}%[/{score_style}] of original content modified"
        f"  [green]+{result.added_lines} lines added[/green]  [red]-{result.removed_lines} lines removed[/red]"
    )

    # Section table
    changed_sections = [s for s in result.sections if s.is_changed]
    unchanged_sections = [s for s in result.sections if not s.is_changed]

    if changed_sections:
        console.print("")
        table = Table(
            title="Changed Sections",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Section", style="bold", width=24)
        table.add_column("Change", width=8)
        table.add_column("+Added", style="green", width=8)
        table.add_column("-Removed", style="red", width=10)
        table.add_column("Preview", min_width=40)

        for sec in changed_sections:
            pct_str = f"{sec.change_pct}%"
            if sec.change_pct >= 60:
                pct_style = "bold green"
            elif sec.change_pct >= 25:
                pct_style = "yellow"
            else:
                pct_style = "cyan"

            # Preview: first added line (truncated)
            preview = ""
            if sec.added:
                line = sec.added[0].strip()
                if line:
                    preview = line[:60] + ("..." if len(line) > 60 else "")

            table.add_row(
                sec.name,
                f"[{pct_style}]{pct_str}[/{pct_style}]",
                str(len(sec.added)),
                str(len(sec.removed)),
                f"[dim]{preview}[/dim]",
            )

        console.print(table)

    if unchanged_sections:
        names = ", ".join(s.name for s in unchanged_sections)
        console.print(f"\n[dim]Unchanged sections: {names}[/dim]")

    # Detailed line-level output for each changed section
    if show_sections and not show_unified:
        for sec in changed_sections:
            console.print(f"\n[bold cyan]--- {sec.name} ---[/bold cyan]")
            for line in sec.removed:
                stripped = line.rstrip()
                if stripped:
                    console.print(f"[red]- {stripped}[/red]")
            for line in sec.added:
                stripped = line.rstrip()
                if stripped:
                    console.print(f"[green]+ {stripped}[/green]")

    # Raw unified diff
    if show_unified:
        console.print("\n[bold]Unified diff:[/bold]")
        for line in result.unified_diff:
            if line.startswith("+++") or line.startswith("---"):
                console.print(f"[bold]{line}[/bold]")
            elif line.startswith("+"):
                console.print(f"[green]{line}[/green]")
            elif line.startswith("-"):
                console.print(f"[red]{line}[/red]")
            elif line.startswith("@@"):
                console.print(f"[cyan]{line}[/cyan]")
            else:
                console.print(f"[dim]{line}[/dim]")

    console.print("")


@main.group()
def config():
    """Manage resume-engine persistent configuration.

    \b
    Set defaults so you don't repeat --model, --format, etc. on every command.

    \b
    Examples:
      resume-engine config set model openai
      resume-engine config set format pdf
      resume-engine config get model
      resume-engine config list
      resume-engine config unset model
    """
    pass


@config.command("list")
def config_list():
    """Show all current config values."""
    from rich.table import Table

    from .config import CONFIG_FILE, VALID_KEYS, load

    data = load()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Key", style="bold", width=12)
    table.add_column("Value", width=20)
    table.add_column("Allowed Values")

    for key in VALID_KEYS:
        val = data.get(key, "[dim]not set[/dim]")
        allowed = VALID_KEYS[key]
        allowed_str = " | ".join(allowed) if allowed else "[dim]any string[/dim]"
        table.add_row(key, str(val), allowed_str)

    console.print(table)
    console.print(f"\n[dim]Config file: {CONFIG_FILE}[/dim]")


@config.command("get")
@click.argument("key")
def config_get(key):
    """Get a single config value."""
    from .config import VALID_KEYS, get

    if key not in VALID_KEYS:
        console.print(f"[red]Unknown key '{key}'. Valid keys: {', '.join(VALID_KEYS)}[/red]")
        raise SystemExit(1)
    val = get(key)
    if val is None:
        console.print(f"[dim]{key} is not set[/dim]")
    else:
        console.print(f"{key} = {val}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a config key to a value."""
    from .config import set_value

    try:
        set_value(key, value)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)
    console.print(f"[green]Set {key} = {value}[/green]")


@config.command("unset")
@click.argument("key")
def config_unset(key):
    """Remove a config key (revert to built-in default)."""
    from .config import unset_value

    removed = unset_value(key)
    if removed:
        console.print(f"[green]Unset {key}[/green]")
    else:
        console.print(f"[dim]{key} was not set[/dim]")


@config.command("reset")
@click.confirmation_option(prompt="This will delete all your resume-engine config. Continue?")
def config_reset():
    """Remove all config and revert to built-in defaults."""
    from .config import reset

    reset()
    console.print("[green]Config reset.[/green]")


@main.command("score")
@click.argument("resume", type=click.Path(exists=True))
@click.option(
    "--brief", is_flag=True, default=False, help="Show score only (no detailed breakdown)"
)
@click.option(
    "--json", "json_output", is_flag=True, default=False, help="Output machine-readable JSON"
)
def score_cmd(resume, brief, json_output):
    """Score a resume's overall quality (0-100) across 5 dimensions.

    Checks section completeness, quantified achievements, action verb usage,
    length, and filler language. No LLM required -- runs instantly.

    
    Examples:
      resume-engine score master-resume.md
      resume-engine score tailored.md --brief
      resume-engine score master-resume.md --json
    """
    import json
    from dataclasses import asdict

    from rich.table import Table

    from .scorer import score_resume

    with open(resume) as f:
        text = f.read()

    result = score_resume(text)

    # Grade band
    total = result.total
    if total >= 85:
        grade = "A"
        grade_style = "bold green"
        grade_label = "Excellent"
    elif total >= 70:
        grade = "B"
        grade_style = "bold cyan"
        grade_label = "Good"
    elif total >= 50:
        grade = "C"
        grade_style = "bold yellow"
        grade_label = "Needs work"
    else:
        grade = "D"
        grade_style = "bold red"
        grade_label = "Significant gaps"

    if json_output:
        payload = asdict(result)
        payload["resume"] = resume
        payload["grade"] = {"letter": grade, "label": grade_label}
        console.print_json(json.dumps(payload))
        return

    console.print("")
    console.print(Panel(f"[bold]Resume Quality Score[/bold]   {resume}", style="blue"))
    console.print(
        f"\n  Overall score: [{grade_style}]{total}/100  Grade {grade}  {grade_label}[/{grade_style}]"
        f"   ({result.word_count} words)\n"
    )

    if brief:
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Dimension", style="bold", width=26)
    table.add_column("Score", width=10)
    table.add_column("Max", width=6)
    table.add_column("Bar", width=20)

    for dim in result.dimensions:
        bar_filled = int(dim.pct / 5)
        bar = (
            "[green]" + "#" * bar_filled + "[/green]" + "[dim]" + "." * (20 - bar_filled) + "[/dim]"
        )
        pct_style = "green" if dim.pct >= 80 else ("yellow" if dim.pct >= 50 else "red")
        table.add_row(
            dim.name,
            f"[{pct_style}]{dim.score}[/{pct_style}]",
            str(dim.max_score),
            bar,
        )

    console.print(table)
    console.print(
        f"\n  Sections found: [green]{', '.join(result.found_sections) or 'none'}[/green]"
    )
    if result.missing_sections:
        console.print(f"  Missing sections: [red]{', '.join(result.missing_sections)}[/red]")
    console.print(
        f"  Quantified bullets: [cyan]{result.quantified_count}/{result.bullet_count}[/cyan]"
        f"   Action verbs: [cyan]{result.action_verb_count}[/cyan]"
    )

    all_suggestions = [s for dim in result.dimensions for s in dim.suggestions]
    if all_suggestions:
        console.print("\n  [bold yellow]Suggestions:[/bold yellow]")
        for i, sug in enumerate(all_suggestions, 1):
            console.print(f"  [yellow]{i}.[/yellow] {sug}")
    else:
        console.print("\n  [bold green]No major issues found![/bold green]")

    console.print("")


@main.command("optimize")
@click.argument("resume", type=click.Path(exists=True))
@click.option("--output", default=None, help="Output file path (default: <resume>-optimized.md)")
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option(
    "--format",
    "fmt",
    default=lambda: _cfg_default("format", "md"),
    type=click.Choice(["md", "pdf"]),
)
@click.option(
    "--explain", "show_explain", is_flag=True, default=False, help="Show a summary of changes made"
)
@click.option(
    "--diff", "show_diff", is_flag=True, default=False, help="Show section diff after optimizing"
)
def optimize(resume, output, model, fmt, show_explain, show_diff):
    """Improve a resume without targeting a specific job.

    Uses the LLM to strengthen bullet points, remove filler language, flag
    missing metrics, and tighten phrasing -- without changing any facts.

    \b
    Examples:
      resume-engine optimize master-resume.md
      resume-engine optimize master-resume.md --output stronger.md --model openai
      resume-engine optimize master-resume.md --explain
      resume-engine optimize master-resume.md --diff
    """
    import os

    from .optimizer import explain_changes, optimize_resume

    with open(resume) as f:
        original_text = f.read()

    console.print(Panel("[bold]resume-engine[/bold] -- optimize resume", style="blue"))
    console.print(f"[dim]Input: {len(original_text)} chars -- optimizing with {model}...[/dim]")

    improved_text = optimize_resume(original_text, model=model)

    # Determine output path
    if output is None:
        base, _ = os.path.splitext(resume)
        md_output = f"{base}-optimized.md"
    else:
        md_output = output if output.endswith(".md") else output

    with open(md_output, "w") as f:
        f.write(improved_text)
    console.print(f"[green]Optimized resume written to {md_output}[/green]")

    # Show explanation of changes
    if show_explain:
        console.print("\n[bold cyan]Changes made:[/bold cyan]")
        console.print("[dim]Asking LLM to explain changes...[/dim]")
        explanation = explain_changes(original_text, improved_text, model=model)
        console.print(explanation)
        console.print("")

    # Show diff
    if show_diff:
        from rich.table import Table

        from .differ import compute_diff

        result = compute_diff(original_text, improved_text)
        changed = [s for s in result.sections if s.is_changed]

        if changed:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Section", style="bold", width=24)
            table.add_column("Change", width=8)
            table.add_column("+Added", style="green", width=8)
            table.add_column("-Removed", style="red", width=10)

            for sec in changed:
                pct_str = f"{sec.change_pct}%"
                if sec.change_pct >= 60:
                    pct_style = "bold green"
                elif sec.change_pct >= 25:
                    pct_style = "yellow"
                else:
                    pct_style = "cyan"
                table.add_row(
                    sec.name,
                    f"[{pct_style}]{pct_str}[/{pct_style}]",
                    str(len(sec.added)),
                    str(len(sec.removed)),
                )

            console.print("")
            console.print(table)
        else:
            console.print("[dim]No section-level changes detected.[/dim]")

    if fmt == "pdf":
        from .pdf import markdown_to_pdf, md_path_to_pdf_path

        pdf_output = md_path_to_pdf_path(md_output)
        try:
            console.print("[dim]Converting to PDF via pandoc...[/dim]")
            markdown_to_pdf(md_output, pdf_output)
            console.print(f"[green]PDF written to {pdf_output}[/green]")
        except RuntimeError as e:
            console.print(f"[yellow]PDF conversion failed: {e}[/yellow]")

    console.print("")


@main.command("interview")
@click.option("--master", default=None, help="Path to master resume (markdown)")
@click.option(
    "--linkedin-url", default=None, help="LinkedIn profile URL to import as master resume"
)
@click.option("--linkedin-export", default=None, help="LinkedIn data export ZIP or directory")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option(
    "--count",
    default=10,
    show_default=True,
    help="Number of questions to generate (5-20 recommended)",
)
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option(
    "--with-followups",
    "with_followups",
    is_flag=True,
    default=False,
    help="Also generate likely follow-up/probing questions on resume specifics",
)
@click.option(
    "--output",
    default=None,
    help="Save prep sheet to a markdown file",
)
@click.option("--json", "json_output", is_flag=True, default=False, help="Output machine-readable JSON")
def interview(master, linkedin_url, linkedin_export, job, job_url, count, model, with_followups, output, json_output):
    """Generate tailored interview questions with STAR-method answer frameworks.

    Analyzes the job posting and your resume to predict likely questions
    across four categories: Behavioral, Technical, Culture Fit, and
    Resume Deep-Dives. Each question includes a STAR-method framework
    tailored to your actual experience.

    \b
    Examples:
      resume-engine interview --master resume.md --job posting.txt
      resume-engine interview --master resume.md --job-url https://example.com/jobs/123 --count 15
      resume-engine interview --master resume.md --job posting.txt --with-followups --output prep.md
      resume-engine interview --master resume.md --job posting.txt --json
    """
    import json
    from dataclasses import asdict

    from .interview import generate_interview_prep

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")

    if not json_output:
        console.print(Panel("[bold]resume-engine[/bold] -- interview prep", style="blue"))

    master_text = _load_master(master, linkedin_url, linkedin_export)

    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    if not json_output:
        console.print(f"[dim]Generating {count} interview questions with {model}...[/dim]")

    result = generate_interview_prep(
        master_text,
        job_text,
        model=model,
        count=count,
        with_followups=with_followups,
    )

    if json_output:
        payload = asdict(result)
        payload["master"] = master
        payload["job"] = job
        payload["job_url"] = job_url
        payload["model"] = model
        payload["count"] = count
        payload["with_followups"] = with_followups
        console.print_json(json.dumps(payload))
        return

    # Category colors
    CATEGORY_STYLES = {
        "behavioral": "bold magenta",
        "technical": "bold cyan",
        "culture fit": "bold blue",
        "resume deep-dive": "bold yellow",
        "general": "bold white",
    }

    def cat_style(cat: str) -> str:
        return CATEGORY_STYLES.get(cat.lower(), "bold white")

    console.print("")
    console.print(f"[bold]Interview Questions[/bold]  ({len(result.questions)} generated)\n")

    md_lines = ["# Interview Prep\n"]
    md_lines.append(f"Generated {len(result.questions)} questions.\n")

    if result.questions:
        # Group by category for display
        from collections import defaultdict

        by_cat = defaultdict(list)
        for q in result.questions:
            by_cat[q.category].append(q)

        for cat, qs in by_cat.items():
            style = cat_style(cat)
            console.print(f"[{style}]== {cat} ==[/{style}]\n")
            md_lines.append(f"## {cat}\n")

            for q in qs:
                console.print(f"  [bold]{q.number}.[/bold] {q.question}")
                md_lines.append(f"### Q{q.number}. {q.question}\n")

                if q.framework:
                    console.print(f"     [dim]STAR: {q.framework}[/dim]")
                    md_lines.append(f"**STAR Framework:** {q.framework}\n")

                console.print("")
                md_lines.append("")
    else:
        # Fallback: print raw output if parsing failed
        console.print(result.raw_questions)
        md_lines.append(result.raw_questions)

    if result.followups:
        console.print("\n[bold yellow]== Likely Follow-Up / Probing Questions ==[/bold yellow]\n")
        md_lines.append("## Likely Follow-Up Questions\n")

        for fq in result.followups:
            console.print(f"  [bold]{fq.number}.[/bold] {fq.question}")
            md_lines.append(f"### FQ{fq.number}. {fq.question}\n")

            if fq.probing:
                console.print(f"     [dim]Probing: {fq.probing}[/dim]")
                md_lines.append(f"**Probing:** {fq.probing}\n")

            console.print("")
            md_lines.append("")
    elif result.raw_followups:
        console.print("\n[bold yellow]== Likely Follow-Up / Probing Questions ==[/bold yellow]\n")
        console.print(result.raw_followups)
        md_lines.append("## Likely Follow-Up Questions\n")
        md_lines.append(result.raw_followups)

    # Save to file if requested
    if output:
        with open(output, "w") as f:
            f.write("\n".join(md_lines))
        console.print(f"[green]Interview prep sheet saved to {output}[/green]")

    console.print("")


@main.command("cover-score")
@click.argument("cover_letter", type=click.Path(exists=True))
@click.option(
    "--brief", is_flag=True, default=False, help="Show score only (no detailed breakdown)"
)
def cover_score_cmd(cover_letter, brief):
    """Score a cover letter's quality (0-100) across 5 dimensions.

    Checks opening hook, company/role specificity, value proposition,
    length, and filler language. No LLM required -- runs instantly.

    \b
    Examples:
      resume-engine cover-score cover-letter.md
      resume-engine cover-score cover-letter.md --brief
    """
    from rich.table import Table

    from .cover_scorer import score_cover_letter

    with open(cover_letter) as f:
        text = f.read()

    result = score_cover_letter(text)
    console.print("")
    console.print(Panel(f"[bold]Cover Letter Quality Score[/bold]   {cover_letter}", style="blue"))

    total = result.total
    if total >= 85:
        grade = "A"
        grade_style = "bold green"
        grade_label = "Excellent"
    elif total >= 70:
        grade = "B"
        grade_style = "bold cyan"
        grade_label = "Good"
    elif total >= 50:
        grade = "C"
        grade_style = "bold yellow"
        grade_label = "Needs work"
    else:
        grade = "D"
        grade_style = "bold red"
        grade_label = "Significant gaps"

    console.print(
        f"\n  Overall score: [{grade_style}]{total}/100  Grade {grade}  {grade_label}[/{grade_style}]"
        f"   ({result.word_count} words)\n"
    )

    if brief:
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Dimension", style="bold", width=28)
    table.add_column("Score", width=8)
    table.add_column("Max", width=6)
    table.add_column("Bar", width=20)

    for dim in result.dimensions:
        bar_filled = int(dim.pct / 5)
        bar = (
            "[green]" + "#" * bar_filled + "[/green]" + "[dim]" + "." * (20 - bar_filled) + "[/dim]"
        )
        pct_style = "green" if dim.pct >= 80 else ("yellow" if dim.pct >= 50 else "red")
        table.add_row(
            dim.name,
            f"[{pct_style}]{dim.score}[/{pct_style}]",
            str(dim.max_score),
            bar,
        )

    console.print(table)

    flags = []
    if result.has_company_name:
        flags.append("[green]Company named[/green]")
    else:
        flags.append("[red]No company name[/red]")
    if result.has_role_name:
        flags.append("[green]Role referenced[/green]")
    else:
        flags.append("[red]No role title[/red]")
    if result.generic_opener:
        flags.append("[red]Generic opener[/red]")
    else:
        flags.append("[green]Strong opener[/green]")

    console.print("\n  " + "   ".join(flags))
    console.print(
        f"\n  Value verbs: [cyan]{result.value_verb_count}[/cyan]"
        f"   Metrics/specifics: [cyan]{result.specificity_count}[/cyan]"
    )

    all_suggestions = [s for dim in result.dimensions for s in dim.suggestions]
    if all_suggestions:
        console.print("\n  [bold yellow]Suggestions:[/bold yellow]")
        for i, sug in enumerate(all_suggestions, 1):
            console.print(f"  [yellow]{i}.[/yellow] {sug}")
    else:
        console.print("\n  [bold green]No major issues found![/bold green]")

    console.print("")


@main.group()
def track():
    """Track job applications in a local SQLite log.

    \b
    Commands:
      add     Log a new application
      list    Show all applications (with optional filters)
      export  Export tracked applications to JSON or CSV
      update  Update status or notes on an application
      delete  Remove an application from the log
      show    Show full details for one application
      stats   Summary of application pipeline
    """
    pass


@track.command("add")
@click.option("--company", required=True, help="Company name")
@click.option("--role", required=True, help="Job title / role")
@click.option(
    "--date", "applied_date", default=None, help="Date applied (YYYY-MM-DD, default: today)"
)
@click.option(
    "--status",
    default="applied",
    type=click.Choice(["applied", "screening", "interview", "offer", "rejected", "withdrawn"]),
    show_default=True,
    help="Application status",
)
@click.option("--url", default=None, help="Job posting URL")
@click.option("--notes", default=None, help="Free-form notes")
def track_add(company, role, applied_date, status, url, notes):
    """Log a new job application."""
    from .tracker import add_application

    app_id = add_application(
        company=company,
        role=role,
        applied_date=applied_date,
        status=status,
        url=url,
        notes=notes,
    )
    console.print(f"[green]Application #{app_id} added:[/green] {company} -- {role}  [{status}]")


@track.command("list")
@click.option("--status", default=None, help="Filter by status")
@click.option("--company", default=None, help="Filter by company name (partial match)")
@click.option("--limit", default=50, show_default=True, help="Max results to show")
def track_list(status, company, limit):
    """Show tracked applications, newest first."""
    from rich.table import Table

    from .tracker import STATUS_STYLES, list_applications

    rows = list_applications(status=status, company=company, limit=limit)

    if not rows:
        console.print("[dim]No applications found.[/dim]")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ID", width=5)
    table.add_column("Company", width=22)
    table.add_column("Role", width=26)
    table.add_column("Date", width=12)
    table.add_column("Status", width=12)
    table.add_column("Notes", width=30)

    for row in rows:
        style = STATUS_STYLES.get(row["status"], "white")
        notes_preview = (row["notes"] or "")[:28] + ("..." if len(row["notes"] or "") > 28 else "")
        table.add_row(
            str(row["id"]),
            row["company"],
            row["role"],
            row["date"],
            f"[{style}]{row['status']}[/{style}]",
            f"[dim]{notes_preview}[/dim]" if notes_preview else "",
        )

    console.print(table)
    console.print(f"[dim]{len(rows)} application(s)[/dim]")


@track.command("export")
@click.option("--status", default=None, help="Filter by status")
@click.option("--company", default=None, help="Filter by company name (partial match)")
@click.option("--limit", default=None, type=int, help="Max rows to export")
@click.option(
    "--format",
    "export_format",
    default="json",
    type=click.Choice(["json", "csv"]),
    show_default=True,
    help="Export file format",
)
@click.option(
    "--output",
    default=None,
    help="Write export to a file instead of stdout",
)
def track_export(status, company, limit, export_format, output):
    """Export tracked applications to JSON or CSV."""
    import csv
    import json
    import sys

    from .tracker import list_applications

    rows = list_applications(status=status, company=company, limit=limit)

    if export_format == "json":
        payload = json.dumps(rows, indent=2)
        if output:
            with open(output, "w") as f:
                f.write(payload + "\n")
            console.print(f"[green]Exported {len(rows)} application(s) to {output}[/green]")
        else:
            click.echo(payload)
        return

    fieldnames = [
        "id",
        "company",
        "role",
        "date",
        "status",
        "url",
        "notes",
        "created_at",
        "updated_at",
    ]

    if output:
        with open(output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        console.print(f"[green]Exported {len(rows)} application(s) to {output}[/green]")
        return

    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


@track.command("show")
@click.argument("app_id", type=int)
def track_show(app_id):
    """Show full details for a single application."""
    from .tracker import STATUS_STYLES, get_application

    row = get_application(app_id)
    if not row:
        console.print(f"[red]No application with id {app_id}[/red]")
        raise SystemExit(1)

    style = STATUS_STYLES.get(row["status"], "white")
    console.print("")
    console.print(
        Panel(
            f"[bold]#{row['id']}[/bold]  {row['company']}  --  {row['role']}",
            style="blue",
        )
    )
    console.print(f"  Date applied:  {row['date']}")
    console.print(f"  Status:        [{style}]{row['status']}[/{style}]")
    if row.get("url"):
        console.print(f"  URL:           {row['url']}")
    if row.get("notes"):
        console.print(f"  Notes:         {row['notes']}")
    console.print(f"  Created:       {row['created_at']}")
    console.print(f"  Updated:       {row['updated_at']}")
    console.print("")


@track.command("update")
@click.argument("app_id", type=int)
@click.option(
    "--status",
    default=None,
    type=click.Choice(["applied", "screening", "interview", "offer", "rejected", "withdrawn"]),
    help="New status",
)
@click.option("--notes", default=None, help="Update notes (replaces existing)")
@click.option("--url", default=None, help="Update job posting URL")
def track_update(app_id, status, notes, url):
    """Update status, notes, or URL for an application."""
    from .tracker import update_application

    if not status and notes is None and url is None:
        raise click.UsageError("Provide at least one of --status, --notes, --url")

    ok = update_application(app_id, status=status, notes=notes, url=url)
    if not ok:
        console.print(f"[red]No application with id {app_id}[/red]")
        raise SystemExit(1)

    parts = []
    if status:
        parts.append(f"status={status}")
    if notes is not None:
        parts.append("notes updated")
    if url is not None:
        parts.append("url updated")
    console.print(f"[green]Application #{app_id} updated:[/green] {', '.join(parts)}")


@track.command("delete")
@click.argument("app_id", type=int)
@click.confirmation_option(prompt="Delete this application from the log?")
def track_delete(app_id):
    """Remove an application from the tracker."""
    from .tracker import delete_application

    ok = delete_application(app_id)
    if not ok:
        console.print(f"[red]No application with id {app_id}[/red]")
        raise SystemExit(1)
    console.print(f"[green]Application #{app_id} deleted.[/green]")


@track.command("stats")
def track_stats():
    """Show a summary of your application pipeline."""
    from .tracker import STATUS_STYLES, VALID_STATUSES, get_stats

    stats = get_stats()
    total = stats["total"]
    by_status = stats["by_status"]

    console.print("")
    console.print(Panel("[bold]Application Tracker -- Pipeline Summary[/bold]", style="blue"))
    console.print(f"  Total applications tracked: [bold]{total}[/bold]\n")

    for s in VALID_STATUSES:
        count = by_status.get(s, 0)
        style = STATUS_STYLES.get(s, "white")
        bar = "#" * count
        console.print(f"  [{style}]{s:<12}[/{style}]  {count:>4}  [dim]{bar}[/dim]")

    console.print("")


@main.command("fit")
@click.option("--master", default=None, help="Path to master resume (markdown)")
@click.option(
    "--linkedin-url", default=None, help="LinkedIn profile URL to import as master resume"
)
@click.option("--linkedin-export", default=None, help="LinkedIn data export ZIP or directory")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option(
    "--model",
    default=lambda: _cfg_default("model", "ollama"),
    type=click.Choice(["ollama", "openai", "anthropic"]),
)
@click.option("--brief", is_flag=True, default=False, help="Show score and verdict only")
@click.option(
    "--output",
    default=None,
    help="Save full fit report to a markdown file",
)
@click.option("--json", "json_output", is_flag=True, default=False, help="Output machine-readable JSON")
def fit(master, linkedin_url, linkedin_export, job, job_url, model, brief, output, json_output):
    """Score how well you fit a job posting (0-100) before applying.

    Combines ATS keyword analysis with LLM-powered evaluation of skills
    coverage, seniority match, and domain fit. Gives a clear recommendation:
    Apply, Apply with caution, or Skip.

    \b
    Examples:
      resume-engine fit --master resume.md --job posting.txt
      resume-engine fit --master resume.md --job-url https://example.com/jobs/123
      resume-engine fit --master resume.md --job posting.txt --model openai --output report.md
      resume-engine fit --master resume.md --job posting.txt --json
    """
    import json
    from dataclasses import asdict

    from .fit import assess_fit

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")

    if not json_output:
        console.print(Panel("[bold]resume-engine[/bold] -- job fit assessment", style="blue"))

    master_text = _load_master(master, linkedin_url, linkedin_export)

    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    if not json_output:
        console.print(f"[dim]Running fit analysis with {model}...[/dim]")

    result = assess_fit(master_text, job_text, model=model)

    if json_output:
        payload = asdict(result)
        payload["master"] = master
        payload["job"] = job
        payload["job_url"] = job_url
        payload["model"] = model
        console.print_json(json.dumps(payload))
        return

    # Recommendation style
    REC_STYLES = {
        "Apply": ("bold green", "green"),
        "Apply with caution": ("bold yellow", "yellow"),
        "Skip": ("bold red", "red"),
    }
    rec_bold, rec_color = REC_STYLES.get(result.recommendation, ("bold white", "white"))

    # Total score style
    total = result.total
    if total >= 80:
        total_style = "bold green"
    elif total >= 65:
        total_style = "bold cyan"
    elif total >= 45:
        total_style = "bold yellow"
    else:
        total_style = "bold red"

    console.print("")
    console.print(
        f"  Fit score:       [{total_style}]{total}/100  {result.verdict}[/{total_style}]"
    )
    console.print(f"  Recommendation:  [{rec_bold}]{result.recommendation}[/{rec_bold}]")
    console.print(f"  ATS keyword match: [dim]{result.ats_score}%[/dim]")

    if brief:
        if result.verdict:
            console.print(f"\n  [dim]{result.verdict}[/dim]")
        console.print("")
        return

    # Dimension breakdown
    from rich.table import Table

    console.print("")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Dimension", style="bold", width=28)
    table.add_column("Score", width=8)
    table.add_column("Max", width=6)
    table.add_column("Bar", width=20)

    for dim in result.dimensions:
        bar_filled = int(dim.pct / 5)
        bar = (
            "[green]" + "#" * bar_filled + "[/green]" + "[dim]" + "." * (20 - bar_filled) + "[/dim]"
        )
        pct_style = "green" if dim.pct >= 80 else ("yellow" if dim.pct >= 50 else "red")
        table.add_row(
            dim.name,
            f"[{pct_style}]{dim.score}[/{pct_style}]",
            str(dim.max_score),
            bar,
        )

    console.print(table)

    # Strengths
    if result.strengths:
        console.print("\n  [bold green]Strengths:[/bold green]")
        for s in result.strengths:
            console.print(f"    [green]+[/green] {s}")

    # Gaps
    if result.gaps:
        console.print("\n  [bold red]Gaps / Risks:[/bold red]")
        for g in result.gaps:
            console.print(f"    [red]-[/red] {g}")

    # Verdict sentence
    if result.verdict:
        console.print(f"\n  [bold]Verdict:[/bold] [{rec_color}]{result.verdict}[/{rec_color}]")

    console.print("")

    # Save report
    if output:
        md_lines = [
            "# Job Fit Report\n",
            f"**Fit Score:** {result.total}/100 -- {result.verdict}\n",
            f"**Recommendation:** {result.recommendation}\n",
            f"**ATS Keyword Match:** {result.ats_score}%\n",
            "\n## Dimension Scores\n",
        ]
        for dim in result.dimensions:
            md_lines.append(f"- **{dim.name}:** {dim.score}/{dim.max_score} ({dim.pct}%)\n")

        if result.strengths:
            md_lines.append("\n## Strengths\n")
            for s in result.strengths:
                md_lines.append(f"- {s}\n")

        if result.gaps:
            md_lines.append("\n## Gaps / Risks\n")
            for g in result.gaps:
                md_lines.append(f"- {g}\n")

        if result.verdict:
            md_lines.append(f"\n## Verdict\n{result.verdict}\n")

        with open(output, "w") as f:
            f.writelines(md_lines)
        console.print(f"[green]Fit report saved to {output}[/green]")
        console.print("")


@main.command("validate")
@click.option("--master", required=True, help="Path to master resume (markdown)")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--resume", "resume_output", default=None, help="Path to tailored resume output")
@click.option("--cover-letter", default=None, help="Path to cover letter output")
@click.option("--output", default=None, help="Save the validation report to markdown")
def validate_cmd(master, job, job_url, resume_output, cover_letter, output):
    """Validate tailored output against the source resume and job posting.

    Flags likely unsupported claims, title/date/company drift, and
    suspicious rewrites before you send a resume or cover letter.

    
    Examples:
      resume-engine validate --master resume.md --job posting.txt --resume tailored.md
      resume-engine validate --master resume.md --job posting.txt --cover-letter cover.md
      resume-engine validate --master resume.md --job posting.txt --resume tailored.md --cover-letter cover.md
    """
    from rich.table import Table

    from .validate import validate_outputs

    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")
    if not resume_output and not cover_letter:
        raise click.UsageError("Provide --resume, --cover-letter, or both")

    console.print(Panel("[bold]resume-engine[/bold] -- grounded validation", style="blue"))

    with open(master) as f:
        master_text = f.read()

    if job:
        with open(job) as f:
            job_text = f.read()
    else:
        from .scraper import scrape_job_posting

        job_text = scrape_job_posting(job_url)

    resume_text = None
    if resume_output:
        with open(resume_output) as f:
            resume_text = f.read()

    cover_text = None
    if cover_letter:
        with open(cover_letter) as f:
            cover_text = f.read()

    report = validate_outputs(
        master_text=master_text,
        job_text=job_text,
        tailored_resume_text=resume_text,
        cover_letter_text=cover_text,
    )

    md_lines = ["# Validation Report\n"]
    has_high = False

    for target in report.targets:
        score_style = (
            "bold green"
            if target.score >= 85
            else ("bold yellow" if target.score >= 65 else "bold red")
        )
        console.print("")
        console.print(
            f"[bold]{target.label.title()}[/bold] trust score: [{score_style}]{target.score}/100[/{score_style}]"
        )
        md_lines.append(f"## {target.label.title()}\n")
        md_lines.append(f"Trust score: {target.score}/100\n")

        if not target.issues:
            console.print("  [green]No obvious grounding problems detected.[/green]")
            md_lines.append("- No obvious grounding problems detected.\n")
            continue

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Severity", width=8)
        table.add_column("Category", width=18)
        table.add_column("Message", width=34)
        table.add_column("Evidence", width=34)

        for issue in target.issues:
            if issue.severity == "high":
                has_high = True
            sev_style = {"high": "red", "medium": "yellow", "low": "cyan"}.get(
                issue.severity, "white"
            )
            table.add_row(
                f"[{sev_style}]{issue.severity}[/{sev_style}]",
                issue.category,
                issue.message,
                issue.evidence[:120],
            )
            md_lines.append(f"- **{issue.severity.upper()} | {issue.category}:** {issue.message}\n")
            if issue.evidence:
                md_lines.append(f"  - Evidence: `{issue.evidence}`\n")
            if issue.suggestion:
                md_lines.append(f"  - Suggestion: {issue.suggestion}\n")

        console.print(table)

    console.print("")
    if has_high:
        console.print(
            "[bold red]High-risk issues found.[/bold red] Review the flagged lines before sending anything."
        )
    else:
        console.print(
            "[bold green]Validation complete.[/bold green] Review any warnings, then send with confidence."
        )

    if output:
        with open(output, "w") as f:
            f.writelines(md_lines)
        console.print(f"[green]Validation report saved to {output}[/green]")

    console.print("")


@main.command("init")
@click.option(
    "--output",
    default="master-resume.md",
    show_default=True,
    help="Output file path for the master resume",
)
def init_cmd(output):
    """Create a master resume from scratch via guided prompts.

    Walks you through entering your contact info, summary, skills,
    work experience, education, and certifications step by step.
    No existing resume file or LLM required.

    \b
    Examples:
      resume-engine init
      resume-engine init --output my-resume.md
    """
    import os

    from .init import Education, Experience, ResumeData, render_markdown

    console.print(
        Panel(
            "[bold]resume-engine[/bold] -- master resume builder\n"
            "[dim]Answer the prompts below to build your resume. Press Enter to skip optional fields.[/dim]",
            style="blue",
        )
    )

    data = ResumeData()

    # Contact info
    console.print("\n[bold cyan]Contact Information[/bold cyan]")
    data.name = click.prompt("  Full name", type=str)
    data.email = click.prompt("  Email", type=str, default="", show_default=False)
    data.phone = click.prompt("  Phone", type=str, default="", show_default=False)
    data.location = click.prompt(
        "  Location (city, state)", type=str, default="", show_default=False
    )
    data.linkedin = click.prompt("  LinkedIn URL", type=str, default="", show_default=False)
    data.website = click.prompt("  Website/portfolio URL", type=str, default="", show_default=False)

    # Summary
    console.print("\n[bold cyan]Professional Summary[/bold cyan]")
    console.print("  [dim]2-3 sentence overview of your background and goals.[/dim]")
    data.summary = click.prompt("  Summary", type=str, default="", show_default=False)

    # Skills
    console.print("\n[bold cyan]Skills[/bold cyan]")
    console.print(
        "  [dim]Enter skills separated by commas (e.g. Python, AWS, Project Management).[/dim]"
    )
    skills_raw = click.prompt("  Skills", type=str, default="", show_default=False)
    if skills_raw.strip():
        data.skills = [s.strip() for s in skills_raw.split(",") if s.strip()]

    # Experience
    console.print("\n[bold cyan]Work Experience[/bold cyan]")
    console.print("  [dim]Add positions one at a time. Leave company blank to stop.[/dim]")

    while True:
        console.print("")
        company = click.prompt(
            "  Company name (blank to finish)", type=str, default="", show_default=False
        )
        if not company.strip():
            break
        title = click.prompt("  Job title", type=str)
        start = click.prompt("  Start date (e.g. Jan 2020)", type=str)
        end = click.prompt("  End date (e.g. Present)", type=str, default="Present")

        console.print("  [dim]Add bullet points for this role. Leave blank to stop.[/dim]")
        bullets: list[str] = []
        while True:
            bullet = click.prompt(
                f"    Bullet {len(bullets) + 1}", type=str, default="", show_default=False
            )
            if not bullet.strip():
                break
            bullets.append(bullet.strip())

        data.experience.append(
            Experience(
                company=company.strip(),
                title=title.strip(),
                start=start.strip(),
                end=end.strip(),
                bullets=bullets,
            )
        )

    # Education
    console.print("\n[bold cyan]Education[/bold cyan]")
    console.print("  [dim]Add degrees one at a time. Leave school blank to stop.[/dim]")

    while True:
        console.print("")
        school = click.prompt(
            "  School name (blank to finish)", type=str, default="", show_default=False
        )
        if not school.strip():
            break
        degree = click.prompt("  Degree (e.g. B.S. Computer Science)", type=str)
        year = click.prompt("  Year (e.g. 2020)", type=str, default="", show_default=False)

        data.education.append(
            Education(school=school.strip(), degree=degree.strip(), year=year.strip())
        )

    # Certifications
    console.print("\n[bold cyan]Certifications[/bold cyan]")
    console.print("  [dim]Add certifications one at a time. Leave blank to stop.[/dim]")

    while True:
        cert = click.prompt(
            "  Certification (blank to finish)", type=str, default="", show_default=False
        )
        if not cert.strip():
            break
        data.certifications.append(cert.strip())

    # Render and save
    md = render_markdown(data)

    if os.path.exists(output) and not click.confirm(
        f"\n  {output} already exists. Overwrite?", default=False
    ):
        console.print("[yellow]Aborted.[/yellow]")
        raise SystemExit(0)

    with open(output, "w") as f:
        f.write(md)

    console.print(f"\n[bold green]Master resume written to {output}[/bold green]")

    # Quick stats
    sections = []
    if data.summary:
        sections.append("Summary")
    if data.skills:
        sections.append("Skills")
    if data.experience:
        sections.append(f"Experience ({len(data.experience)} roles)")
    if data.education:
        sections.append(f"Education ({len(data.education)} entries)")
    if data.certifications:
        sections.append(f"Certifications ({len(data.certifications)})")
    console.print(f"  [dim]Sections: {', '.join(sections)}[/dim]")

    console.print(
        "\n[dim]Next steps:[/dim]\n"
        f"  [dim]1. Review and polish: [bold]{output}[/bold][/dim]\n"
        "  [dim]2. Score it: [bold]resume-engine score {output}[/bold][/dim]\n"
        "  [dim]3. Optimize with AI: [bold]resume-engine optimize {output}[/bold][/dim]\n"
        "  [dim]4. Tailor to a job: [bold]resume-engine tailor --master {output} --job posting.txt[/bold][/dim]\n"
    )


if __name__ == "__main__":
    main()
