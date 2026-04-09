# resume-engine

**[Documentation](https://14-tr.github.io/resume-engine)** | [PyPI](https://pypi.org/project/resume-engine/) | [GitHub](https://github.com/14-TR/resume-engine)

CLI tool that takes a master resume + job posting and produces a tailored resume, cover letter, interview prep, and more. Local-first with Ollama, or use OpenAI/Anthropic.

```bash
pip install resume-engine
```

## Quick Start

```bash
# Tailor resume to a job posting
resume-engine tailor --master resume.md --job posting.txt --output tailored.md

# Full application package (resume + cover letter)
resume-engine package --master resume.md --job posting.txt --outdir ./application/

# Generate a validation report with the package
resume-engine package --master resume.md --job posting.txt --outdir ./application/ --validate-report

# Score your resume quality (instant, no LLM)
resume-engine score resume.md

# Validate a tailored resume before sending
resume-engine validate --master resume.md --job posting.txt --resume tailored.md

# Diagnose local setup issues before you start
resume-engine doctor

# Track where you've applied
resume-engine track add --company "Acme Corp" --role "Staff Engineer"
```

## Commands

### tailor

Rewrite your resume to match a specific job posting. Reorders sections, emphasizes relevant experience, and matches keywords.

```bash
resume-engine tailor --master resume.md --job posting.txt --output tailored.md

# From a URL (scrapes job requirements)
resume-engine tailor --master resume.md --job-url "https://careers.example.com/12345"

# With a specific template style
resume-engine tailor --master resume.md --job posting.txt --template technical

# Interactive mode (asks gap-filling questions first)
resume-engine tailor --master resume.md --job posting.txt --interactive

# PDF output
resume-engine tailor --master resume.md --job posting.txt --format pdf
```

### cover

Generate a cover letter matched to the job posting and your experience.

```bash
resume-engine cover --master resume.md --job posting.txt --output cover.md
resume-engine cover --master resume.md --job-url "https://example.com/jobs/123" --format pdf
```

### package

Generate a complete application package (tailored resume + cover letter) in one command. Optionally include a grounded validation report in the same output folder before you send anything.

```bash
resume-engine package --master resume.md --job posting.txt --outdir ./application/
resume-engine package --master resume.md --job posting.txt --outdir ./app/ --format pdf
resume-engine package --master resume.md --job posting.txt --outdir ./application/ --validate-report
```

### score

Instant resume quality score (0-100) across 5 dimensions: structure, readability, quantified achievements, keywords, and impact. No LLM required. Use `--json` for automation-friendly output.

```bash
resume-engine score master-resume.md
resume-engine score tailored.md --brief
resume-engine score master-resume.md --json
```

### cover-score

Instant cover letter quality score (0-100) across 5 dimensions: opening hook, company specificity, value proposition, length, and filler detection. No LLM required.

```bash
resume-engine cover-score cover-letter.md
resume-engine cover-score cover-letter.md --brief
```

### validate

Grounded trust check for tailored output. Compares a tailored resume and/or cover letter against your master resume plus the job posting, then flags likely unsupported claims, title drift, date drift, company drift, and suspicious rewrites.

```bash
resume-engine validate --master resume.md --job posting.txt --resume tailored.md
resume-engine validate --master resume.md --job posting.txt --cover-letter cover-letter.md
resume-engine validate --master resume.md --job posting.txt --resume tailored.md --cover-letter cover-letter.md --output validation-report.md
```

### optimize

LLM-powered resume improvement without targeting a specific job. Strengthens bullets, removes filler, flags missing metrics.

```bash
resume-engine optimize master-resume.md
resume-engine optimize master-resume.md --output stronger.md --model openai
resume-engine optimize master-resume.md --explain    # summary of changes
resume-engine optimize master-resume.md --diff       # section-level diff
```

### interview

Predict likely interview questions with STAR-method answer frameworks tailored to your real experience. Categories: Behavioral, Technical, Culture Fit, and Resume Deep-Dive.

```bash
resume-engine interview --master resume.md --job posting.txt
resume-engine interview --master resume.md --job-url "https://example.com/jobs/123" --count 15
resume-engine interview --master resume.md --job posting.txt --with-followups --output prep.md
```

### ats

Analyze ATS keyword match between your resume and a job posting. Shows which keywords you hit and which you miss.

```bash
resume-engine ats --resume resume.md --job posting.txt
resume-engine ats --resume resume.md --job-url "https://example.com/jobs/123" --top 20

# Before/after comparison with a tailored version
resume-engine ats --resume master.md --job posting.txt --tailored tailored.md
```

### diff

Section-aware comparison between your original and tailored resume. See exactly what the AI changed.

```bash
resume-engine diff master-resume.md tailored-resume.md
resume-engine diff master-resume.md tailored-resume.md --unified
```

### track

Local SQLite-backed application tracker. Log where you've applied, update statuses, and see your pipeline.

```bash
# Log a new application
resume-engine track add --company "Acme Corp" --role "Staff Engineer"
resume-engine track add --company "StartupX" --role "Backend Dev" --url "https://..."

# List applications
resume-engine track list
resume-engine track list --status interview
resume-engine track list --company acme

# Update status
resume-engine track update 1 --status interview
resume-engine track update 1 --notes "Phone screen scheduled for Friday"

# View details and pipeline stats
resume-engine track show 1
resume-engine track stats

# Export your tracker to JSON or CSV
resume-engine track export --format json --output applications.json
resume-engine track export --format csv --status interview --output interviews.csv

# Remove an entry
resume-engine track delete 3
```

Valid statuses: `applied`, `screening`, `interview`, `offer`, `rejected`, `withdrawn`.

### doctor

Check your local environment before tailoring, exporting PDFs, or switching providers. `doctor` understands which backend is configured as your default and highlights required versus optional setup gaps. Add `--strict` in scripts or CI to fail fast when required checks are broken.

```bash
resume-engine doctor
resume-engine doctor --strict
```

### config

Save defaults so you don't repeat flags on every command.

```bash
resume-engine config set model openai
resume-engine config set format pdf
resume-engine config get model
resume-engine config list
resume-engine config unset model
resume-engine config reset
```

### import

Convert raw resume text into a structured master resume in markdown.

```bash
resume-engine import --text linkedin-export.txt --output master-resume.md
resume-engine import --text raw-resume.txt --output master-resume.md --model openai

# From clipboard (macOS)
pbpaste | resume-engine import --stdin --output master-resume.md
```

**LinkedIn workflow:**
1. Go to your LinkedIn profile > "More" > "Save to PDF"
2. Convert: `pdftotext linkedin-profile.pdf linkedin-export.txt`
3. Import: `resume-engine import --text linkedin-export.txt --output master-resume.md`
4. Review and fill any gaps
5. Use as your master resume for all tailoring

### batch

Tailor your resume to multiple jobs in one command.

```bash
# From a directory of job postings
resume-engine batch --master resume.md --jobs-dir ./jobs/ --outdir ./applications/
resume-engine batch --master resume.md --jobs-dir ./jobs/ --outdir ./applications/ --with-cover --format pdf

# From a JSON manifest
resume-engine batch --master resume.md --manifest batch-manifest.json --outdir ./applications/
```

Output structure:

```
applications/
  acme-corp/
    resume.md
    cover-letter.md   (if --with-cover)
    resume.pdf        (if --format pdf)
  startup-x/
    resume.md
    ...
```

### templates

Manage resume layout styles.

```bash
resume-engine templates list
resume-engine templates show technical
```

Built-in templates:

| Slug | Best for |
|------|----------|
| `classic` | Most roles -- traditional chronological |
| `concise` | Experienced candidates -- tight single page |
| `technical` | Engineers -- skills-first, project emphasis |
| `executive` | Directors/VPs -- leadership and impact focus |

Drop custom `.md` files in `~/.resume-engine/templates/` to add your own.

### check

Verify that dependencies (pandoc, LaTeX, Ollama) are installed and working.

```bash
resume-engine check
```

## Master Resume Format

Your master resume is the superset of everything. Include all experience, skills, and projects. The engine selects and emphasizes what matters for each job.

```markdown
# Your Name

## Contact
- email: you@example.com
- location: City, State

## Summary
Your full professional summary...

## Experience
### Job Title -- Company (2020-2024)
- Achievement 1
- Achievement 2

## Skills
- Skill Category: skill1, skill2, skill3

## Education
### Degree -- University (Year)

## Projects
### Project Name
Description...
```

## PDF Output

Add `--format pdf` to any command that generates documents:

```bash
resume-engine tailor --master resume.md --job posting.txt --format pdf
resume-engine package --master resume.md --job posting.txt --outdir ./app/ --format pdf
```

Requires **pandoc** and a LaTeX engine:

```bash
# macOS
brew install pandoc basictex
sudo tlmgr install titlesec enumitem parskip

# Linux (Debian/Ubuntu)
sudo apt install pandoc texlive-latex-extra
```

## LLM Support

Uses local Ollama (qwen2.5:14b) by default -- free, no API key required.

```bash
# Local Ollama (default)
resume-engine tailor --master resume.md --job posting.txt

# OpenAI
OPENAI_API_KEY=sk-... resume-engine tailor --master resume.md --job posting.txt --model openai

# Anthropic
ANTHROPIC_API_KEY=sk-... resume-engine tailor --master resume.md --job posting.txt --model anthropic

# Save your default model
resume-engine config set model openai
```

## License

MIT

## Contributing

Contributions welcome. Please open an issue or PR.

```bash
git clone https://github.com/14-TR/resume-engine
cd resume-engine
pip install -e ".[dev]"
pytest tests/
```

## Releasing

Releases publish to PyPI automatically via GitHub Actions when a version tag is pushed:

```bash
git tag v0.3.1
git push origin v0.3.1
```

Requires **PyPI Trusted Publishing** configured in the `pypi` environment on the repo.
