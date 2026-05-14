# Command Reference


## Shared review dashboard schema

`tailor`, `cover`, `package`, `batch`, `ats`, `diff`, `optimize`, `doctor`, `score`, `cover-score`, `fit`, `interview`, and `validate` can emit machine-readable JSON for dashboards, scripts, and CI gates. Review-oriented commands share the same top-level envelope:

```json
{
  "schema": "resume-engine.dashboard/v1",
  "command": "fit",
  "generated_at": "2026-04-18T10:00:00+00:00",
  "inputs": {},
  "summary": {},
  "artifacts": {},
  "data": {}
}
```

Use `summary` for dashboard cards, `artifacts` for linked files, and `data` for the command-specific body.

`ats`, `doctor`, and `score` also support `--json`, but they return raw command-specific payloads rather than the shared dashboard envelope.

---

## `tailor`

Tailor a resume to a specific job posting. Use `--json` to emit the shared `resume-engine.dashboard/v1` review schema while still writing the tailored markdown file.

```bash
resume-engine tailor [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume (markdown) |
| `--linkedin-url` | — | LinkedIn profile URL to import as master resume |
| `--linkedin-export` | — | LinkedIn data export ZIP or directory |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--output` | `tailored-resume.md` | Output file path |
| `--model` | `ollama` | LLM backend: `ollama`, `openai`, `anthropic` |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--interactive` | off | Ask gap-filling questions before tailoring |
| `--template` | — | Resume style (see `templates list`) |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

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
| `--linkedin-url` | — | LinkedIn profile URL to import as master resume |
| `--linkedin-export` | — | LinkedIn data export ZIP or directory |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--output` | `cover-letter.md` | Output file path |
| `--model` | `ollama` | LLM backend |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--interactive` | off | Ask gap-filling questions first |
| `--template` | — | Cover letter style |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

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

Generate a full application package (tailored resume + cover letter + fit summary). The optional manifest uses the shared `resume-engine.dashboard/v1` schema.

```bash
resume-engine package [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume (markdown) |
| `--linkedin-url` | — | LinkedIn profile URL to import as master resume |
| `--linkedin-export` | — | LinkedIn data export ZIP or directory |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--outdir` | `./application` | Output directory |
| `--model` | `ollama` | LLM backend |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--template` | — | Style for both documents |
| `--validate-report` | off | Generate grounded validation markdown in the package |
| `--no-validate-report` | on | Skip grounded validation report generation |
| `--json` | off | Write a `resume-engine.dashboard/v1` manifest JSON |
| `--no-json` | on | Skip manifest JSON generation |

Output structure:
```
application/
  resume.md
  cover-letter.md
  fit-summary.md
  validation-report.md (if --validate-report)
  package-summary.json (if --json)
  resume.pdf       (if --format pdf)
  cover-letter.pdf (if --format pdf)
  fit-summary.pdf  (if --format pdf)
```

When `--format pdf --json` are used together, `package-summary.json` includes
portable artifact references for the generated PDFs in addition to the markdown
outputs.

When `--validate-report --json` is enabled, `package-summary.json` also records
`summary.validation_status`, `summary.validation_risk_level`,
`summary.validation_high_severity_issue_count`, and
`summary.validation_lowest_trust_score`. Packages with high-severity validation
findings or very low trust scores are marked `needs_review`, and the CLI prints a
review warning rather than a ready-to-send completion line.

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
| `--json` | off | Emit raw ATS analysis JSON to stdout |

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
| `--json` | off | Emit `resume-engine.dashboard/v1` batch results to stdout |

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

## `init`

Create a starter master resume through the guided resume builder.

```bash
resume-engine init [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--output` | `master-resume.md` | Output file path |

---

## `score`

Score resume quality instantly without an LLM.

```bash
resume-engine score [OPTIONS] RESUME
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `RESUME` | (required) | Resume markdown file to score |
| `--brief` | off | Print a compact score summary |
| `--json` | off | Emit raw machine-readable score results |

---

## `cover-score`

Score cover letter quality instantly without an LLM.

```bash
resume-engine cover-score [OPTIONS] COVER_LETTER
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `COVER_LETTER` | (required) | Cover letter file to score |
| `--brief` | off | Print a compact score summary |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

---

## `fit`

Estimate whether a job is worth applying to before tailoring.

```bash
resume-engine fit [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume |
| `--linkedin-url` | — | LinkedIn profile URL to import as master resume |
| `--linkedin-export` | — | LinkedIn data export ZIP or directory |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--model` | `ollama` | LLM backend |
| `--brief` | off | Print a compact fit summary |
| `--output` | — | Optional markdown output file |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

Either `--job` or `--job-url` is required.

---

## `interview`

Generate tailored interview prep from a resume and job posting.

```bash
resume-engine interview [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | (required) | Path to master resume |
| `--linkedin-url` | — | LinkedIn profile URL to import as master resume |
| `--linkedin-export` | — | LinkedIn data export ZIP or directory |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--count` | `10` | Number of questions to generate |
| `--model` | `ollama` | LLM backend |
| `--with-followups` | off | Include follow-up questions |
| `--output` | — | Optional markdown output file |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

Either `--job` or `--job-url` is required.

---

## `validate`

Run grounded trust checks before sending a tailored resume or cover letter.

```bash
resume-engine validate [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--master` | — | Path to master resume |
| `--linkedin-url` | — | LinkedIn profile URL to import as master resume |
| `--linkedin-export` | — | LinkedIn data export ZIP or directory |
| `--job` | — | Path to job posting text file |
| `--job-url` | — | URL of job posting to scrape |
| `--resume` | — | Tailored resume to validate |
| `--cover-letter` | — | Cover letter to validate |
| `--output` | — | Optional markdown report path |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

Use exactly one resume source: `--master`, `--linkedin-url`, or `--linkedin-export`.
Either `--resume` or `--cover-letter` is required.

---

## `optimize`

Improve a resume without targeting a specific job posting.

```bash
resume-engine optimize [OPTIONS] RESUME
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `RESUME` | (required) | Resume markdown file to optimize |
| `--output` | `optimized-resume.md` | Output file path |
| `--model` | `ollama` | LLM backend |
| `--format` | `md` | Output format: `md`, `pdf` |
| `--explain` | off | Print a summary of changes |
| `--diff` | off | Print a section-level diff |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

---

## `diff`

Compare original and tailored resumes section by section.

```bash
resume-engine diff [OPTIONS] ORIGINAL TAILORED
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `ORIGINAL` | (required) | Original resume markdown file |
| `TAILORED` | (required) | Tailored resume markdown file |
| `--unified` | off | Include unified text diff output |
| `--sections` | off | Print section-level changes |
| `--json` | off | Emit `resume-engine.dashboard/v1` JSON to stdout |

---

## `doctor`

Diagnose local setup issues before tailoring, PDF export, or provider changes.

```bash
resume-engine doctor [OPTIONS]
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--strict` | off | Exit non-zero when required checks fail |
| `--json` | off | Emit machine-readable setup results |

---

## `config`

Save and inspect CLI defaults such as model, format, output directory, and template.

```bash
resume-engine config COMMAND [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `list` | Show saved defaults |
| `get KEY` | Show one default value |
| `set KEY VALUE` | Save a default value |
| `unset KEY` | Remove one saved default |
| `reset --yes` | Clear all saved defaults |

---

## `track`

Manage the local SQLite-backed application tracker.

```bash
resume-engine track COMMAND [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `add` | Log a new application |
| `list` | List applications, optionally filtered |
| `show APP_ID` | Show one application |
| `update APP_ID` | Update status, notes, or URL |
| `stats` | Summarize the pipeline by status |
| `export` | Export applications to JSON or CSV |
| `delete APP_ID --yes` | Remove an application |

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

## `templates`

Manage resume layout styles.

```bash
resume-engine templates COMMAND [OPTIONS]
```

**Subcommands:**

| Command | Description |
|---------|-------------|
| `list` | List available templates |
| `show NAME` | Show layout instructions for a template |

---

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
