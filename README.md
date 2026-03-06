# resume-engine

CLI tool that takes a master resume + job posting → tailored resume.

```bash
pip install resume-engine
```

## Usage

```bash
# Tailor resume to a job posting
resume-engine tailor --master resume.md --job posting.txt --output tailored.md

# From a URL (scrapes job requirements)
resume-engine tailor --master resume.md --job-url "https://careers.example.com/12345" --output tailored.md

# Generate cover letter
resume-engine cover --master resume.md --job posting.txt --output cover.md

# Full application package (resume + cover letter)
resume-engine package --master resume.md --job posting.txt --outdir ./application/
```

## How it works

1. **Parse** your master resume (markdown)
2. **Analyze** the job posting for requirements, keywords, and priorities
3. **Tailor** the resume: reorder sections, emphasize relevant experience, match keywords
4. **Output** as markdown or PDF

## Master Resume Format

Your master resume is the superset of everything. Include all experience, skills, and projects. The engine selects and emphasizes what matters for each job.

```markdown
# Your Name

## Contact
- email: you@example.com
- location: City, State

## Summary
Your full professional summary...

## Experience
### Job Title — Company (2020-2024)
- Achievement 1
- Achievement 2
...

## Skills
- Skill Category: skill1, skill2, skill3
...

## Education
### Degree — University (Year)
...

## Projects
### Project Name
Description...
```

## LLM Support

Uses local Ollama (qwen2.5:14b) by default. Falls back to OpenAI or Anthropic if configured.

```bash
# Use local Ollama (default, free)
resume-engine tailor --master resume.md --job posting.txt

# Use OpenAI
OPENAI_API_KEY=sk-... resume-engine tailor --master resume.md --job posting.txt --model openai

# Use Anthropic
ANTHROPIC_API_KEY=sk-... resume-engine tailor --master resume.md --job posting.txt --model anthropic
```

## License

MIT
