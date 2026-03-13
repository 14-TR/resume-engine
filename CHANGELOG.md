# Changelog

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
