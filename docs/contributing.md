# Contributing

Contributions are welcome. Here's how to get started.

## Development Setup

```bash
git clone https://github.com/14-TR/resume-engine
cd resume-engine
pip install -e ".[dev]"
```

Run the tests:

```bash
pytest tests/
```

Run the CI-equivalent lint and format checks:

```bash
ruff check resume_engine/ tests/
ruff format --check resume_engine/ tests/
```

## Project Structure

```
resume_engine/
  cli.py          # Click CLI entry point -- all commands defined here
  engine.py       # Core tailoring logic (prompt construction, LLM calls)
  llm.py          # LLM backend abstraction (Ollama, OpenAI, Anthropic)
  ats.py          # ATS keyword extraction and scoring
  pdf.py          # Markdown-to-PDF via pandoc
  templates.py    # Built-in and custom template management
  interactive.py  # Gap-filling question flow
  batch.py        # Batch mode logic
  importer.py     # Raw resume text to master resume markdown
  scraper.py      # Job posting URL scraper

examples/
  master-resume.md       # Sample master resume (Alex Rivera)
  job-posting.txt        # Sample job posting (Meridian Cloud)
  batch-manifest.json    # Sample batch manifest

tests/
  test_ats.py
  test_cli.py
  test_templates.py
  test_importer.py
```

## Adding a New LLM Backend

1. Open `resume_engine/llm.py`
2. Add a new branch in the `complete()` function
3. Add the new choice to the `type=click.Choice(...)` in `cli.py`
4. Add a section to `docs/reference/llm-backends.md`

## Adding a Built-in Template

1. Open `resume_engine/templates.py`
2. Add a new dict entry to `BUILT_IN_TEMPLATES`
3. Add a section to `docs/reference/templates.md`

## Running the Docs Site Locally

```bash
pip install mkdocs-material
mkdocs serve
```

The docs will be available at `http://localhost:8000`.

## Opening a PR

- Keep PRs focused -- one feature or fix per PR
- Include tests for new behavior
- Update `docs/` and `CHANGELOG.md` if applicable
- Run `pytest tests/`, `ruff check resume_engine/ tests/`, and `ruff format --check resume_engine/ tests/` before submitting

## Releasing

Releases are triggered by pushing a version tag after TR approves the release:

```bash
git tag v0.3.1
git push origin v0.3.1
```

GitHub Actions publishes to PyPI automatically via Trusted Publishing.

Before a release tag:

1. Confirm the next version in `pyproject.toml`
2. Update `docs/changelog.md`
3. Check README and command reference examples against `resume-engine --help`
4. Run `pytest tests/` and `ruff check .`
5. Confirm the release is approved by TR

Agent-created maintenance/docs work should stop at a reviewed PR. Do not publish ad hoc builds or push release tags from agent work unless the active task explicitly authorizes a package release.
