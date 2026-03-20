# Changelog

## [Unreleased]

### Added
- `resume-engine check` command -- system health checker that verifies Ollama is running, pandoc/pdflatex are installed, and API keys are set; exits non-zero when required checks fail; 20 new tests in `tests/test_check.py`

## [Previously Unreleased]

### Added
- `resume-engine import` command -- converts any raw resume text (LinkedIn copy-paste, PDF export, old resumes) into a structured master resume markdown
- 12 new tests covering the import module and CLI command
- README documentation for the LinkedIn/import workflow


## [0.2.0] - 2026-03-12

### Changed
- Renamed Python package from `src` to `resume_engine` for proper PyPI distribution
- Bumped version to 0.2.0

### Added
- GitHub Actions publish workflow (`publish.yml`) - triggers on `v*.*.*` tags using PyPI Trusted Publishing
- PyPI, CI, and license badges in README
- Contributing / Releasing section in README

## [0.1.0] - 2026-03-10

### Added
- Initial CLI scaffold (tailor, cover, package commands)
- LLM backends: Ollama (default), OpenAI, Anthropic
- Example master resume and job posting in `examples/`
- PDF output via pandoc (`--format pdf`)
- ATS keyword analysis command with match scoring
- Interactive mode with gap analysis and Q&A
- Template system (classic, concise, technical, executive)
- Batch mode - tailor to multiple jobs at once
- GitHub Actions CI (43 tests, ruff lint)
