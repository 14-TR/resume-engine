# resume-engine

**[Documentation](https://14-tr.github.io/resume-engine)** | [PyPI](https://pypi.org/project/resume-engine/) | [GitHub](https://github.com/14-TR/resume-engine)

CLI tool that takes a master resume + job posting → tailored resume.

```bash
pip install resume-engine
```

## Usage

```bash
# Tailor resume to a job posting
resume-engine tailor --master resume.md --job posting.txt --output tailored.md

# From a URL (scrapes job requirements)
resume-engine tailor --master resume.md --job-url "https://careers.example.com/12345" --output tailored.md

# Generate cover letter
resume-engine cover --master resume.md --job posting.txt --output cover.md

# Full application package (resume + cover letter)
resume-engine package --master resume.md --job posting.txt --outdir ./application/
```

## How it works

1. **Parse** your master resume (markdown)
2. **Analyze** the job posting for requirements, keywords, and priorities
3. **Tailor** the resume: reorder sections, emphasize relevant experience, match keywords
4. **Output** as markdown or PDF

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
### Job Title — Company (2020-2024)
- Achievement 1
- Achievement 2
...

## Skills
- Skill Category: skill1, skill2, skill3
...

## Education
### Degree — University (Year)
...

## Projects
### Project Name
Description...
```


## Batch Mode

Tailor your resume to multiple jobs in one command.

### From a directory

```bash
# Put all your job postings (.txt or .md) in a folder, then:
resume-engine batch --master resume.md --jobs-dir ./jobs/ --outdir ./applications/

# With cover letters too
resume-engine batch --master resume.md --jobs-dir ./jobs/ --outdir ./applications/ --with-cover

# With PDF output
resume-engine batch --master resume.md --jobs-dir ./jobs/ --outdir ./applications/ --format pdf --with-cover
```

Each job gets its own subfolder:

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

### From a JSON manifest

For more control, use a manifest file:

```json
[
  {"name": "acme-corp",   "job": "jobs/acme.txt"},
  {"name": "startup-x",   "job_url": "https://careers.startup.io/123"},
  {"name": "big-tech-co", "job": "jobs/bigtech.txt"}
]
```

```bash
resume-engine batch --master resume.md --manifest batch-manifest.json --outdir ./applications/
```

See `examples/batch-manifest.json` for a working example.


## PDF Output

Add `--format pdf` to any command to generate a PDF alongside the markdown:

```bash
resume-engine tailor --master resume.md --job posting.txt --output tailored.md --format pdf
resume-engine cover --master resume.md --job posting.txt --format pdf
resume-engine package --master resume.md --job posting.txt --outdir ./application/ --format pdf
```

PDF conversion requires **pandoc** and a LaTeX engine:

```bash
# macOS
brew install pandoc basictex
sudo tlmgr install titlesec enumitem parskip

# Linux (Debian/Ubuntu)
sudo apt install pandoc texlive-latex-extra
```


## Templates

Choose from four built-in layout styles with `--template`:

```bash
# List available templates
resume-engine templates list

# Show a template's layout instructions
resume-engine templates show technical

# Tailor using the technical template (skills-first layout)
resume-engine tailor --master resume.md --job posting.txt --template technical

# Use executive style for the full application package
resume-engine package --master resume.md --job posting.txt --template executive
```

| Slug | Name | Best for |
|------|------|----------|
| `classic` | Classic | Most roles - traditional chronological format |
| `concise` | Concise | Experienced candidates - tight single-page layout |
| `technical` | Technical | Engineers - skills-first, project emphasis |
| `executive` | Executive | Directors/VPs - leadership and business impact focus |

### Custom Templates

Drop any `.md` file in `~/.resume-engine/templates/` to add your own. Use front matter for metadata:

```markdown
---
name: My Style
description: My custom layout
---

LAYOUT INSTRUCTIONS:
- ...your instructions...
```

## LLM Support

Uses local Ollama (qwen2.5:14b) by default. Falls back to OpenAI or Anthropic if configured.

```bash
# Use local Ollama (default, free)
resume-engine tailor --master resume.md --job posting.txt

# Use OpenAI
OPENAI_API_KEY=sk-... resume-engine tailor --master resume.md --job posting.txt --model openai

# Use Anthropic
ANTHROPIC_API_KEY=sk-... resume-engine tailor --master resume.md --job posting.txt --model anthropic
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

Releases are published to PyPI automatically via GitHub Actions when a version tag is pushed:

```bash
git tag v0.2.0
git push origin v0.2.0
```

Requires **PyPI Trusted Publishing** configured in the `pypi` environment on the repo (no API token needed).
