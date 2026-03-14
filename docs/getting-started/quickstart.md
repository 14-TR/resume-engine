# Quick Start

This guide gets you from zero to a tailored resume in under 5 minutes.

## Step 1: Install

```bash
pip install resume-engine
```

## Step 2: Create your master resume

Your master resume is the **complete** version of your career history -- everything you've ever done. Resume Engine will select and emphasize the most relevant parts for each job.

Create `master-resume.md`:

```markdown
# Your Name
your@email.com | (555) 000-0000 | City, State

## Summary
A concise summary of your background and what you bring to a role.

## Skills
**Languages:** Python, JavaScript, SQL
**Tools:** Docker, Kubernetes, Git
**Cloud:** AWS, GCP

## Experience

### Senior Software Engineer -- Acme Corp (2022 - Present)
- Achievement 1 with measurable result
- Achievement 2 with measurable result

### Software Engineer -- Startup Inc (2020 - 2022)
- Achievement 1
- Achievement 2

## Education
**B.S. Computer Science** -- State University, 2020
```

!!! tip
    Already have a resume? Use `resume-engine import` to convert it automatically.
    See [Import from LinkedIn](../tutorials/import-from-linkedin.md).

## Step 3: Save the job posting

Copy the job description text and save it as `job-posting.txt`.

You can also use a URL and let Resume Engine scrape it:

```bash
resume-engine tailor --master master-resume.md --job-url "https://example.com/jobs/123"
```

## Step 4: Tailor your resume

```bash
resume-engine tailor \
  --master master-resume.md \
  --job job-posting.txt \
  --output tailored-resume.md
```

Resume Engine will:

1. Parse your master resume and job posting
2. Identify relevant skills, keywords, and requirements
3. Reorder and emphasize sections for that specific role
4. Write a tailored resume to `tailored-resume.md`

## Step 5: Check your ATS score

ATS (Applicant Tracking System) software scans resumes for keywords before a human ever sees them. Check your match score:

```bash
resume-engine ats \
  --resume master-resume.md \
  --job job-posting.txt \
  --tailored tailored-resume.md
```

Output example:

```
Original resume match score:  47%  (14/30 keywords)
Tailored resume match score:  73%  (22/30 keywords)  +26%

Newly matched by tailoring:
  distributed systems  kafka  aws lambda  postmortem  async-first

Still missing:
  billing  usage metering  tenant provisioning
```

## What's next?

- Generate a cover letter: [cover command](../reference/commands.md#cover)
- Apply to many jobs at once: [Batch Mode](../tutorials/batch-mode.md)
- Different resume styles: [Templates](../reference/templates.md)
- PDF output: [PDF Output](../reference/pdf-output.md)
