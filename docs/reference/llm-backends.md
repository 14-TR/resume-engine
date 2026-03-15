# LLM Backends

Resume Engine supports three LLM backends. Ollama is the default and requires no API key.

## Ollama (default)

Runs locally on your machine. Free, private, no internet required once set up.

**Setup:**

```bash
# Install Ollama
brew install ollama   # macOS
# or download from https://ollama.com

# Pull the default model
ollama pull qwen2.5:14b

# Start the server (runs in background)
ollama serve
```

**Use:**

```bash
resume-engine tailor --master resume.md --job posting.txt
# or explicitly:
resume-engine tailor --master resume.md --job posting.txt --model ollama
```

**Notes:**
- Requires ~9GB RAM for qwen2.5:14b
- Quality is excellent for tailoring tasks
- Ollama must be running before invoking resume-engine

---

## OpenAI

Uses the OpenAI API. Higher quality output, especially for complex resumes.

**Setup:**

```bash
export OPENAI_API_KEY=sk-...
```

**Use:**

```bash
resume-engine tailor --master resume.md --job posting.txt --model openai
```

**Notes:**
- Uses `gpt-4o-mini` by default (fast and affordable)
- ~$0.01-0.05 per resume tailoring operation
- Requires internet access

---

## Anthropic

Uses the Anthropic Claude API.

**Setup:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**Use:**

```bash
resume-engine tailor --master resume.md --job posting.txt --model anthropic
```

**Notes:**
- Uses Claude Haiku by default (fast and affordable)
- Excellent at following formatting instructions

---

## Choosing a Backend

| Use case | Recommended |
|----------|-------------|
| Getting started / experimenting | `ollama` |
| Production batch runs (free) | `ollama` |
| Highest quality output | `openai` or `anthropic` |
| Privacy-sensitive resume data | `ollama` |
| Fast cloud option | `openai` (gpt-4o-mini) |

---

## Troubleshooting

**Ollama connection error:**
```
Error: Could not connect to Ollama at http://localhost:11434
```
Make sure Ollama is running: `ollama serve`

**OpenAI API key error:**
```
Error: No API key found
```
Set `OPENAI_API_KEY` in your shell or `.env` file.

**Model not found (Ollama):**
```
Error: model not found: qwen2.5:14b
```
Pull the model first: `ollama pull qwen2.5:14b`
