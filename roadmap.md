# Resume Engine Roadmap

**Vision:** The best open-source CLI for AI-powered resume tailoring. One command, perfect resume.

**Goal:** Public adoption — useful to any job seeker.

## Priority Queue

1. ~~Add example master resume + job posting in examples/ directory~~ (done)
2. ~~PDF output via weasyprint or pandoc (--format pdf)~~ (done)
3. ~~ATS keyword analysis — show match score before/after tailoring~~ (done)
4. ~~Interactive mode — ask user questions to fill gaps~~ (done)
5. ~~Template system — different resume styles/layouts~~ (done)
6. ~~Batch mode — tailor to multiple jobs at once~~ (done)
7. ~~LinkedIn profile import as master resume source~~ (done)
8. ~~PyPI publish — `pip install resume-engine`~~ (done)
9. ~~GitHub Actions CI (tests + lint)~~ (done)
10. ~~Documentation site with tutorials~~ (done)

11. ~~Persistent config (`resume-engine config set model openai`) -- save defaults, skip repeated flags~~ (done)
12. ~~Resume quality scorer (`resume-engine score resume.md`) -- instant 0-100 health score, 5 dimensions, actionable suggestions, no LLM required~~ (done)
13. ~~Resume optimizer (`resume-engine optimize resume.md`) -- LLM-powered generic improvement: strengthen bullets, remove filler, flag missing metrics, no job posting required~~ (done)
14. ~~Interview prep generator (`resume-engine interview`) -- predict likely questions (Behavioral, Technical, Culture Fit, Resume Deep-Dive) with STAR-method answer frameworks tailored to the candidate's real experience~~ (done)
15. ~~Job fit assessment (`resume-engine fit`) -- composite 0-100 fit score across ATS match, required skills, seniority, and domain; gives Apply / Apply with caution / Skip recommendation before tailoring~~ (done)
16. ~~Cover letter quality scorer (`resume-engine cover-score cover-letter.md`) -- instant 0-100 health score, 5 dimensions (opening hook, company specificity, value proposition, length, filler), no LLM required~~ (done)
17. ~~Application tracker (`resume-engine track`) -- local SQLite log of jobs applied to (company, role, date, status, notes); search and update status from the CLI~~ (done)
18. ~~Interactive resume builder (`resume-engine init`) -- guided setup wizard creates a master resume from scratch via interactive prompts; no existing resume or LLM required~~ (done)
19. ~~Grounded output validator (`resume-engine validate`) -- compare tailored resume / cover letter output against the source master resume + job posting, flag unsupported claims, title/date/company drift, and suspicious rewrites before the user sends anything. This should become the main trust feature before adding more generation surface area.~~ (done)

## Constraints
- Python 3.9+, minimal dependencies
- Local-first (Ollama default, no API key required for basic usage)
- No em dashes in output
- Public repo (14-TR/resume-engine)
- MIT license

20. ~~Machine-readable scoring output (`resume-engine score --json`) -- emit structured JSON for scripting, dashboards, and CI checks~~ (done)
21. ~~Environment doctor (`resume-engine doctor`) -- backend-aware setup diagnostics for Python version, configured default model, Ollama reachability, API keys, and PDF tooling; supports `--strict` for CI and scripted setup checks~~ (done)
