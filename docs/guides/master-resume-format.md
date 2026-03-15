# Master Resume Format

Your master resume is the **complete** version of your career history. It's not meant to be submitted directly -- it's the source of truth that Resume Engine draws from when tailoring for specific jobs.

## The Core Idea

Think of your master resume as a database of everything you've done. For each job application, Resume Engine queries this database and builds a focused, relevant subset.

**More detail is better.** Include every job, every project, every skill. When you omit something from your master resume, you lose the ability to include it in tailored versions.

## Structure

```markdown
# Full Name
email@example.com | (555) 000-0000 | linkedin.com/in/yourname | github.com/yourname
City, State

## Summary

2-3 sentences covering your background, specialization, and what you're looking for.
Keep this broad in your master resume -- it gets rewritten per job during tailoring.

## Skills

**Languages:** Python, JavaScript, Go, SQL, Bash
**Frameworks:** FastAPI, React, Django, Node.js
**Infrastructure:** AWS (EC2, Lambda, RDS, S3), Docker, Kubernetes, Terraform
**Data:** PostgreSQL, Redis, Elasticsearch, Kafka, Airflow
**Practices:** REST APIs, CI/CD, TDD, Agile, Code review, Technical writing

## Experience

### Job Title -- Company Name, Location (YYYY - YYYY or Present)

- Achievement 1: specific, measurable result
- Achievement 2: specific, measurable result
- Achievement 3: context + action + outcome

### Previous Job Title -- Previous Company, Location (YYYY - YYYY)

- Achievement 1
- ...

## Education

**Degree Name** -- University Name, Year
Minor: ... | GPA: ... (include if 3.5+)

## Projects

### Project Name (github.com/link or URL)
Brief description: what it is, what it does, tech stack, usage/impact.

### Another Project
...

## Certifications

- Certification Name (Year)
- ...
```

## Writing Good Bullet Points

The quality of your tailored resumes depends on the quality of your bullet points.

**Formula:** `[Action verb] + [what you did] + [measurable result]`

**Weak:**
```
- Helped with backend development
- Worked on improving performance
```

**Strong:**
```
- Led migration of monolithic Django app to microservices, reducing p99 latency from 1.8s to 310ms
- Built real-time data ingestion pipeline processing 4M events/day using Kafka and Python workers
```

Include numbers wherever you can:
- Team size you led or worked with
- Scale (users, requests/day, data volume)
- Time saved or performance improvement
- Cost reduction percentages
- Uptime percentages

## Skills Section Tips

List technologies explicitly -- the ATS analysis matches against exact keyword occurrences.

**Good:**
```
**Cloud:** AWS (Lambda, EC2, RDS, S3, SQS), GCP (BigQuery, Cloud Functions), Azure
```

**Not as good:**
```
**Cloud:** Cloud computing, various AWS services
```

## Keeping Your Master Resume Updated

After every new job, project, or certification:

1. Add a new section or bullet point
2. Run `resume-engine ats` against a few recent job postings to see if your score improved

Your master resume grows over time. It's a living document, not a one-time task.
