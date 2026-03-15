# Import from LinkedIn (or Any Source)

Don't have a master resume in markdown yet? The `import` command converts raw resume text from any source into a structured master resume ready for tailoring.

## Supported Sources

- LinkedIn PDF export
- Old Word/PDF resumes (converted to text)
- Copy-pasted LinkedIn profile text
- Any plain-text resume format

## LinkedIn Workflow

### Option 1: Save to PDF, convert to text

1. Go to your LinkedIn profile
2. Click **More** -> **Save to PDF**
3. Convert the PDF to text:

```bash
# macOS (install with: brew install poppler)
pdftotext linkedin-profile.pdf linkedin-export.txt

# or on Linux
pdftotext linkedin-profile.pdf linkedin-export.txt
```

4. Import it:

```bash
resume-engine import --text linkedin-export.txt --output master-resume.md
```

### Option 2: Copy-paste from browser

1. Open your LinkedIn profile
2. Select all text (Cmd+A or Ctrl+A), copy it
3. Pipe from clipboard:

=== "macOS"

    ```bash
    pbpaste | resume-engine import --stdin --output master-resume.md
    ```

=== "Linux (xclip)"

    ```bash
    xclip -selection clipboard -o | resume-engine import --stdin --output master-resume.md
    ```

=== "Windows (PowerShell)"

    ```powershell
    Get-Clipboard | resume-engine import --stdin --output master-resume.md
    ```

## Using a Cloud Model for Better Results

LinkedIn exports are often messy. A cloud model handles the formatting better:

```bash
resume-engine import \
  --text linkedin-export.txt \
  --output master-resume.md \
  --model openai
```

## What the Import Does

The LLM takes your raw resume text (messy formatting, LinkedIn-style sections, etc.) and outputs clean, structured markdown:

```markdown
# Your Name
email | phone | location

## Summary
...

## Experience
### Job Title -- Company (Year - Year)
- Achievement...

## Skills
...

## Education
...
```

## After Importing

Review the output carefully:

- Fill in any gaps the LLM may have missed
- Expand bullet points with metrics where you remember them
- Add projects, certifications, or other sections that might have been lost

Once your master resume is solid, use it for all future tailoring:

```bash
resume-engine tailor --master master-resume.md --job posting.txt --output tailored.md
```

!!! tip
    Your master resume should be the **complete** version of your career -- more detail is better. Resume Engine trims and focuses it for each specific job.
