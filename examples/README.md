# Examples

Sample files for testing and demonstrating resume-engine.

## Files

| File | Description |
|---|---|
| `master-resume.md` | Full master resume for a fictional software engineer (Alex Rivera) |
| `job-posting.txt` | Sample job posting for a Senior Python Engineer role |

## Usage

**Tailor the resume to the job posting:**
```bash
resume-engine tailor \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --output tailored-resume.md
```

**Generate a cover letter:**
```bash
resume-engine cover \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --output cover-letter.md
```

**Generate a full application package:**
```bash
resume-engine package \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --outdir ./application
```

Add `--model openai` or `--model anthropic` to use a cloud LLM instead of the default local Ollama.
