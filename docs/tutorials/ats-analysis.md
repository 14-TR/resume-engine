# ATS Score Analysis

ATS (Applicant Tracking System) software parses resumes before a recruiter ever reads them. A mismatch between the job posting keywords and your resume can mean automatic rejection.

Resume Engine's `ats` command shows you exactly where you stand -- and how much tailoring improved your score.

## Basic Analysis

```bash
resume-engine ats \
  --resume resume.md \
  --job job-posting.txt
```

Output:

```
Original resume match score:  47%  (14/30 keywords)

Matched keywords:
  python  fastapi  aws  postgresql  distributed systems  ci/cd  docker
  api  rest  data pipelines  postgres  infrastructure  backend  tests

Missing keywords:
  kafka  billing  metering  tenant  sqs  async  rfc  postmortem
  usage  event streaming  lambda  airflow  workflow  cost optimization
  documentation
```

## Before/After Comparison

Pass `--tailored` to compare your original vs. tailored resume:

```bash
resume-engine ats \
  --resume master-resume.md \
  --job job-posting.txt \
  --tailored tailored-resume.md
```

Output:

```
Original resume match score:  47%  (14/30 keywords)
Tailored resume match score:  73%  (22/30 keywords)  +26%

Newly matched by tailoring:
  kafka  async  postmortem  event streaming  lambda  cost optimization
  documentation  workflow

Still missing:
  billing  metering  tenant  sqs  usage
```

## Understanding the Score

The score is the percentage of extracted keywords from the job posting that appear in your resume. Resume Engine extracts:

- Single important words (technologies, skills, methodologies)
- Two-word phrases that appear together (e.g. "distributed systems", "data pipelines")
- Capitalized terms get a frequency boost (proper nouns, product names)

**Score thresholds:**

| Score | Meaning |
|-------|---------|
| 70%+ | Strong match -- proceed to apply |
| 45-70% | Moderate match -- improve before applying |
| Below 45% | Poor match -- heavy tailoring needed |

## Adjusting Keyword Count

By default, Resume Engine analyzes the top 30 keywords from the job posting. Increase for more thorough analysis:

```bash
resume-engine ats \
  --resume resume.md \
  --job posting.txt \
  --top 50
```

## Workflow Tip

Run ATS analysis at every step of your job search:

1. **Before tailoring** -- baseline score
2. **After tailoring** -- verify improvement
3. **After manual edits** -- confirm score held

```bash
# Baseline
resume-engine ats --resume master.md --job posting.txt

# Tailor
resume-engine tailor --master master.md --job posting.txt --output tailored.md

# Verify improvement
resume-engine ats --resume master.md --job posting.txt --tailored tailored.md
```

!!! note
    ATS scoring is keyword-based, not semantic. "Python developer" and "Python engineer" might count separately. The LLM tailoring naturally picks up on exact phrasing from the job posting.
