## [0.3.1] - 2026-03-28

### Added
- `resume-engine interview` command - LLM-powered interview prep generator
  - Predicts likely questions across 4 categories: Behavioral, Technical, Culture Fit, Resume Deep-Dive
  - Each question includes a STAR-method answer framework tailored to the candidate's actual experience
  - `--count` option to control number of questions (default: 10)
  - `--with-followups` flag: generates additional probing/follow-up questions targeting resume specifics
  - `--output` flag: saves full prep sheet to a markdown file
  - No-fabrication rule enforced in prompt -- frameworks reference real companies/roles only
  - 24 tests covering parser, module API, and CLI

# Changelog

## [0.3.0] - 2026-03-27

### Added
- `resume-engine config` command - persistent configuration system
  - Save defaults for model, format, template, output directory
  - `config set/get/unset/list/reset` subcommands
  - 25 tests covering config module and CLI
- `resume-engine score` command - resume quality scoring (0-100)
  - Scores across 5 dimensions: structure, readability, metrics, keywords, impact
  - Provides actionable improvement suggestions
  - 37 tests covering scorer module and CLI
- `resume-engine diff` command - section-aware resume comparison
  - Shows which sections changed between original and tailored resume
  - Line counts and change statistics
  - 20 tests covering differ module and CLI
- `resume-engine optimize` command - LLM-powered resume improvement without job posting
  - Strengthens weak bullet points with action verbs
  - Replaces filler language with direct phrasing
  - Flags bullets missing quantified metrics with [ADD METRIC] placeholders
  - --explain flag: asks LLM to summarize what changed
  - --diff flag: shows section-level diff table of before/after
  - --format pdf support via pandoc
  - 11 tests covering optimizer module and CLI
- Total: 93 new tests across new commands (223 total tests)

## [0.2.0] - 2026-03-12

### Changed
- Renamed Python package from `src` to `resume_engine` for proper PyPI distribution
- Bumped version to 0.2.0

### Added
- GitHub Actions publish workflow (`publish.yml`) - triggers on `v*.*.*` tags using PyPI Trusted Publishing
- PyPI, CI, and license badges in README
- Contributing / Releasing section in README
- `resume-engine import` command - convert raw resume text to structured master resume markdown
- Troubleshooting and FAQ page in documentation site
- Changelog page in documentation site nav

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
