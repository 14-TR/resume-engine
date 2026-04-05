# Resume Engine: A Local-First CLI Architecture for Grounded, Multi-Artifact Job Application Generation

**Author:** TR Ingram  
**Date:** 2026-04-05  
**Version:** 1  

**Abstract**  
Resume Engine is a Python 3.9+ command-line system for transforming a master resume plus a target job description into multiple application artifacts, including tailored resumes, cover letters, interview preparation briefs, fit assessments, ATS analyses, optimization passes, and grounded validation reports. The project combines a small local-first runtime footprint with a modular architecture: prompt-driven generation modules for synthesis, deterministic heuristic analyzers for scoring and safety, a Click-based CLI facade, and optional export layers for PDF rendering and SQLite-backed application tracking. This paper presents the repository's architecture, implementation details, public interfaces, algorithmic properties, security posture, and operational limitations based on direct source inspection of the codebase under `/Users/tr-mini/Desktop/resume-engine`. Particular attention is given to the project's design balance between generative flexibility and explicit anti-hallucination controls, especially the `validate` subsystem introduced as the primary trust feature.

## 1. Introduction

Resume Engine addresses a concrete problem in modern job search workflows: most candidates maintain some form of unstructured or semi-structured master resume, then repeatedly adapt it to heterogeneous job descriptions, ATS keyword expectations, cover-letter conventions, and interview preparation demands. Existing tooling typically fragments this workflow into separate SaaS services or manual copy-editing loops. Resume Engine instead proposes a single local-first CLI that treats the master resume as the canonical source artifact and produces downstream representations on demand.

The repository's roadmap (`roadmap.md:1-35`) defines the vision succinctly: "The best open-source CLI for AI-powered resume tailoring. One command, perfect resume." The implementation broadens that mission beyond simple tailoring. By version `0.3.1` (`pyproject.toml:6-24`), the codebase includes generation commands (`tailor`, `cover`, `package`, `batch`, `optimize`, `interview`, `import`), deterministic analysis commands (`ats`, `score`, `cover-score`, `fit`), governance features (`validate`, `check`), and persistence/ergonomic layers (`config`, `track`, `templates`, `init`).

The scope of this paper is the source tree itself, with emphasis on the production package under `resume_engine/`, the CLI surface in `resume_engine/cli.py`, bundled templates in `templates/`, packaging metadata in `pyproject.toml`, documentation and examples under `docs/` and `examples/`, and the test suite under `tests/`. Where behavior is heuristic rather than formally specified, that is stated explicitly. The analysis was informed by direct inspection of source files, roadmap and documentation review, and a local attempt to execute the test suite.

A useful way to understand the project is as a pipeline compiler for job applications. The master resume acts as source material. The job posting acts as a target specification. Resume Engine then generates specialized outputs, evaluates those outputs against lexical and structural heuristics, and optionally stores workflow metadata in a tracker database. That architecture makes it closer to a developer toolchain than to a conventional resume builder. The system accepts plain text and Markdown as its principal representations, which is a pragmatic engineering choice: text is diffable, composable, portable across platforms, and simple to inspect when a generative step misbehaves.

The repository also shows a deliberate trust posture. Many AI-powered resume tools optimize only for persuasive output quality. Resume Engine repeatedly encodes anti-fabrication rules in its prompts, then backs them with deterministic checks in `validate.py`. That pattern matters because resume generation is unusually sensitive to hallucination risk. A fabricated metric or inflated title can hurt the user materially. The codebase therefore deserves analysis not just as an LLM wrapper, but as a small assurance-oriented application stack.

## 2. System Architecture

### 2.1 High-level Architecture

At a high level, Resume Engine is a layered monolith:

```text
User / Shell
   |
   v
Click CLI (resume_engine/cli.py)
   |
   +--> Config + templates + file/url loading
   +--> Generative modules (engine, optimizer, interview, importer, interactive)
   +--> Deterministic analyzers (ats, scorer, cover_scorer, differ, fit, validate)
   +--> External integrations (llm, scraper, linkedin, pdf, tracker, check)
   |
   v
Markdown / PDF / Console / SQLite outputs
```

