"""Tests for ATS keyword analysis module."""

from src.ats import _extract_bigrams, _tokenize, analyze, extract_keywords, score_resume


class TestTokenize:
    def test_basic_tokenization(self):
        tokens = _tokenize("Python developer with 5 years experience")
        assert "python" in tokens
        assert "developer" in tokens
        assert "years" in tokens

    def test_removes_stopwords(self):
        tokens = _tokenize("the and or but in on at to")
        assert tokens == []

    def test_minimum_length_filter(self):
        tokens = _tokenize("AI ML go py java")
        # "go" and "py" are 2 chars, filtered; "java" stays
        assert "java" in tokens
        assert "go" not in tokens
        assert "py" not in tokens

    def test_punctuation_stripped(self):
        tokens = _tokenize("Python, JavaScript, and React.js")
        assert "python" in tokens
        assert "javascript" in tokens


class TestExtractBigrams:
    def test_basic_bigrams(self):
        tokens = ["machine", "learning", "engineer"]
        bigrams = _extract_bigrams(tokens)
        assert "machine learning" in bigrams
        assert "learning engineer" in bigrams

    def test_empty_input(self):
        assert _extract_bigrams([]) == []

    def test_single_token(self):
        assert _extract_bigrams(["python"]) == []


class TestExtractKeywords:
    def test_returns_list_of_tuples(self):
        job = "Python developer needed. Python experience required. Python skills important."
        kws = extract_keywords(job, top_n=10)
        assert isinstance(kws, list)
        assert all(isinstance(k, tuple) and len(k) == 2 for k in kws)

    def test_python_appears_in_top_keywords(self):
        job = "Python developer needed. Python experience required. Python skills important."
        kws = extract_keywords(job, top_n=10)
        kw_words = [k for k, _ in kws]
        assert "python" in kw_words

    def test_top_n_respected(self):
        job = " ".join([f"skill{i}" * 3 for i in range(50)])
        kws = extract_keywords(job, top_n=5)
        assert len(kws) <= 5

    def test_empty_text(self):
        kws = extract_keywords("", top_n=10)
        assert kws == []


class TestScoreResume:
    def test_perfect_match(self):
        keywords = [("python", 5), ("django", 3), ("postgres", 2)]
        resume = "I have python django postgres experience."
        result = score_resume(resume, keywords)
        assert result["score"] == 100
        assert result["matched_count"] == 3
        assert result["missing"] == []

    def test_no_match(self):
        keywords = [("java", 5), ("spring", 3)]
        resume = "Python developer with extensive flask experience."
        result = score_resume(resume, keywords)
        assert result["score"] == 0
        assert result["matched_count"] == 0
        assert len(result["missing"]) == 2

    def test_partial_match(self):
        keywords = [("python", 5), ("java", 3), ("sql", 2)]
        resume = "Python developer with SQL database skills."
        result = score_resume(resume, keywords)
        assert result["matched_count"] == 2
        assert result["matched_count"] + len(result["missing"]) == result["total_keywords"]
        assert 0 < result["score"] < 100

    def test_empty_keywords(self):
        result = score_resume("some resume text", [])
        assert result["score"] == 0
        assert result["total_keywords"] == 0

    def test_result_keys_present(self):
        result = score_resume("python developer", [("python", 3)])
        assert "score" in result
        assert "matched" in result
        assert "missing" in result
        assert "total_keywords" in result
        assert "matched_count" in result


class TestAnalyze:
    def test_returns_expected_structure(self):
        resume = "Experienced Python developer with Django and PostgreSQL skills."
        job = "Looking for a Python developer with Django framework experience. Python required. Django preferred."
        result = analyze(resume, job, top_n=10)
        assert "score" in result
        assert "matched" in result
        assert "missing" in result
        assert "keywords" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_score_improves_with_matching_resume(self):
        job = "Python developer needed. Python experience required. Python Django skills."
        weak_resume = "Java developer with Spring Boot background."
        strong_resume = "Python developer with Django experience and Python scripting skills."

        weak_result = analyze(weak_resume, job, top_n=10)
        strong_result = analyze(strong_resume, job, top_n=10)

        assert strong_result["score"] >= weak_result["score"]
