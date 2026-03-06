"""Job posting scraper -- extracts text from job URLs."""
import httpx
import re


def scrape_job_posting(url: str) -> str:
    """Fetch a job posting URL and extract readable text."""
    resp = httpx.get(url, follow_redirects=True, timeout=30,
                     headers={"User-Agent": "Mozilla/5.0 (resume-engine)"})
    resp.raise_for_status()
    html = resp.text
    
    # Strip tags, keep text
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Try to find the job description section
    # Most job sites have these keywords near the actual content
    markers = ['responsibilities', 'qualifications', 'requirements', 
               'about the role', 'job description', 'what you', 'who you']
    
    lower = text.lower()
    best_start = 0
    for marker in markers:
        idx = lower.find(marker)
        if idx != -1 and (best_start == 0 or idx < best_start):
            best_start = max(0, idx - 200)  # Include some context before
    
    if best_start > 0:
        text = text[best_start:best_start + 5000]
    else:
        text = text[:5000]
    
    return text
