# Command Reference

## `tailor`

Tailor a resume to a specific job posting.

```bash
resume-engine tailor [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume (markdown) |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--output` | `tailored-resume.md` | Output file path |
| `--model` | `ollama` | LLM backend: `ollama`, `openai`, `anthropic` |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--interactive` | off | Ask gap-filling questions before tailoring |
| `--template` | — | Resume style (see `templates list`) |

Either `--job` or `--job-url` is required.

**Examples:**

```bash
# Basic tailoring
resume-engine tailor --master resume.md --job posting.txt

# From URL, PDF output, with template
resume-engine tailor \
  --master resume.md \
  --job-url "https://careers.example.com/123" \
  --output tailored.md \
  --format pdf \
  --template technical \
  --model openai
```

---

## `cover`

Generate a cover letter for a job posting.

```bash
resume-engine cover [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume (markdown) |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--output` | `cover-letter.md` | Output file path |
| `--model` | `ollama` | LLM backend |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--interactive` | off | Ask gap-filling questions first |
| `--template` | — | Cover letter style |

**Example:**

```bash
resume-engine cover \
  --master resume.md \
  --job posting.txt \
  --output cover-letter.md \
  --model anthropic
```

---

## `package`

Generate a full application package (tailored resume + cover letter).

```bash
resume-engine package [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume (markdown) |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--outdir` | `./application` | Output directory |
| `--model` | `ollama` | LLM backend |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--template` | — | Style for both documents |

Output structure:
```
application/
  resume.md
  cover-letter.md
  resume.pdf       (if --format pdf)
  cover-letter.pdf (if --format pdf)
```

---

## `ats`

Analyze ATS keyword match score.

```bash
resume-engine ats [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--resume` | (required) | Path to resume to analyze |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--tailored` | — | Tailored resume for before/after comparison |
| `--top` | `30` | Number of keywords to extract |

**Example:**

```bash
# Simple score check
resume-engine ats --resume resume.md --job posting.txt

# Before/after comparison
resume-engine ats \
  --resume master-resume.md \
  --job posting.txt \
  --tailored tailored-resume.md \
  --top 40
```

---

## `batch`

Tailor resume to multiple jobs at once.

```bash
resume-engine batch [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume |
| `--jobs-dir` | — | Directory of `.txt`/`.md` job postings |
| `--manifest` | — | JSON manifest file |
| `--outdir` | `./batch-output` | Root output directory |
| `--model` | `ollama` | LLM backend |
| `--format` | `md` | Output format |
| `--template` | — | Resume style |
| `--with-cover` | off | Also generate cover letters |

Either `--jobs-dir` or `--manifest` is required (not both).

**Manifest format:**

```json
[
  {"name": "company-a", "job": "jobs/company-a.txt"},
  {"name": "company-b", "job_url": "https://company-b.com/jobs/42"}
]
```

---

## `import`

Convert raw resume text to a structured master resume.

```bash
resume-engine import [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--text` | — | Path to raw resume text file |
| `--output` | `master-resume.md` | Output file path |
| `--model` | `ollama` | LLM backend |
| `--stdin` | off | Read raw text from stdin |

Either `--text` or `--stdin` is required.

**Examples:**

```bash
# From a file
resume-engine import --text raw-resume.txt --output master-resume.md

# From clipboard (macOS)
pbpaste | resume-engine import --stdin --output master-resume.md

# Better quality with cloud model
resume-engine import --text raw.txt --output master.md --model openai
```

---

---

## `check`

Verify that all required and optional dependencies are installed and reachable.

```bash
resume-engine check
```

No options -- just run it. Resume Engine checks:

| Dependency | Category | Required? |
|---|---|---|
| Ollama | LLM Backend | No (default backend, but optional if using cloud) |
| pandoc | PDF Output | No |
| pdflatex | PDF Output | No |
| OPENAI_API_KEY | LLM Backend | No |
| ANTHROPIC_API_KEY | LLM Backend | No |

**Example output:**

```
 resume-engine -- system check

  Ollama                   OK    running at http://localhost:11434 -- 2 model(s) pulled
  pandoc                   OK    pandoc 3.1.2
  pdflatex                WARN   pdflatex not found in PATH
  OpenAI API key          WARN   OPENAI_API_KEY not set
  Anthropic API key       WARN   ANTHROPIC_API_KEY not set

All required checks passed. resume-engine is ready to use.
```

Run this after installing to confirm your setup is working before processing your first resume.

## `templates list`

List all available resume templates.

```bash
resume-engine templates list
```

---

## `templates show`

Show the layout instructions for a specific template.

```bash
resume-engine templates show <name>
```

**Example:**

```bash
resume-engine templates show technical
```
