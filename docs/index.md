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
| `score` | Score resume quality instantly, with optional JSON output |
| `cover-score` | Score cover letter quality instantly, with optional JSON output |
| `fit` | Estimate whether a role is worth applying to before tailoring |
| `interview` | Generate tailored interview prep, with optional JSON output |
| `validate` | Run grounded trust checks before sending anything |
| `doctor` | Diagnose local setup issues before you start |
| `ats` | Analyze keyword match score |
| `batch` | Tailor to multiple jobs at once |
| `import` | Convert raw resume text to master format |
| `templates list` | Browse built-in layout styles |
| `check` | Verify dependencies (Ollama, pandoc, API keys) |

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


## Automation-Friendly Workflows

Resume Engine is not just a document generator. It can also act like a quality gate in local scripts and CI. The key commands with JSON output are:

- `resume-engine doctor --json`
- `resume-engine score --json`
- `resume-engine cover-score --json`
- `resume-engine fit --json`
- `resume-engine interview --json`
- `resume-engine validate --json`

A practical pattern is to tailor first, then run `validate --json` and only continue if the result looks safe. That gives you a grounded trust check before you send a resume or cover letter anywhere.
