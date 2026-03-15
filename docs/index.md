# Resume Engine

> AI-powered resume tailoring CLI. One command, perfect resume.

```bash
pip install resume-engine
resume-engine tailor --master resume.md --job posting.txt --output tailored.md
```

Resume Engine takes your master resume and a job posting, and produces a tailored resume optimized for that specific role -- matching keywords, reordering sections, and highlighting the most relevant experience.

## Why Resume Engine?

- **Local-first** -- uses Ollama by default, no API key required
- **Fast** -- single command from job posting to tailored resume
- **ATS-aware** -- keyword analysis shows match score before and after tailoring
- **Batch-ready** -- apply to multiple jobs with one command
- **Open source** -- MIT license, runs anywhere Python runs

## Core Commands

| Command | What it does |
|---------|--------------|
| `tailor` | Tailor resume to a specific job |
| `cover` | Generate a cover letter |
| `package` | Full application (resume + cover letter) |
| `ats` | Analyze keyword match score |
| `batch` | Tailor to multiple jobs at once |
| `import` | Convert raw resume text to master format |
| `templates list` | Browse built-in layout styles |

## Quick Example

```bash
# 1. Install
pip install resume-engine

# 2. Import your existing resume (or write master-resume.md from scratch)
resume-engine import --text my-old-resume.txt --output master-resume.md

# 3. Check your ATS match before tailoring
resume-engine ats --resume master-resume.md --job job-posting.txt

# 4. Tailor it
resume-engine tailor --master master-resume.md --job job-posting.txt --output tailored.md

# 5. Check ATS score after
resume-engine ats --resume master-resume.md --job job-posting.txt --tailored tailored.md
```

## Get Started

- **New here?** Follow the [Quick Start](getting-started/quickstart.md) guide.
- **Have a resume to import?** See [Import from LinkedIn](tutorials/import-from-linkedin.md).
- **Applying to many jobs?** Jump straight to [Batch Mode](tutorials/batch-mode.md).