The core architectural choice is separation between orchestration and capability modules. `resume_engine/cli.py` concentrates command registration, argument validation, and presentation. Domain logic is delegated into relatively small, mostly single-purpose modules such as `ats.py`, `tracker.py`, `pdf.py`, and `templates.py`. This yields a favorable maintainability property: the CLI is broad but the analytical and generative primitives remain individually testable.

The architecture is monolithic in deployment but modular in code organization. There is no plugin bus, daemon process, or service mesh. Instead, the repository relies on a clear package boundary: each concern gets a file, and cross-file calls are explicit. That keeps startup costs low and makes local installation straightforward. For a CLI distributed through PyPI, that simplicity is a feature rather than a constraint.

### 2.2 Component Topology

The principal runtime pathways are:

1. ingress: a master resume is loaded from a local file, a LinkedIn public URL, or a LinkedIn export via `_load_master()` (`cli.py:19-42`)
2. transformation: command handlers call specialized modules such as `tailor_resume()` (`engine.py:51-68`), `generate_cover_letter()` (`engine.py:71-91`), `assess_fit()` (`fit.py:196-265`), or `validate_outputs()` (`validate.py:264-275`)
3. persistence/rendering: results are written as Markdown, optionally converted to PDF (`pdf.py:40-101`), or stored in SQLite (`tracker.py:79-191`)
4. presentation: results are printed with Rich panels, tables, progress bars, and short summaries

A second important topology is the distinction between local deterministic passes and remote generative passes. Deterministic analyzers depend only on Python stdlib plus lightweight libraries. Generative modules depend on `llm.py`, which is the main boundary to external AI providers. This means the system can still do meaningful work even when no remote provider is configured.

### 2.3 Data Flow

A representative `tailor` flow is:

```text
master.md / LinkedIn source
        +
job posting file / scraped URL
        |
        v
_load_master() + file/url read
        |
        +--> interactive gap analysis (optional)
        |       analyze_gaps() -> ask_questions() -> enrich_master()
        |
        v
tailor_resume()
        |
        v
llm.complete()
        |
        +--> Ollama local HTTP API
        +--> OpenAI chat completions
        +--> Anthropic messages API
        |
        v
markdown output
        |
        +--> optional markdown_to_pdf()
        v
resume file(s)
```

Other flows follow the same pattern with different transforms. `cover` and `package` call the cover-letter generator; `fit` combines ATS analysis plus an LLM evaluation; `optimize` performs generic strengthening rather than job-targeted tailoring; `validate` performs a post-hoc audit of generated artifacts; `track` persists application records to SQLite. The important pattern is compositionality: the repository is not a single end-to-end script, but a set of reusable functions wrapped by CLI commands.

The most important architectural novelty is that Resume Engine does not treat LLM output as the end of the workflow. Instead, it adds deterministic post-generation checks: ATS comparison, diff inspection, heuristic quality scoring, and grounded validation. The system decomposes the job-application pipeline into generation plus verification rather than generation alone. That is a good fit for high-risk content transformation, because the user is not merely seeking fluency; they are seeking correctness and relevance.

### 2.4 Technology Stack and Justification

`pyproject.toml:6-39` declares a minimal runtime stack:

- Python 3.9+
- Click for CLI composition and option parsing
- Rich for terminal UX, panels, tables, and progress bars
- httpx for local and remote HTTP integrations
- sqlite3 from the standard library for the tracker
- pandoc / pdflatex as optional external binaries for PDF export

This stack aligns with the roadmap constraint of minimal dependencies and local-first operation (`roadmap.md:29-34`). The implementation largely honors that goal. The only mandatory non-stdlib Python dependencies are Click, Rich, and httpx. Heavier features such as PDF output and cloud inference are opt-in. That keeps the base package small and lowers friction for installation.

There is also a subtle but important product decision in the stack: Markdown is the internal lingua franca. Instead of trying to maintain a custom structured resume schema with separate rendering templates, the system asks the LLM to emit human-readable Markdown directly. This reduces the amount of renderer logic that needs to exist in the repository, and it keeps the artifacts inspectable with ordinary developer tooling. The tradeoff is that structural guarantees are weaker than they would be with a normalized AST or JSON schema.

