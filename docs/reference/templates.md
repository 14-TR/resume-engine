# Templates

Resume Engine includes four built-in layout styles. Use `--template` to apply one.

## Built-in Templates

```bash
resume-engine templates list
```

| Slug | Name | Best for |
|------|------|---------|
| `classic` | Classic | Most roles -- traditional chronological format |
| `concise` | Concise | Experienced candidates -- tight single-page layout |
| `technical` | Technical | Engineers -- skills-first, project emphasis |
| `executive` | Executive | Directors/VPs -- leadership and business impact focus |

### Classic

Standard chronological format. Experience first, then skills, then education. Works for almost any role.

```bash
resume-engine tailor --master resume.md --job posting.txt --template classic
```

### Concise

Strips verbose language, cuts to one page if possible. Good for senior candidates with a lot of experience to distill.

```bash
resume-engine tailor --master resume.md --job posting.txt --template concise
```

### Technical

Skills section first, then experience with detailed technical bullet points, then projects. Best for software engineering, data science, and DevOps roles.

```bash
resume-engine tailor --master resume.md --job posting.txt --template technical
```

### Executive

Opens with impact and scope -- team size, budget, business outcomes. Experience bullets lead with business results over technical details. Best for director and VP roles.

```bash
resume-engine tailor --master resume.md --job posting.txt --template executive
```

---

## Custom Templates

Drop a `.md` file into `~/.resume-engine/templates/` to add your own template.

Use front matter for metadata:

```markdown
---
name: My Custom Style
description: My preferred resume layout
---

LAYOUT INSTRUCTIONS:
- Lead with a strong summary paragraph
- List all skills in a two-column table
- Use past tense for all bullet points
- Keep bullet points to one line each
- End with a one-line "open to" statement
```

Your template will appear in `resume-engine templates list` and can be used with `--template my-custom-style` (slug is the filename without `.md`, lowercased with dashes).

---

## Show Template Instructions

See the exact instructions a template passes to the LLM:

```bash
resume-engine templates show technical
```
