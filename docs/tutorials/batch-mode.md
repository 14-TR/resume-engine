# Batch Mode

Apply to multiple jobs in one command. Resume Engine generates a tailored resume (and optional cover letter) for each job, organized in its own output folder.

## From a Directory of Job Postings

Save each job posting as a `.txt` or `.md` file in a folder:

```
jobs/
  google-swe.txt
  stripe-backend.txt
  anthropic-research.txt
```

Run batch:

```bash
resume-engine batch \
  --master master-resume.md \
  --jobs-dir ./jobs/ \
  --outdir ./applications/
```

Output:

```
applications/
  google-swe/
    resume.md
  stripe-backend/
    resume.md
  anthropic-research/
    resume.md
```

## With Cover Letters

```bash
resume-engine batch \
  --master master-resume.md \
  --jobs-dir ./jobs/ \
  --outdir ./applications/ \
  --with-cover
```

Output:

```
applications/
  google-swe/
    resume.md
    cover-letter.md
  ...
```

## With PDF Output

```bash
resume-engine batch \
  --master master-resume.md \
  --jobs-dir ./jobs/ \
  --outdir ./applications/ \
  --format pdf \
  --with-cover
```

Each folder will contain `.md` and `.pdf` versions of both documents.

## Using a Manifest File

For finer control (custom job names, URLs mixed with files), use a JSON manifest:

```json
[
  {
    "name": "google-swe",
    "job": "jobs/google.txt"
  },
  {
    "name": "stripe-backend",
    "job_url": "https://stripe.com/jobs/listing/12345"
  },
  {
    "name": "anthropic-research",
    "job": "jobs/anthropic.txt"
  }
]
```

```bash
resume-engine batch \
  --master master-resume.md \
  --manifest batch-manifest.json \
  --outdir ./applications/
```

See `examples/batch-manifest.json` for a working example.

## Choosing a Model

For batch runs, Ollama (default) keeps it free. Use `--model openai` for higher quality at scale:

```bash
resume-engine batch \
  --master master-resume.md \
  --jobs-dir ./jobs/ \
  --outdir ./applications/ \
  --model openai
```

!!! warning
    Cloud models charge per-token. A batch of 20 jobs with OpenAI will use roughly 20 * ~3,000 tokens = ~60k tokens output. Check your usage.

## Summary Output

After the batch completes, Resume Engine prints a summary table:

```
Job                  Status    Duration
google-swe           OK        4.2s
stripe-backend       OK        3.8s
anthropic-research   FAILED    -

2/3 succeeded. Output: ./applications/
```

Failed jobs are skipped with an error message. Re-run with just that job file to debug.