## 3. Implementation

### 3.1 Package Entry and Compatibility

The package version is stored in `resume_engine/__init__.py:3` as `__version__ = "0.3.1"`. The canonical entry point is the console script `resume-engine = "resume_engine.cli:main"` (`pyproject.toml:31-32`). A legacy compatibility shim remains in `src/cli.py:1-6`, allowing `python -m src.cli` to invoke the modern CLI surface. This matches recent commit history (`3862b1b`) indicating restored entrypoint compatibility.

The packaging metadata also exposes project URLs for homepage, repository, docs, and bug tracker, and declares optional dependency groups for development and documentation. The result is a conventional modern Python package structure with no unusual build hooks or packaging indirection.

### 3.2 CLI Orchestration Layer

`resume_engine/cli.py` is the control plane. It exposes the following command handlers and line ranges:

- `tailor` (`84-142`)
- `cover` (`177-225`)
- `package` (`253-299`)
- `ats` (`310-393`)
- `batch` (`422-481`)
- `import_resume` (`495-538`)
- `check` (`542-582`)
- template commands (`586-631`)
- `diff_cmd` (`647-766`)
- config commands (`770-862`)
- `score_cmd` (`870-962`)
- `optimize` (`985-1076`)
- `interview` (`1106-1217`)
- `cover_score_cmd` (`1223-1318`)
- tracker commands (`1324-1500`)
- `fit` (`1524-1661`)
- `validate_cmd` (`1671-1772`)
- `init_cmd` (`1782-1914`)

The CLI file is intentionally wide rather than deeply abstracted. The benefit is discoverability: all public commands live in one place. The cost is size and some duplication, especially repeated patterns for loading master/job text, writing Markdown, and optionally converting to PDF. Still, for a user-facing CLI, explicitness may be preferable to over-abstraction.

A representative command such as `tailor` follows a simple orchestration template: validate mutually exclusive options, print a Rich panel, load the master source, load the job source, optionally run interactive gap analysis, call a transformation function, write the Markdown output, and optionally invoke PDF conversion. This pattern is repeated with small variations across `cover`, `package`, `optimize`, and `interview`. It suggests that the next refactor opportunity would be extraction of reusable helpers for source loading, output writing, and PDF emission.

### 3.3 LLM Abstraction

`resume_engine/llm.py` implements a simple provider switch. `complete(prompt, model)` dispatches to `_ollama`, `_openai`, or `_anthropic` (`llm.py:11-20`). Key design choices:

- Ollama default: `OLLAMA_URL` defaults to `http://localhost:11434`, model to `qwen2.5:14b` (`llm.py:7-8`)
- no SDK dependency: all providers are called via raw `httpx.post`
- uniform string contract: every backend returns plain text stripped from the HTTP response
- bounded generation parameters: temperature 0.3 and max token style caps for all backends

The abstraction is intentionally thin. There is no retry logic, rate limiting, schema enforcement, caching, or streaming support. This simplicity makes the module easy to understand and minimizes external dependencies, but it also means reliability is almost entirely delegated to upstream providers. The code expects providers to be available and reasonably compliant.

One concrete inconsistency is visible between code and docs: `docs/reference/llm-backends.md` states Anthropic uses Claude Haiku, but `llm.py:57-72` is hardcoded to `claude-sonnet-4-20250514`. That is a documentation drift issue with user-facing consequences, especially around price and behavior expectations.

### 3.4 Generation Modules

`engine.py` defines the primary synthesis prompts. `tailor_resume()` (`51-68`) injects optional template instructions from `templates.py` into `_BASE_TAILOR_PROMPT` (`5-27`), then calls `complete()`. `generate_cover_letter()` (`71-91`) reuses the same template registry but only as a tone hint rather than structural instructions. `import_resume()` (`115-118`) converts arbitrary raw text into a standardized markdown master resume.

The prompt engineering style is conservative and repetitive on purpose. Each prompt reiterates three rules: preserve honesty, avoid em dashes, and emit clean Markdown only. The prompts also try to constrain length and enforce practical output conventions such as strong action verbs and quantified bullets.

