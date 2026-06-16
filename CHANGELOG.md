# Changelog

All notable changes to Resume Engine are documented here.

## [Unreleased]

### Changed
- Clarified release documentation for maintenance/adoption work after the 0.3.1 package surface.
- Kept release ownership explicit: agent work should prepare docs/PRs for review, not push tags or publish packages without TR approval.
- Updated the legacy `check` failure guidance to send users back through `resume-engine doctor`, matching the current install/onboarding path.

---

## [0.3.1] - 2026-05-01

### Added
- Shared `resume-engine.dashboard/v1` JSON envelope across review and automation commands.
- Machine-readable JSON output for `tailor`, `cover`, `package`, `batch`, `ats`, `diff`, `optimize`, `doctor`, `score`, `cover-score`, `fit`, `interview`, and `validate`.
- Expanded `package` output with an optional validation report and dashboard manifest.
- `doctor` setup diagnostics for Python version, configured backend, Ollama, provider keys, and PDF tooling.
- Grounded validation, fit assessment, interview prep, cover scoring, tracker export, and interactive initialization commands.
- Automation workflow documentation for JSON-first review gates.

### Changed
- Updated README and command reference coverage for the completed public CLI surface.
- Restored legacy `src.cli` entrypoint compatibility for older invocation paths.

---

## [0.3.0] - 2026-03-27

### Added
- `resume-engine import` command -- converts raw resume text, LinkedIn copy-paste, PDF exports, and old resumes into a structured master resume markdown file.
- `resume-engine optimize` command for general resume improvement without a target job.
- `resume-engine score` command for instant resume quality scoring.
- `resume-engine diff` command for section-aware comparison between original and tailored resumes.
- `resume-engine config` commands for persisted local defaults.
- Documentation site, troubleshooting guide, and command reference expansion.

### Changed
- Bumped package and CLI version to 0.3.0.
- Kept the public package local-first with Ollama as the default backend and cloud providers as optional integrations.

---

## [0.2.0] - 2026-03-12

### Changed
- Renamed Python package from `src` to `resume_engine` for proper PyPI distribution.
- Bumped version to 0.2.0.

### Added
- GitHub Actions publish workflow (`publish.yml`) -- triggers on `v*.*.*` tags using PyPI Trusted Publishing.
- PyPI, CI, and license badges in README.
- Contributing / Releasing section in README.

---

## [0.1.0] - 2026-03-10

### Added
- Initial CLI scaffold (`tailor`, `cover`, `package` commands).
- LLM backends: Ollama (default), OpenAI, Anthropic.
- Example master resume and job posting in `examples/`.
- PDF output via pandoc (`--format pdf`).
- ATS keyword analysis command with match scoring.
- Interactive mode with gap analysis and Q&A.
- Template system (classic, concise, technical, executive).
- Batch mode -- tailor to multiple jobs at once.
- GitHub Actions CI (43 tests, ruff lint).
