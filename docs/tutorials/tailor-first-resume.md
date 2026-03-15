# Tailor Your First Resume

This tutorial walks through a complete example using the sample files included in the repo.

## The Example Files

Resume Engine ships with a sample master resume and job posting in `examples/`:

- `examples/master-resume.md` -- Alex Rivera, senior software engineer
- `examples/job-posting.txt` -- Senior Python Engineer at Meridian Cloud

You can use these to try the tool before working with your own resume.

## Run the Tailoring

```bash
resume-engine tailor \
  --master examples/master-resume.md \
  --job examples/job-posting.txt \
  --output tailored-resume.md
```

## What Happens

Resume Engine sends your master resume and job posting to the LLM with a tailoring prompt. The model:

1. **Reads the job requirements** -- required skills, preferred experience, responsibilities
2. **Scans your master resume** -- everything you've done
3. **Selects and rewrites** -- pulls out the most relevant bullet points, reorders sections, adjusts the summary to match the role
4. **Returns tailored markdown** -- ready to review and submit

## Review the Output

Open `tailored-resume.md` and compare it to `examples/master-resume.md`. Notice:

- The **summary** now references specific technologies from the job posting
- **Bullet points** are reordered to lead with the most relevant accomplishments
- **Skills** section matches the keywords in the job description

## Iteration

Not happy with the result? Try:

- **Different model**: `--model openai` or `--model anthropic` for higher quality output
- **Interactive mode**: `--interactive` lets you fill in gaps before tailoring
- **Different template**: `--template technical` or `--template concise` for different layouts

```bash
resume-engine tailor \
  --master master-resume.md \
  --job posting.txt \
  --output tailored.md \
  --model openai \
  --template technical
```

## Check the ATS Score

Always run ATS analysis to verify keyword coverage:

```bash
resume-engine ats \
  --resume master-resume.md \
  --job examples/job-posting.txt \
  --tailored tailored-resume.md
```

Aim for **70%+** match score on tailored resumes. If you're below that, consider adding the missing keywords manually or re-running with a cloud model.

## Generate the Full Package

When you're happy with the tailored resume, generate a cover letter too:

```bash
resume-engine package \
  --master master-resume.md \
  --job posting.txt \
  --outdir ./application/ \
  --format pdf
```

This outputs:
```
application/
  resume.md
  resume.pdf
  cover-letter.md
  cover-letter.pdf
```