Other generation modules specialize the prompt pattern:

- `optimizer.py:17-35,54-63` performs generic quality improvement and optional change explanation
- `interactive.py:8-98` adds pre-tailoring gap analysis; notably it expects JSON from the LLM and strips markdown fences before parsing
- `interview.py:26-213` requests a structured numbered list and reconstructs typed dataclasses
- `importer.py:5-43` overlaps semantically with `engine.import_resume`, but uses a separately maintained prompt

This reveals a modest architectural inconsistency: import functionality exists in two modules with overlapping prompts and responsibilities. There is no immediate correctness failure, but it creates future drift risk. If formatting guidance changes, two prompts must stay aligned.

### 3.5 Deterministic Analysis Modules

The codebase's strongest engineering characteristic is its use of non-LLM heuristics for evaluation.

#### ATS analysis

`ats.py` tokenizes text (`124-135`), extracts bigrams (`138-144`), computes weighted keyword frequencies (`147-170`), and scores keyword presence in the resume (`173-201`). Complexity is approximately `O(n)` for tokenization plus `O(k)` for keyword scoring, where `k` is the extracted top-N term set. The algorithm is intentionally lexical rather than semantic. That makes it fast and predictable, but it may miss synonymy and equivalent phrasing.

#### Resume scoring

`scorer.py` defines five dimensions totaling 100 points: section completeness, quantified achievements, action verbs, length, and filler detection. Core helpers include `_extract_section_headings()` (`157-165`), `_count_quantified_bullets()` (`168-175`), and `_count_action_verbs()` (`178-183`). This is a rule-based static analysis pass over markdown content. It is best understood as a linter for resume hygiene.

#### Cover-letter scoring

`cover_scorer.py` mirrors the resume scorer with dimensions for opening hook, specificity, value proposition, length, and filler. Important heuristics include generic opener detection (`143-148`), company/role detection (`178-205`), and metric/value-verb counts. It is a structurally similar subsystem adapted to a different artifact class.

#### Diffing

`differ.py` provides structured and unified diffs. `_split_sections()` (`54-74`) segments markdown by heading, and `compute_diff()` (`77-142`) computes both line-level and section-level changes using `difflib.unified_diff`. This is a useful trust affordance because it lets users inspect what changed between master and tailored versions rather than accepting generative output blindly.

#### Fit assessment

`fit.py` is hybrid rather than purely deterministic. It composes ATS score with four LLM-scored dimensions, parses `Score: X/Y` patterns (`113-126`), and falls back to heuristic defaults if the model fails to follow format. This is a pragmatic compromise: the system preserves utility even when the model returns imperfectly structured output.

#### Grounded validation

`validate.py` is the repository's trust anchor. `validate_text()` (`170-261`) compares generated output against both the master resume and job posting. It extracts date ranges, companies, titles, capitalized phrases, bullets, and known skill mentions; then it emits categorized issues such as `date drift`, `company drift`, `title drift`, `unsupported claim`, `suspicious rewrite`, and `unsupported skill`. Severity-weighted penalties produce a final score.

This module is especially notable because it codifies a philosophy: the right post-processing target is not merely did the prose look good, but did the output remain grounded in allowed sources. That philosophy makes Resume Engine more responsible than many comparable AI résumé tools.

### 3.6 External Integration Modules

- `linkedin.py` supports both public-profile scraping (`17-73`) and LinkedIn export parsing (`184-472`)
- `scraper.py` fetches arbitrary job URLs and strips HTML with regexes (`8-49`)
- `pdf.py` writes a temporary LaTeX header and invokes pandoc (`40-101`)
- `check.py` performs environment checks for Ollama, pandoc, pdflatex, and API keys (`10-166`)
- `templates.py` registers bundled and user templates with user-first shadowing semantics (`14-84`)
- `tracker.py` maintains a local SQLite table of applications with CRUD and summary stats (`79-191`)
- `config.py` stores defaults in XDG-style TOML (`46-139`)
- `batch.py` processes multiple job specs sequentially with Rich progress UI (`97-240`)
- `init.py` defines dataclasses for interactive resume building and renders markdown (`14-115`)

