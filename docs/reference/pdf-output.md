# PDF Output

Add `--format pdf` to any command to generate a PDF alongside the markdown.

## Requirements

PDF conversion requires **pandoc** and a LaTeX engine:

=== "macOS"

    ```bash
    brew install pandoc basictex
    sudo tlmgr install titlesec enumitem parskip
    ```

=== "Linux (Debian/Ubuntu)"

    ```bash
    sudo apt install pandoc texlive-latex-extra
    ```

Verify the install:

```bash
pandoc --version
pdflatex --version
```

## Usage

```bash
# Tailored resume as PDF
resume-engine tailor \
  --master resume.md \
  --job posting.txt \
  --output tailored.md \
  --format pdf

# Cover letter as PDF
resume-engine cover \
  --master resume.md \
  --job posting.txt \
  --format pdf

# Full package (resume + cover letter) as PDFs
resume-engine package \
  --master resume.md \
  --job posting.txt \
  --outdir ./application/ \
  --format pdf
```

When `--format pdf` is used, Resume Engine always writes the markdown file first, then converts it to PDF. Both files are kept.

## Output Files

| Command | Markdown | PDF |
|---------|---------|-----|
| `tailor --output tailored.md --format pdf` | `tailored.md` | `tailored.pdf` |
| `cover --output cover.md --format pdf` | `cover.md` | `cover.pdf` |
| `package --outdir app/ --format pdf` | `app/resume.md`, `app/cover-letter.md` | `app/resume.pdf`, `app/cover-letter.pdf` |
| `batch --outdir apps/ --format pdf` | per-job `.md` files | per-job `.pdf` files |

## PDF Styling

The generated PDF uses clean resume formatting:
- 1-inch margins
- Section headers with a thin rule underneath
- Compact spacing between items
- No page header/footer
- 11pt font size

The formatting is applied via a LaTeX header passed to pandoc. If you need custom styling, modify `resume_engine/pdf.py` and the `LATEX_HEADER` string.

## Troubleshooting

**pandoc not found:**
```
RuntimeError: pandoc is not installed.
Install it with: brew install pandoc
```
Install pandoc: `brew install pandoc` (macOS) or `sudo apt install pandoc` (Linux)

**pdflatex not found (PDF engine error):**
```
pandoc: pdflatex not found.
```
Install BasicTeX: `brew install basictex`, then `sudo tlmgr install titlesec enumitem parskip`

**Package not found error during conversion:**
```
! LaTeX Error: File `titlesec.sty' not found.
```
Run: `sudo tlmgr install titlesec enumitem parskip`

!!! tip
    If PDF fails, the markdown output is always written first. You can convert manually with: `pandoc tailored.md -o tailored.pdf`
