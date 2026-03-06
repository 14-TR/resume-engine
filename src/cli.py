"""CLI entry point for resume-engine."""
import click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def main():
    """AI-powered resume tailoring CLI."""
    pass

@main.command()
@click.option("--master", required=True, help="Path to master resume (markdown)")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--output", default="tailored-resume.md", help="Output file path")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
@click.option("--format", "fmt", default="md", type=click.Choice(["md", "pdf"]))
def tailor(master, job, job_url, output, model, fmt):
    """Tailor a resume to a specific job posting."""
    from .engine import tailor_resume
    
    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")
    
    console.print(Panel("[bold]resume-engine[/bold] — tailoring resume", style="blue"))
    
    # Load master resume
    with open(master) as f:
        master_text = f.read()
    console.print(f"[dim]Loaded master resume: {len(master_text)} chars[/dim]")
    
    # Load job posting
    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting
        job_text = scrape_job_posting(job_url)
    
    console.print(f"[dim]Loaded job posting: {len(job_text)} chars[/dim]")
    
    # Tailor
    result = tailor_resume(master_text, job_text, model=model)
    
    # Output
    with open(output, "w") as f:
        f.write(result)
    
    console.print(f"[green]Tailored resume written to {output}[/green]")

@main.command()
@click.option("--master", required=True, help="Path to master resume (markdown)")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--output", default="cover-letter.md", help="Output file path")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
def cover(master, job, job_url, output, model):
    """Generate a cover letter for a job posting."""
    from .engine import generate_cover_letter
    
    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")
    
    console.print(Panel("[bold]resume-engine[/bold] — generating cover letter", style="blue"))
    
    with open(master) as f:
        master_text = f.read()
    
    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting
        job_text = scrape_job_posting(job_url)
    
    result = generate_cover_letter(master_text, job_text, model=model)
    
    with open(output, "w") as f:
        f.write(result)
    
    console.print(f"[green]Cover letter written to {output}[/green]")

@main.command()
@click.option("--master", required=True, help="Path to master resume (markdown)")
@click.option("--job", default=None, help="Path to job posting text file")
@click.option("--job-url", default=None, help="URL of job posting to scrape")
@click.option("--outdir", default="./application", help="Output directory")
@click.option("--model", default="ollama", type=click.Choice(["ollama", "openai", "anthropic"]))
def package(master, job, job_url, outdir, model):
    """Generate full application package (resume + cover letter)."""
    import os
    os.makedirs(outdir, exist_ok=True)
    
    console.print(Panel("[bold]resume-engine[/bold] — full application package", style="blue"))
    
    with open(master) as f:
        master_text = f.read()
    
    if job:
        with open(job) as f:
            job_text = f.read()
    elif job_url:
        from .scraper import scrape_job_posting
        job_text = scrape_job_posting(job_url)
    
    if not job and not job_url:
        raise click.UsageError("Provide either --job or --job-url")
    
    from .engine import tailor_resume, generate_cover_letter
    
    resume = tailor_resume(master_text, job_text, model=model)
    with open(os.path.join(outdir, "resume.md"), "w") as f:
        f.write(resume)
    console.print("[green]Resume written[/green]")
    
    letter = generate_cover_letter(master_text, job_text, model=model)
    with open(os.path.join(outdir, "cover-letter.md"), "w") as f:
        f.write(letter)
    console.print("[green]Cover letter written[/green]")
    
    console.print(f"\n[bold green]Application package ready in {outdir}/[/bold green]")

if __name__ == "__main__":
    main()
