# Examples

Sample files for testing and demonstrating resume-engine commands.

## Files

| File | Description |
|---|---|
| `master-resume.md` | Full master resume for a fictional software engineer (Alex Rivera) |
| `raw-resume.txt` | Unstructured plain-text resume for testing the `import` command |
| `job-posting.txt` | Senior Python Engineer role (backend/platform) |
| `job-posting-frontend.txt` | Frontend Engineer role (design systems) |
| `batch-manifest.json` | Manifest for batch mode with both job postings |

## Quick Start

Run all examples from the project root (`resume-engine/`).

### Tailor a resume

```bash
resume-engine tailor \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --output tailored-resume.md
```

### Generate a cover letter

```bash
resume-engine cover \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --output cover-letter.md
```

### Full application package (resume + cover letter)

```bash
resume-engine package \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --outdir ./application
```

### ATS keyword analysis

```bash
# Score the master resume against a job posting
resume-engine ats \
  --resume examples/master-resume.md \
  --job examples/job-posting.txt

# Before/after comparison (tailor first, then compare)
resume-engine ats \
  --resume examples/master-resume.md \
  --job examples/job-posting.txt \
  --tailored tailored-resume.md
```

### Import a raw resume

Convert unstructured text into a structured master resume:

```bash
resume-engine import \
  --text examples/raw-resume.txt \
  --output imported-resume.md
```

Or pipe from stdin:

```bash
cat examples/raw-resume.txt | resume-engine import --stdin --output imported-resume.md
```

### Batch mode

Tailor to multiple jobs at once:

```bash
# Using the manifest file
resume-engine batch \
  --master examples/master-resume.md \
  --manifest examples/batch-manifest.json \
  --outdir ./batch-output

# Using a directory of job postings
resume-engine batch \
  --master examples/master-resume.md \
  --jobs-dir examples/ \
  --outdir ./batch-output

# With cover letters and PDF output
resume-engine batch \
  --master examples/master-resume.md \
  --manifest examples/batch-manifest.json \
  --outdir ./batch-output \
  --with-cover \
  --format pdf
```

### Templates

```bash
# List available templates
resume-engine templates list

# Preview a template
resume-engine templates show technical

# Tailor with a specific template
resume-engine tailor \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --template technical \
  --output tailored-resume.md
```

### Interactive mode

Add `--interactive` to `tailor` or `cover` to answer gap-filling questions before generation:

```bash
resume-engine tailor \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --interactive \
  --output tailored-resume.md
```

## LLM Options

All commands default to local Ollama. Add `--model openai` or `--model anthropic` to use cloud LLMs:

```bash
resume-engine tailor \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --model openai \
  --output tailored-resume.md
```
