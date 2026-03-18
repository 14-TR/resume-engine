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
10. Documentation site with tutorials

## Constraints
- Python 3.9+, minimal dependencies
- Local-first (Ollama default, no API key required for basic usage)
- No em dashes in output
- Public repo (14-TR/resume-engine)
- MIT license
