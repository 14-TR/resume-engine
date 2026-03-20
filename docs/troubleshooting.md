# Troubleshooting & FAQ

Common issues and how to fix them.

---

## Installation

### `pip install resume-engine` fails

Make sure you have Python 3.9 or newer:

```bash
python --version
# Python 3.9.x or higher required
```

If you have multiple Python versions, try `pip3` or `python3 -m pip install resume-engine`.

---

### `resume-engine: command not found` after install

Your Python scripts directory is not on your PATH. Try:

```bash
# macOS / Linux
export PATH="$HOME/.local/bin:$PATH"

# Or install with pipx (isolated, no PATH issues)
pipx install resume-engine
```

Add the export to your `~/.zshrc` or `~/.bashrc` to make it permanent.

---

## Ollama Issues

### `Error: Ollama is not running`

Resume Engine defaults to Ollama. Start it before running any command:

```bash
ollama serve
```

Leave that terminal open, or run it in the background:

```bash
ollama serve &
```

To verify it is running:

```bash
curl http://localhost:11434
# Should return: Ollama is running
```

---

### `Error: model not found` / Ollama returns empty response

You need to pull the model first:

```bash
ollama pull qwen2.5:14b
```

This downloads about 9GB. Run it once; subsequent runs use the cached model.

If you want a smaller model (less RAM, lower quality):

```bash
ollama pull llama3.2:3b
OLLAMA_MODEL=llama3.2:3b resume-engine tailor --master resume.md --job posting.txt
```

---

### Ollama times out on long resumes

Large resumes can take 60-120 seconds locally. If you hit a timeout:

```bash
# Use a cloud model for faster results
resume-engine tailor --master resume.md --job posting.txt --model openai
```

Or switch to a smaller Ollama model via the `OLLAMA_MODEL` environment variable.

---

## Cloud Models

### `RuntimeError: OPENAI_API_KEY not set`

Export your API key before running:

```bash
export OPENAI_API_KEY=sk-...
resume-engine tailor --master resume.md --job posting.txt --model openai
```

Add the export to your `~/.zshrc` or `~/.bashrc` to avoid setting it each session.

---

### `RuntimeError: ANTHROPIC_API_KEY not set`

Same pattern:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
resume-engine tailor --master resume.md --job posting.txt --model anthropic
```

---

## PDF Output

### `RuntimeError: pandoc is not installed`

Install pandoc:

=== "macOS"

    ```bash
    brew install pandoc basictex
    sudo tlmgr install titlesec enumitem parskip
    ```

=== "Linux (Debian/Ubuntu)"

    ```bash
    sudo apt install pandoc texlive-latex-extra
    ```

Verify:

```bash
pandoc --version
pdflatex --version
```

---

### `pandoc: pdflatex not found`

You have pandoc but not a LaTeX engine. Install BasicTeX:

```bash
brew install basictex
sudo tlmgr install titlesec enumitem parskip
```

Then restart your terminal and retry.

---

### PDF output looks broken or has missing sections

The markdown file is always written first. If the PDF looks wrong:

1. Check the `.md` output file for LLM artifacts
2. Convert manually with pandoc for debugging:

```bash
pandoc tailored.md -o tailored.pdf --pdf-engine=pdflatex
```

If the markdown looks wrong, the issue is in the LLM output. Try `--model openai` or `--model anthropic` for better quality.

---

## ATS Scores

### My ATS score is very low (under 30%)

A low baseline score is normal before tailoring. It means your master resume and this job use different vocabulary.

**Check if the job is a realistic fit:** If your master resume has zero overlap with the job posting, the role may not match your background.

**After tailoring, check again:**

```bash
resume-engine ats \
  --resume master-resume.md \
  --job posting.txt \
  --tailored tailored-resume.md
```

A well-tailored resume should score 60-80%+.

---

### My tailored ATS score is still under 50%

The LLM may have missed some keywords. Options:

- **Re-run with a cloud model**: `--model openai` or `--model anthropic` produce more thorough tailoring
- **Add missing keywords manually**: Check the "Still missing" list in the ATS output and add them where they genuinely apply
- **Use interactive mode**: `--interactive` lets you answer gap-filling questions that give the LLM more context

---

### ATS score is 100% but the resume looks wrong

ATS scoring is keyword-based -- a 100% score means all keywords appear, not that the resume reads naturally. Always review the output before submitting.

---

## Import Command

### The imported master resume is missing sections

The import command relies on the LLM to structure your raw text. If sections are missing:

1. Check that your raw input includes the relevant experience
2. Try `--model openai` for better extraction accuracy
3. Add missing sections to the output file manually

---

### `--stdin` is not reading my piped input

Make sure you are piping correctly:

```bash
# From clipboard (macOS)
pbpaste | resume-engine import --stdin --output master-resume.md

# From a file via pipe
cat old-resume.txt | resume-engine import --stdin --output master-resume.md
```

---

## LinkedIn Import

### LinkedIn "Save to PDF" gives a file that is hard to convert

LinkedIn PDFs have inconsistent formatting. Use this workflow for best results:

1. Go to your LinkedIn profile
2. Open the browser print dialog (Ctrl+P / Cmd+P)
3. Save as PDF
4. Convert: `pdftotext linkedin.pdf linkedin.txt`
5. Import: `resume-engine import --text linkedin.txt --output master-resume.md`

Or simply copy-paste your LinkedIn profile text directly into a `.txt` file.

---

## Batch Mode

### Batch mode stops partway through

If one job file causes an error, batch mode logs the failure and continues. Check the output directory for successful runs and the terminal output for which files failed.

Run the failed jobs individually to get the full error message:

```bash
resume-engine tailor --master master-resume.md --job failing-job.txt --output out.md
```

---

## Still stuck?

Open an issue on GitHub: [14-TR/resume-engine/issues](https://github.com/14-TR/resume-engine/issues)

Include:
- The command you ran (omit any personal file contents)
- The full error message
- Your OS and Python version (`python --version`)
- Whether you are using Ollama, OpenAI, or Anthropic
