"""Batch processing -- tailor resume to multiple jobs at once."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table


@dataclass
class JobSpec:
    """A single job in a batch run."""
    name: str
    job_file: Optional[str] = None
    job_url: Optional[str] = None

    def load_text(self) -> str:
        if self.job_file:
            with open(self.job_file) as f:
                return f.read()
        elif self.job_url:
            from .scraper import scrape_job_posting
            return scrape_job_posting(self.job_url)
        raise ValueError(f"Job '{self.name}' has no file or URL")


@dataclass
class BatchResult:
    name: str
    success: bool
    resume_path: str = ""
    cover_path: str = ""
    pdf_paths: list = field(default_factory=list)
    error: str = ""
    elapsed: float = 0.0


def load_jobs_from_dir(jobs_dir: str) -> list[JobSpec]:
    """Load all .txt and .md files from a directory as job specs."""
    jobs = []
    p = Path(jobs_dir)
    for ext in ("*.txt", "*.md"):
        for f in sorted(p.glob(ext)):
            jobs.append(JobSpec(name=f.stem, job_file=str(f)))
    return jobs


def load_jobs_from_manifest(manifest_path: str) -> list[JobSpec]:
    """Load job specs from a JSON manifest file.

    Manifest format (list of objects):
      [
        {"name": "acme-corp",  "job": "/path/to/acme.txt"},
        {"name": "startup-x",  "job_url": "https://..."},
        {"name": "big-co",     "job": "jobs/bigco.txt"}
      ]
    """
    with open(manifest_path) as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Manifest must be a JSON array")

    jobs = []
    manifest_dir = str(Path(manifest_path).parent)

    for i, entry in enumerate(data):
        name = entry.get("name") or entry.get("title") or f"job-{i+1}"

        job_file = entry.get("job") or entry.get("job_file")
        if job_file and not os.path.isabs(job_file):
            job_file = os.path.join(manifest_dir, job_file)

        job_url = entry.get("job_url") or entry.get("url")

        jobs.append(JobSpec(name=name, job_file=job_file, job_url=job_url))

    return jobs


def run_batch(
    master_text: str,
    jobs: list[JobSpec],
    outdir: str,
    model: str = "ollama",
    fmt: str = "md",
    template: Optional[str] = None,
    with_cover: bool = False,
    console: Optional[Console] = None,
) -> list[BatchResult]:
    """Run batch tailoring and return results."""
    from .engine import tailor_resume, generate_cover_letter
    from .pdf import markdown_to_pdf, md_path_to_pdf_path

    if console is None:
        console = Console()

    os.makedirs(outdir, exist_ok=True)
    results: list[BatchResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task("Processing jobs...", total=len(jobs))

        for job_spec in jobs:
            start = time.time()
            progress.update(task, description=f"[cyan]{job_spec.name}[/cyan]")

            job_outdir = os.path.join(outdir, job_spec.name)
            os.makedirs(job_outdir, exist_ok=True)

            try:
                # Load job text
                job_text = job_spec.load_text()

                # Tailor resume
                tailored = tailor_resume(master_text, job_text, model=model, template=template)
                resume_md = os.path.join(job_outdir, "resume.md")
                with open(resume_md, "w") as f:
                    f.write(tailored)

                result = BatchResult(
                    name=job_spec.name,
                    success=True,
                    resume_path=resume_md,
                )

                # Cover letter
                if with_cover:
                    letter = generate_cover_letter(master_text, job_text, model=model, template=template)
                    cover_md = os.path.join(job_outdir, "cover-letter.md")
                    with open(cover_md, "w") as f:
                        f.write(letter)
                    result.cover_path = cover_md

                # PDF conversion
                if fmt == "pdf":
                    pdf_paths = []
                    try:
                        resume_pdf = md_path_to_pdf_path(resume_md)
                        markdown_to_pdf(resume_md, resume_pdf)
                        pdf_paths.append(resume_pdf)
                        if with_cover and result.cover_path:
                            cover_pdf = md_path_to_pdf_path(result.cover_path)
                            markdown_to_pdf(result.cover_path, cover_pdf)
                            pdf_paths.append(cover_pdf)
                    except RuntimeError as e:
                        console.print(f"  [yellow]PDF failed for {job_spec.name}: {e}[/yellow]")
                    result.pdf_paths = pdf_paths

                result.elapsed = time.time() - start

            except Exception as e:
                result = BatchResult(
                    name=job_spec.name,
                    success=False,
                    error=str(e),
                    elapsed=time.time() - start,
                )

            results.append(result)
            progress.advance(task)

    return results


def print_summary(results: list[BatchResult], console: Console, fmt: str = "md", with_cover: bool = False) -> None:
    """Print a summary table of batch results."""
    table = Table(title="Batch Results", show_header=True, header_style="bold cyan")
    table.add_column("Job", style="bold", min_width=16)
    table.add_column("Status", width=8)
    table.add_column("Resume", width=8)
    if with_cover:
        table.add_column("Cover", width=8)
    if fmt == "pdf":
        table.add_column("PDFs", width=6)
    table.add_column("Time", width=8)
    table.add_column("Notes")

    succeeded = 0
    failed = 0

    for r in results:
        elapsed_str = f"{r.elapsed:.1f}s"
        if r.success:
            succeeded += 1
            status = "[green]OK[/green]"
            resume_str = "[green]yes[/green]"
            row = [r.name, status, resume_str]
            if with_cover:
                row.append("[green]yes[/green]" if r.cover_path else "[dim]no[/dim]")
            if fmt == "pdf":
                row.append(str(len(r.pdf_paths)) if r.pdf_paths else "[dim]0[/dim]")
            row.append(elapsed_str)
            row.append("")
        else:
            failed += 1
            status = "[red]FAIL[/red]"
            row = [r.name, status, "[dim]--[/dim]"]
            if with_cover:
                row.append("[dim]--[/dim]")
            if fmt == "pdf":
                row.append("[dim]--[/dim]")
            row.append(elapsed_str)
            row.append(f"[red]{r.error[:60]}[/red]")

        table.add_row(*row)

    console.print(table)
    console.print(
        f"\n[bold]Summary:[/bold] [green]{succeeded} succeeded[/green]"
        + (f"  [red]{failed} failed[/red]" if failed else "")
    )
