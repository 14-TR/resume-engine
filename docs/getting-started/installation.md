# Installation

## Requirements

- Python 3.9 or newer
- pip

## Install from PyPI

```bash
pip install resume-engine
```

Verify the install:

```bash
resume-engine --version
```

## Install from Source

```bash
git clone https://github.com/14-TR/resume-engine
cd resume-engine
pip install -e ".[dev]"
```


## Verify Your Setup

After installing, run the system check to confirm everything is working:

```bash
resume-engine check
```

This checks Ollama connectivity, pandoc availability, and any API keys you have configured. Green means go -- you are ready to tailor resumes.

## LLM Backend Setup

Resume Engine uses **Ollama** by default (free, runs locally). No API key required.

### Ollama (default, recommended)

1. Install Ollama: [ollama.com](https://ollama.com)
2. Pull the default model:

```bash
ollama pull qwen2.5:14b
```

3. Start Ollama (it runs as a background service):

```bash
ollama serve
```

That's it -- `resume-engine` will use Ollama automatically.

### OpenAI (optional)

Set your API key as an environment variable:

```bash
export OPENAI_API_KEY=sk-...
resume-engine tailor --master resume.md --job posting.txt --model openai
```

### Anthropic (optional)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
resume-engine tailor --master resume.md --job posting.txt --model anthropic
```

## PDF Support (optional)

PDF output requires pandoc and a LaTeX engine:

=== "macOS"

    ```bash
    brew install pandoc basictex
    sudo tlmgr install titlesec enumitem parskip
    ```

=== "Linux (Debian/Ubuntu)"

    ```bash
    sudo apt install pandoc texlive-latex-extra
    ```

Once installed, add `--format pdf` to any command:

```bash
resume-engine tailor --master resume.md --job posting.txt --output tailored.md --format pdf
```
