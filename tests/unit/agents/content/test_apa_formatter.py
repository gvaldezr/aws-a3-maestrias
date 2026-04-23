"""Tests unitarios y PBT para apa_formatter — U4."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.content.apa_formatter import format_apa_reference, generate_apa_bibliography


def _paper(title: str = "Test Paper", year: int = 2023, authors: list | None = None) -> dict:
    return {
        "title": title,
        "authors": authors or ["García, J.", "López, M."],
        "year": year,
        "journal": "Journal of Innovation",
        "doi": "10.1234/test",
    }


class TestFormatApaReference:
    def test_includes_year(self):
        ref = format_apa_reference(_paper(year=2023))
        assert "2023" in ref

    def test_includes_title(self):
        ref = format_apa_reference(_paper(title="Machine Learning in Education"))
        assert "Machine Learning in Education" in ref

    def test_includes_doi(self):
        ref = format_apa_reference(_paper())
        assert "https://doi.org/10.1234/test" in ref

    def test_no_doi_still_formats(self):
        paper = _paper()
        paper.pop("doi")
        ref = format_apa_reference(paper)
        assert "Test Paper" in ref
        assert "https://doi.org" not in ref

    def test_single_author(self):
        ref = format_apa_reference(_paper(authors=["Smith, J."]))
        assert "Smith, J." in ref

    def test_returns_string(self):
        assert isinstance(format_apa_reference(_paper()), str)


class TestGenerateApaBibliography:
    def test_returns_list(self):
        result = generate_apa_bibliography([_paper()])
        assert isinstance(result, list)

    def test_sorted_alphabetically(self):
        papers = [_paper("Zebra Study"), _paper("Alpha Research"), _paper("Middle Work")]
        result = generate_apa_bibliography(papers)
        assert result == sorted(result)

    def test_empty_input_returns_empty(self):
        assert generate_apa_bibliography([]) == []

    def test_count_matches_input(self):
        papers = [_paper(f"Paper {i}") for i in range(5)]
        result = generate_apa_bibliography(papers)
        assert len(result) == 5


class TestApaBibliographyPBT:
    @given(st.lists(
        st.fixed_dictionaries({
            "title": st.text(min_size=1, max_size=50),
            "authors": st.lists(st.text(min_size=2, max_size=20), min_size=1, max_size=3),
            "year": st.integers(min_value=2000, max_value=2025),
            "journal": st.text(min_size=1, max_size=30),
        }),
        min_size=0, max_size=20,
    ))
    @settings(max_examples=30)
    def test_bibliography_count_matches_input(self, papers: list[dict]):
        """PBT-02 round-trip: count(output) == count(input)."""
        result = generate_apa_bibliography(papers)
        assert len(result) == len(papers)

    @given(st.lists(
        st.fixed_dictionaries({
            "title": st.text(min_size=1, max_size=50),
            "authors": st.lists(st.text(min_size=2, max_size=20), min_size=1, max_size=3),
            "year": st.integers(min_value=2000, max_value=2025),
            "journal": st.text(min_size=1, max_size=30),
        }),
        min_size=1, max_size=10,
    ))
    @settings(max_examples=30)
    def test_all_results_are_strings(self, papers: list[dict]):
        """PBT-03 invariant: todos los elementos son strings."""
        result = generate_apa_bibliography(papers)
        assert all(isinstance(r, str) for r in result)
