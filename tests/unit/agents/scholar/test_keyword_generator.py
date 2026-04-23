"""Tests unitarios y PBT para keyword_generator — U2."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.scholar.keyword_generator import generate_search_keywords


def _lo(desc: str) -> dict:
    return {"ra_id": "RA1", "description": desc}


def _comp(desc: str) -> dict:
    return {"competency_id": "C1", "description": desc}


class TestGenerateSearchKeywords:
    def test_returns_list(self):
        result = generate_search_keywords([_lo("Analizar tendencias tecnológicas")], [_comp("Liderazgo estratégico")])
        assert isinstance(result, list)

    def test_max_10_keywords(self):
        los = [_lo(f"Resultado de aprendizaje número {i} sobre innovación tecnológica digital") for i in range(10)]
        result = generate_search_keywords(los, [])
        assert len(result) <= 10

    def test_no_stopwords_in_result(self):
        result = generate_search_keywords([_lo("el análisis de los sistemas")], [])
        stopwords = {"el", "de", "los", "la", "en", "y", "que"}
        assert not any(kw in stopwords for kw in result)

    def test_empty_inputs_returns_empty(self):
        result = generate_search_keywords([], [])
        assert result == []

    def test_keywords_min_length_4(self):
        result = generate_search_keywords([_lo("big data analytics platform")], [])
        assert all(len(kw) >= 4 for kw in result)

    def test_keywords_are_lowercase(self):
        result = generate_search_keywords([_lo("Machine Learning Innovation")], [])
        assert all(kw == kw.lower() for kw in result)


class TestKeywordGeneratorPBT:
    @given(
        st.lists(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Zs"))), min_size=1, max_size=5),
        st.lists(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Zs"))), min_size=0, max_size=3),
    )
    @settings(max_examples=30)
    def test_result_never_exceeds_10_keywords(self, lo_descs: list[str], comp_descs: list[str]):
        """PBT-03 invariant: resultado siempre <= 10 keywords."""
        los = [{"ra_id": "RA1", "description": d} for d in lo_descs]
        comps = [{"competency_id": "C1", "description": d} for d in comp_descs]
        result = generate_search_keywords(los, comps)
        assert len(result) <= 10

    @given(
        st.lists(st.text(min_size=5, max_size=50), min_size=1, max_size=3),
    )
    @settings(max_examples=30)
    def test_all_keywords_are_strings(self, lo_descs: list[str]):
        """PBT-03 invariant: todos los elementos son strings."""
        los = [{"ra_id": "RA1", "description": d} for d in lo_descs]
        result = generate_search_keywords(los, [])
        assert all(isinstance(kw, str) for kw in result)
