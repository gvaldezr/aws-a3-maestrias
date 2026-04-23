"""Tests unitarios y PBT para bloom_mapper — U3."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.di.bloom_mapper import (
    get_bloom_level_for_verb,
    get_preferred_bloom_levels,
    map_objective_to_competencies,
    select_bloom_verb,
    validate_objective_bloom,
)
from src.agents.di.models import BloomLevel, BLOOM_VERBS


class TestGetBloomLevelForVerb:
    def test_analizar_returns_analizar(self):
        assert get_bloom_level_for_verb("analizar") == BloomLevel.ANALIZAR

    def test_evaluar_returns_evaluar(self):
        assert get_bloom_level_for_verb("evaluar") == BloomLevel.EVALUAR

    def test_unknown_verb_returns_none(self):
        assert get_bloom_level_for_verb("conocer") is None

    def test_case_insensitive(self):
        assert get_bloom_level_for_verb("DISEÑAR") == BloomLevel.CREAR

    def test_all_canonical_verbs_are_mapped(self):
        for level, verbs in BLOOM_VERBS.items():
            for verb in verbs:
                assert get_bloom_level_for_verb(verb) == level


class TestGetPreferredBloomLevels:
    def test_fundamentos_returns_lower_levels(self):
        levels = get_preferred_bloom_levels("FUNDAMENTOS")
        assert BloomLevel.RECORDAR in levels or BloomLevel.COMPRENDER in levels

    def test_concentracion_returns_analizar_evaluar(self):
        levels = get_preferred_bloom_levels("CONCENTRACION")
        assert BloomLevel.ANALIZAR in levels
        assert BloomLevel.EVALUAR in levels

    def test_proyecto_returns_evaluar_crear(self):
        levels = get_preferred_bloom_levels("PROYECTO")
        assert BloomLevel.EVALUAR in levels or BloomLevel.CREAR in levels

    def test_unknown_type_returns_default(self):
        levels = get_preferred_bloom_levels("UNKNOWN")
        assert len(levels) >= 1


class TestMapObjectiveToCompetencies:
    def test_matching_keywords_returns_competency(self):
        comps = [{"competency_id": "C1", "description": "Liderazgo estratégico en innovación tecnológica"}]
        result = map_objective_to_competencies("Analizar estrategias de innovación tecnológica", comps)
        assert "C1" in result

    def test_no_match_returns_empty(self):
        comps = [{"competency_id": "C1", "description": "Gestión financiera corporativa"}]
        result = map_objective_to_competencies("Diseñar algoritmos de machine learning", comps)
        assert result == []

    def test_multiple_competencies_can_match(self):
        comps = [
            {"competency_id": "C1", "description": "Analizar sistemas tecnológicos complejos"},
            {"competency_id": "C2", "description": "Evaluar sistemas de información empresarial"},
        ]
        result = map_objective_to_competencies("Analizar sistemas de información tecnológicos", comps)
        assert len(result) >= 1


class TestBloomMapperPBT:
    @given(st.sampled_from(["FUNDAMENTOS", "CONCENTRACION", "PROYECTO"]))
    @settings(max_examples=20)
    def test_preferred_levels_always_non_empty(self, subject_type: str):
        """PBT-03 invariant: siempre retorna al menos un nivel."""
        levels = get_preferred_bloom_levels(subject_type)
        assert len(levels) >= 1

    @given(st.sampled_from(list(BloomLevel)))
    @settings(max_examples=20)
    def test_canonical_verbs_always_map_to_correct_level(self, level: BloomLevel):
        """PBT-03 invariant: verbos canónicos siempre mapean a su nivel correcto."""
        for verb in BLOOM_VERBS[level]:
            assert get_bloom_level_for_verb(verb) == level
