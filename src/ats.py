"""ATS keyword analysis -- match scoring between resume and job posting."""

import re
from collections import Counter
from typing import List, Tuple

# Common stopwords to skip
STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "that",
    "this",
    "these",
    "those",
    "i",
    "you",
    "we",
    "they",
    "he",
    "she",
    "it",
    "our",
    "your",
    "their",
    "its",
    "my",
    "we",
    "us",
    "not",
    "no",
    "if",
    "then",
    "than",
    "so",
    "also",
    "just",
    "more",
    "most",
    "some",
    "any",
    "all",
    "each",
    "both",
    "other",
    "into",
    "through",
    "about",
    "up",
    "out",
    "such",
    "what",
    "how",
    "when",
    "where",
    "who",
    "which",
    "work",
    "working",
    "worked",
    "team",
    "role",
    "position",
    "experience",
    "ability",
    "strong",
    "excellent",
    "good",
    "great",
    "well",
    "new",
    "including",
    "etc",
    "per",
    "across",
    "within",
    "between",
}

# High-value tech/skill patterns to look for
SKILL_PATTERNS = [
    r"\b[A-Z][a-zA-Z]+(?:\.[a-zA-Z]+)+\b",  # e.g. Node.js, ASP.NET
    r"\b[A-Z]{2,}\b",  # e.g. SQL, AWS, API
    r"\b[A-Za-z]+\+\+\b",  # e.g. C++
    r"\b[A-Za-z]#\b",  # e.g. C#
]


def _tokenize(text: str) -> List[str]:
    """Extract meaningful words and phrases from text."""
    # Preserve known multi-word patterns before lowercasing
    tokens = []

    # Add whole words (lowercase, no punctuation)
    cleaned = text.lower()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    words = cleaned.split()
    tokens = [w for w in words if len(w) >= 3 and w not in STOPWORDS]

    return tokens


def _extract_bigrams(tokens: List[str]) -> List[str]:
    """Extract 2-word phrases from token list."""
    return [
        f"{tokens[i]} {tokens[i + 1]}"
        for i in range(len(tokens) - 1)
        if tokens[i] not in STOPWORDS and tokens[i + 1] not in STOPWORDS
    ]


def extract_keywords(job_text: str, top_n: int = 30) -> List[Tuple[str, int]]:
    """
    Extract the most important keywords and phrases from a job posting.
    Returns list of (keyword, frequency) sorted by frequency.
    """
    tokens = _tokenize(job_text)
    bigrams = _extract_bigrams(tokens)

    # Count everything
    all_terms = tokens + bigrams
    counts = Counter(all_terms)

    # Boost capitalized terms from original text (proper nouns, tech names)
    for match in re.finditer(r"\b([A-Z][a-zA-Z]{1,}(?:\.[a-zA-Z]+)*)\b", job_text):
        word = match.group(1).lower()
        if word not in STOPWORDS and len(word) >= 2:
            counts[word] = counts.get(word, 0) + 2  # boost

    # Filter: keep only terms that appear at least twice OR are capitalized tech terms
    keywords = {k: v for k, v in counts.items() if v >= 2 and len(k) >= 3}

    # Sort by frequency descending
    sorted_kw = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
    return sorted_kw[:top_n]


def score_resume(resume_text: str, keywords: List[Tuple[str, int]]) -> dict:
    """
    Score a resume against a list of keywords.
    Returns dict with score (0-100), matched, and missing keywords.
    """
    resume_lower = resume_text.lower()
    # Remove punctuation for matching
    resume_clean = re.sub(r"[^\w\s]", " ", resume_lower)

    matched = []
    missing = []

    for kw, freq in keywords:
        # Check if keyword (or its significant parts) appear in resume
        if kw in resume_clean:
            matched.append(kw)
        else:
            missing.append(kw)

    total = len(keywords)
    score = round((len(matched) / total * 100)) if total > 0 else 0

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "total_keywords": total,
        "matched_count": len(matched),
    }


def analyze(resume_text: str, job_text: str, top_n: int = 30) -> dict:
    """Full ATS analysis: extract keywords and score the resume."""
    keywords = extract_keywords(job_text, top_n=top_n)
    result = score_resume(resume_text, keywords)
    result["keywords"] = keywords
    return result
