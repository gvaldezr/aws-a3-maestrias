"""Tests unitarios y PBT para relevance_scorer — U2."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.scholar.models import Paper
from src.agents.scholar.relevance_scorer import calculate_relevance_score, rank_and_select_top20


def _paper(title: str = "Test Paper", year: int = 2023, quartile: str = "Q1", abstract: str = "") -> Paper:
    return Paper(
        scopus_id="S1", title=title, authors=["Author A"],
        year=year, journal="Test Journal", quartile=quartile,
        key_finding="Key finding", abstract=abstract,
    )


class TestCalculateRelevanceScore:
    def test_score_in_range_0_to_1(self):
        paper = _paper("Machine Learning Innovation", 2023, "Q1", "deep learning neural networks")
        score = calculate_relevance_score(paper, ["machine", "learning", "innovation"])
        assert 0.0 <= score <= 1.0

    def test_q1_scores_higher_than_q2_same_paper(self):
        keywords = ["innovation", "technology"]
        q1 = _paper("Innovation Technology", 2023, "Q1")
        q2 = _paper("Innovation Technology", 2023, "Q2")
        assert calculate_relevance_score(q1, keywords) > calculate_relevance_score(q2, keywords)

    def test_recent_paper_scores_higher(self):
        keywords = ["innovation"]
        recent = _paper("Innovation Study", 2023, "Q1")
        old = _paper("Innovation Study", 2018, "Q1")
        assert calculate_relevance_score(recent, keywords) > calculate_relevance_score(old, keywords)

    def test_empty_keywords_returns_zero(self):
        paper = _paper("Machine Learning")
        assert calculate_relevance_score(paper, []) == 0.0

    def test_title_match_increases_score(self):
        keywords = ["blockchain"]
        with_match = _paper("Blockchain Technology Review", 2023, "Q2")
        without_match = _paper("Unrelated Topic Study", 2023, "Q2")
        assert calculate_relevance_score(with_match, keywords) > calculate_relevance_score(without_match, keywords)


class TestRankAndSelectTop20:
    def test_returns_at_most_20_papers(self):
        papers = [_paper(f"Paper {i}", 2023, "Q1") for i in range(30)]
        result = rank_and_select_top20(papers, ["innovation"])
        assert len(result) <= 20

    def test_returns_all_if_less_than_20(self):
        papers = [_paper(f"Paper {i}") for i in range(5)]
        result = rank_and_select_top20(papers, ["innovation"])
        assert len(result) == 5

    def test_sorted_by_score_descending(self):
        keywords = ["machine", "learning"]
        papers = [
            _paper("Unrelated Topic", 2020, "Q2"),
            _paper("Machine Learning Deep", 2023, "Q1", "machine learning neural"),
            _paper("Machine Study", 2022, "Q1"),
        ]
        result = rank_and_select_top20(papers, keywords)
        scores = [p.relevance_score for p in result]
        assert scores == sorted(scores, reverse=True)


class TestRelevanceScorerPBT:
    @given(
        st.text(min_size=1, max_size=200),
        st.integers(min_value=2000, max_value=2025),
        st.sampled_from(["Q1", "Q2"]),
        st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=10),
    )
    @settings(max_examples=50)
    def test_score_always_in_0_1_range(self, title: str, year: int, quartile: str, keywords: list[str]):
        """PBT-03 invariant: score siempre en [0.0, 1.0]."""
        paper = _paper(title, year, quartile)
        score = calculate_relevance_score(paper, keywords)
        assert 0.0 <= score <= 1.0, f"Score fuera de rango: {score}"

    @given(st.lists(
        st.builds(lambda t, y: _paper(t, y, "Q1"), st.text(min_size=1, max_size=50), st.integers(2019, 2025)),
        min_size=0, max_size=30,
    ))
    @settings(max_examples=30)
    def test_top20_never_exceeds_20(self, papers: list[Paper]):
        """PBT-03 invariant: rank_and_select_top20 nunca retorna más de 20."""
        result = rank_and_select_top20(papers, ["innovation"])
        assert len(result) <= 20