Each module is relatively small and direct. `pdf.py` is notable because it enriches pandoc with a bundled LaTeX header that tunes margins, spacing, section formatting, and list density. `templates.py` is notable because it treats user templates as shadowing built-ins, which is a sane extensibility model. `tracker.py` is notable because it avoids ORM complexity and uses plain SQL, which is entirely adequate for the single-table workload.

### 3.7 Data Structures and Schemas

The codebase favors simple dataclasses and dictionaries: `BatchResult`, `JobSpec`, `DimensionResult`, `ScorerResult`, `CoverDimension`, `CoverScorerResult`, `FitDimension`, `FitResult`, `InterviewQuestion`, `FollowupQuestion`, `InterviewPrepResult`, `ValidationIssue`, `ValidationTargetResult`, `ValidationReport`, `ResumeData`, `Experience`, and `Education`.

The SQLite schema in `tracker.py:53-64` is a single table:

```sql
CREATE TABLE IF NOT EXISTS applications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    company    TEXT NOT NULL,
    role       TEXT NOT NULL,
    date       TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'applied',
    url        TEXT,
    notes      TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

The schema is intentionally flat, which is sufficient for individual users and keeps query logic trivial. It also avoids migration complexity at this project stage.

## 4. API / Interface Specification

Resume Engine exposes a CLI, not a network service. Its effective API surface is therefore the command set in `cli.py` plus the callable module functions.

### 4.1 Primary CLI Commands

- `tailor` (`cli.py:84-142`): inputs master resume and job text; outputs tailored markdown and optional PDF
- `cover` (`177-225`): generates a cover letter from the same sources
- `package` (`253-299`): emits both resume and cover letter into an output directory
- `ats` (`310-393`): computes keyword match, optionally before/after with a tailored resume
- `batch` (`422-481`): processes multiple jobs from a directory or JSON manifest
- `import` (`495-538`): transforms raw text or stdin into master-resume markdown
- `check` (`542-582`): inspects local runtime dependencies
- `templates list/show` (`592-631`): exposes template registry contents
- `diff` (`647-766`): shows section-aware or unified changes between two resume files
- `config set/get/unset/list/reset` (`770-862`): manipulates persistent defaults
- `score` (`870-962`): deterministic resume quality score
- `optimize` (`985-1076`): LLM-based generic strengthening of a resume
- `interview` (`1106-1217`): question bank and STAR frameworks
- `cover-score` (`1223-1318`): deterministic cover-letter score
- `track add/list/show/update/delete/stats` (`1324-1500`): application tracker operations
- `fit` (`1524-1661`): hybrid apply/no-apply assessment
- `validate` (`1671-1772`): grounded output audit
- `init` (`1782-1914`): interactive master-resume creation

### 4.2 Public Python Functions

Representative callable interfaces include:

- `llm.complete(prompt, model)`
- `engine.tailor_resume(master_text, job_text, model, template)`
- `engine.generate_cover_letter(master_text, job_text, model, template)`
- `batch.run_batch(master_text, jobs, outdir, model, fmt, template, with_cover, console)`
- `ats.analyze(resume_text, job_text, top_n)`
- `scorer.score_resume(text)`
- `cover_scorer.score_cover_letter(text)`
- `fit.assess_fit(resume_text, job_text, model, ats_top_n)`
- `validate.validate_text(master_text, job_text, output_text, label)`
- `validate.validate_outputs(master_text, job_text, tailored_resume_text, cover_letter_text)`
- `tracker.add_application(...)`, `list_applications(...)`, `update_application(...)`, and related CRUD helpers

### 4.3 Error Handling

Error handling is deliberately lightweight:

- invalid CLI usage raises `click.UsageError`
- missing provider credentials raise `RuntimeError`
- network failures from `httpx` propagate or are wrapped into `RuntimeError`
- PDF conversion failures raise `RuntimeError`, but some commands catch them and preserve Markdown output
- tracker operations return booleans for missing records rather than exceptions

This makes the tool forgiving in common cases, but error semantics are not uniform across modules. In some paths the user gets a rich explanatory message; in others the raw exception string surfaces. That is acceptable at alpha maturity but worth unifying before broader adoption.

## 5. Performance Analysis

Most deterministic modules operate in linear or near-linear time relative to input text size:

- tokenization / regex scanning in `ats.py`, `scorer.py`, and `cover_scorer.py`: `O(n)`
- diffing in `differ.py`: dominated by `difflib`, typically near `O(n*m)` worst case but acceptable for resume-scale documents
- validation in `validate.py`: largely `O(n)` token scans plus similarity checks per bullet against source bullets; practical cost remains small due to tiny documents
- SQLite tracker CRUD: effectively `O(1)` or `O(log n)` at this scale

Actual bottlenecks are external: LLM latency, network scraping latency, pandoc/LaTeX subprocess startup, and sequential batch execution (`batch.py:97-189`). The architecture is appropriate for single-user CLI use, but not designed as a high-throughput multi-tenant service.

The batch runner is especially illustrative. `run_batch()` loops over job specs sequentially, creates an output directory per job, loads the job text, invokes tailoring, optionally generates a cover letter, and optionally converts artifacts to PDF. The complexity is linear in the number of jobs times the cost of each external generation call. This is sensible for a solo job seeker applying to a handful of roles, but it will scale poorly for larger campaign-style usage.

A local test run during this audit failed during collection because `httpx` was not installed in the audit environment. That is not a packaging defect, since `pyproject.toml` correctly declares `httpx>=0.24`, but it shows the project's runtime correctness depends on installation discipline. No benchmark harness exists in the repository, so algorithmic properties are clearer than empirical throughput. The codebase would benefit from even a small synthetic benchmark suite covering ATS extraction, validation speed, and per-job batch latency.

## 6. Security Considerations

Resume Engine handles sensitive personal data: employment history, contact information, skills, and occasionally API keys. The main security considerations are:

### 6.1 Data Locality

The local-first default is the strongest privacy feature. Ollama is the default provider (`llm.py:11-20`), and all deterministic analyses are local. Users can perform tailoring without transmitting resumes to remote APIs. This is a meaningful product differentiator for privacy-conscious users.

### 6.2 Attack Surface

Main attack surfaces include:

- remote HTTP calls to OpenAI / Anthropic / Ollama
- arbitrary job URL scraping via `scraper.py`
- LinkedIn HTML/ZIP ingestion via `linkedin.py`
- subprocess invocation of pandoc/pdflatex in `pdf.py`
- local file writes based on user-provided paths

There is no shell interpolation in subprocess calls. `pdf.py` passes argument arrays to `subprocess.run`, which reduces command-injection risk. SQLite operations use parameterized queries in tracker operations, which is likewise correct.

### 6.3 Input Validation

Validation is mixed:

- CLI option checking via Click is strong for required combinations
- tracker status values are validated against enumerated constants (`tracker.py:26-28, 87-88, 149-150`)
- config keys/values are validated against `VALID_KEYS` (`config.py:32-38, 100-109`)
- job scraping and LinkedIn parsing perform little sanitization beyond textual extraction

The weakest area is HTML parsing. `scraper.py` and the HTML fallback portions of `linkedin.py` rely on regex stripping rather than DOM parsing. That approach is simple and dependency-light, but brittle. It may include hidden page noise, omit meaningful content, or behave unpredictably on highly dynamic pages.

### 6.4 Output Trust

The most security-relevant control is `validate.py`, which attempts to detect hallucinated claims before the user sends the output externally. This is not a formal verifier, but it substantially reduces the risk of fabricated companies, titles, dates, or skills. It is arguably the most important subsystem in the repository because it addresses the failure mode that matters most in this domain.

That said, heuristic grounding checks can yield both false positives and false negatives. A legitimate rewrite may be flagged as suspicious if its wording diverges too much from the source bullet. Conversely, a subtle but unsupported embellishment may slip through if it shares enough lexical overlap. This is not a criticism so much as a calibration reminder: the validator is a strong lint layer, not a proof system.

## 7. Known Limitations & Technical Debt

Several issues are visible from direct inspection:

1. documentation drift: `docs/reference/llm-backends.md` says Anthropic uses Claude Haiku, but `llm.py:57-72` hardcodes `claude-sonnet-4-20250514`
2. duplicate import logic: `engine.py` and `importer.py` each define their own import prompt and function
3. CLI size: `cli.py` is nearly two thousand lines, making it the primary maintenance hotspot
4. HTML scraping brittleness: `scraper.py` and parts of `linkedin.py` use regex-heavy extraction that will fail on highly scripted pages
5. no formal schemas for most LLM output: only `interactive.py` tries to coerce JSON
6. sequential batch execution: practical for individuals, slow for large application bursts
7. potential false positives in validation: `validate.py` uses heuristic token grounding and `SequenceMatcher`
8. template system is prompt-only: it affects generation guidance but not a real renderer/layout engine
9. init formatting divergence: `init.py:74-81` renders experience as `Title | Company`, whereas import prompts and docs standardize on `Title -- Company`
10. test environment dependency coupling: modules import `httpx` at load time, which prevented partial test collection in a misconfigured environment

Two additional architectural debts are worth noting. First, the project has a lot of prompt logic but very little structured output enforcement. Most parsing is regex-based over freeform text. That works surprisingly well when prompts are stable, but it introduces fragility as models or prompt wording evolve. Second, many commands are operationally similar but implemented independently in the CLI. That speeds feature addition early on, but it accumulates maintenance cost over time.

## 8. Related Work

Resume Engine sits between several product categories: SaaS resume builders focused on visual templates, ATS keyword analyzers, AI cover-letter generators, job-search CRMs/trackers, and interview prep assistants. Its distinguishing trait is unification in a single local-first CLI. Unlike visual-first resume builders, it treats Markdown as the primary authoring representation. Unlike pure prompt wrappers, it includes deterministic scoring and validation modules. Unlike job trackers, it keeps generation, evaluation, and tracking in one repository.

The closest conceptual analog is a developer-oriented static-site-generator workflow for job applications: source text plus target description in, multiple derived artifacts out, with linting and validation passes in between. That framing explains many of the repository's strengths. It also clarifies the intended user: someone comfortable with files, command lines, and iterative review, rather than someone who wants a WYSIWYG editor.

Relative to commercial AI resume products, the novel contribution is not any single heuristic algorithm. Rather, it is the integration pattern: local-first generation, deterministic quality scoring, grounded hallucination checks, template-aware prompting, and application tracking in one compact package. For open-source tooling, that makes the project unusually complete.

## 9. Future Work

The roadmap claims the trust layer should precede additional generation surface area, and that is the correct priority. Based on the repository state, the most valuable next steps are:

1. unify import logic into one canonical module
2. extract reusable CLI helpers to reduce duplication
3. add structured output schemas for LLM-backed commands
4. introduce concurrency controls or async batching
5. add fixture-based benchmark tests for ATS, validation, and batch mode
6. harden scraping with parser libraries or provider-specific adapters
7. add optional semantic similarity in ATS/validation rather than purely lexical checks
8. expose JSON output modes for scripting and CI use
9. document model behavior and cost tradeoffs more precisely
10. add migration support for tracker schema evolution

A more ambitious direction would be a normalized intermediate representation for resumes and cover letters. Instead of relying entirely on freeform Markdown, the system could parse or generate a structured resume object, then render Markdown and PDF from that object. Such a refactor would be substantial, but it would improve validation accuracy, diff quality, and testability.

## 10. Appendix

### 10.1 Full File Tree

```text
.github/workflows/ci.yml
.github/workflows/docs.yml
.github/workflows/publish.yml
.gitignore
.pytest_cache/.gitignore
.pytest_cache/CACHEDIR.TAG
.pytest_cache/README.md
.pytest_cache/v/cache/lastfailed
.pytest_cache/v/cache/nodeids
.ruff_cache/.gitignore
.ruff_cache/0.15.5/16060132609622192576
.ruff_cache/0.15.5/5758493480780935177
.ruff_cache/0.15.5/9812615345200772111
.ruff_cache/0.15.6/3479601664348739384
.ruff_cache/0.15.6/6193114108018156919
.ruff_cache/CACHEDIR.TAG
CHANGELOG.md
LICENSE
README.md
docs/changelog.md
docs/contributing.md
docs/getting-started/installation.md
docs/getting-started/quickstart.md
docs/guides/job-search-workflow.md
docs/guides/master-resume-format.md
docs/index.md
docs/reference/commands.md
docs/reference/llm-backends.md
docs/reference/pdf-output.md
docs/reference/templates.md
docs/technical-paper.md
docs/troubleshooting.md
docs/tutorials/ats-analysis.md
docs/tutorials/batch-mode.md
docs/tutorials/import-from-linkedin.md
docs/tutorials/tailor-first-resume.md
examples/README.md
examples/batch-manifest.json
examples/job-posting-frontend.txt
examples/job-posting.txt
examples/master-resume.md
examples/raw-resume.txt
mkdocs.yml
pyproject.toml
resume_engine/__init__.py
resume_engine/ats.py
resume_engine/batch.py
resume_engine/check.py
resume_engine/cli.py
resume_engine/config.py
resume_engine/cover_scorer.py
resume_engine/differ.py
resume_engine/engine.py
resume_engine/fit.py
resume_engine/importer.py
resume_engine/init.py
resume_engine/interactive.py
resume_engine/interview.py
resume_engine/linkedin.py
resume_engine/llm.py
resume_engine/optimizer.py
resume_engine/pdf.py
resume_engine/scorer.py
resume_engine/scraper.py
resume_engine/templates.py
resume_engine/tracker.py
resume_engine/validate.py
roadmap.md
src/__init__.py
src/cli.py
templates/classic.md
templates/concise.md
templates/executive.md
templates/technical.md
tests/__init__.py
tests/test_ats.py
tests/test_check.py
tests/test_cli.py
tests/test_config.py
tests/test_cover_scorer.py
tests/test_differ.py
tests/test_engine_import.py
tests/test_fit.py
tests/test_importer.py
tests/test_init.py
tests/test_interview.py
tests/test_linkedin.py
tests/test_optimizer.py
tests/test_pdf.py
tests/test_scorer.py
tests/test_templates.py
tests/test_tracker.py
tests/test_validate.py
```

### 10.2 Dependency List

Runtime dependencies from `pyproject.toml`:

- click>=8.0
- httpx>=0.24
- rich>=13.0

Optional development dependencies:

- pytest>=7.0
- pytest-cov>=4.0
- ruff>=0.3

Optional docs dependency:

- mkdocs-material>=9.0

External tool dependencies:

- pandoc
- pdflatex / BasicTeX or TeX Live
- Ollama (for default local inference)

### 10.3 Configuration Reference

Persistent config keys from `config.py:32-38`:

| Key | Allowed Values | Meaning |
|---|---|---|
| `model` | `ollama`, `openai`, `anthropic` | default LLM backend |
| `format` | `md`, `pdf` | default output format |
| `output` | free-form path | default file output |
| `outdir` | free-form path | default directory output |
| `template` | free-form slug | default resume style |

Default path:

- XDG config: `~/.config/resume-engine/config.toml`

Tracker paths:

- XDG data: `~/.local/share/resume-engine/tracker.db`

Template search order from `templates.py:14-21`:

1. `~/.resume-engine/templates/`
2. bundled `templates/`

### 10.4 Tests and Coverage Surface

The repository contains focused tests for nearly every module, including ATS analysis, CLI behavior, config persistence, cover scoring, diffing, fit assessment, import paths, interview preparation, LinkedIn parsing, optimizer behavior, PDF conversion, scoring, templates, tracker persistence, and validation. This breadth is a major strength. The missing piece is not feature coverage but operational evidence: there is no benchmark or end-to-end golden-output suite for generated artifacts.

### 10.5 Audit Red Flags

- Documentation and implementation disagree on the Anthropic backend model.
- Import functionality is duplicated.
- Resume formatting conventions differ between `init.py` and prompt-based import docs.
- Scraping remains heuristic and fragile.
- The validation system is promising but not formally calibrated against false-positive and false-negative rates.
