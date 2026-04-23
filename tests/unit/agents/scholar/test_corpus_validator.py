"""Tests unitarios y PBT para corpus_validator — U2."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.scholar.corpus_validator import validate_corpus
from src.agents.scholar.models import Paper


def _paper(title: str = "Test Paper") -> Paper:
    return Paper(
        scopus_id="S1", title=title, authors=["A"],
        year=2023, journal="J", quartile="Q1", key_finding="KF",
    )


def _lo(ra_id: str, desc: str) -> dict:
    return {"ra_id": ra_id, "description": desc}


class TestValidateCorpus:
    def test_insufficient_when_less_than_5_papers(self):
        papers = [_paper() for _ in range(3)]
        result = validate_corpus(papers, [_lo("RA1", "machine learning")])
        assert not result.is_sufficient
        assert result.paper_count == 3

    def test_sufficient_with_5_or_more_papers(self):
        papers = [_paper(f"Machine Learning Paper {i}") for i in range(5)]
        los = [_lo("RA1", "machine learning")]
        result = validate_corpus(papers, los)
        assert result.is_sufficient
        assert result.paper_count == 5

    def test_gaps_populated_when_insufficient(self):
        papers = [_paper() for _ in range(2)]
        los = [_lo("RA1", "blockchain"), _lo("RA2", "innovation")]
        result = validate_corpus(papers, los)
        assert "RA1" in result.gaps
        assert "RA2" in result.gaps

    def test_empty_papers_returns_insufficient(self):
        result = validate_corpus([], [_lo("RA1", "machine learning")])
        assert not result.is_sufficient
        assert result.paper_count == 0


class TestCorpusValidatorPBT:
    @given(st.integers(min_value=0, max_value=4))
    @settings(max_examples=20)
    def test_less_than_5_papers_always_insufficient(self, count: int):
        """PBT-03 invariant: < 5 papers siempre es insuficiente."""
        papers = [_paper() for _ in range(count)]
        result = validate_corpus(papers, [_lo("RA1", "test topic")])
        assert not result.is_sufficient

    @given(st.integers(min_value=5, max_value=20))
    @settings(max_examples=20)
    def test_paper_count_matches_input(self, count: int):
        """PBT-03 invariant: paper_count siempre refleja el input."""
        papers = [_paper(f"Machine Learning Paper {i}") for i in range(count)]
        result = validate_corpus(papers, [_lo("RA1", "machine learning")])
        assert result.paper_count == count
