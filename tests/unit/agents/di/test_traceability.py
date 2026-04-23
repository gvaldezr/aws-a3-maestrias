"""Tests unitarios y PBT para traceability — U3."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.di.models import BloomLevel, LearningObjective
from src.agents.di.traceability import (
    build_traceability_matrix,
    coverage_ratio,
    detect_alignment_gaps,
    validate_ra_coverage,
)


def _obj(obj_id: str, ra_ids: list[str], competency_ids: list[str] | None = None) -> LearningObjective:
    return LearningObjective(
        objective_id=obj_id,
        description=f"Objetivo {obj_id}",
        bloom_verb="analizar",
        bloom_level=BloomLevel.ANALIZAR,
        competency_ids=competency_ids if competency_ids is not None else ["C1"],
        ra_ids=ra_ids,
    )


def _lo(ra_id: str) -> dict:
    return {"ra_id": ra_id, "description": f"Resultado {ra_id}"}


class TestBuildTraceabilityMatrix:
    def test_one_entry_per_objective_ra_pair(self):
        objs = [_obj("O1", ["RA1", "RA2"])]
        matrix = build_traceability_matrix(objs, [_lo("RA1"), _lo("RA2")])
        assert len(matrix) == 2

    def test_entry_has_correct_fields(self):
        objs = [_obj("O1", ["RA1"], ["C1", "C2"])]
        matrix = build_traceability_matrix(objs, [_lo("RA1")])
        assert matrix[0].objective_id == "O1"
        assert matrix[0].ra_id == "RA1"
        assert "C1" in matrix[0].competency_ids

    def test_empty_objectives_returns_empty_matrix(self):
        assert build_traceability_matrix([], [_lo("RA1")]) == []


class TestValidateRACoverage:
    def test_all_covered_returns_empty(self):
        objs = [_obj("O1", ["RA1"]), _obj("O2", ["RA2"])]
        gaps = validate_ra_coverage(objs, [_lo("RA1"), _lo("RA2")])
        assert gaps == []

    def test_uncovered_ra_returned(self):
        objs = [_obj("O1", ["RA1"])]
        gaps = validate_ra_coverage(objs, [_lo("RA1"), _lo("RA2")])
        assert "RA2" in gaps

    def test_empty_objectives_all_ras_uncovered(self):
        gaps = validate_ra_coverage([], [_lo("RA1"), _lo("RA2")])
        assert set(gaps) == {"RA1", "RA2"}


class TestDetectAlignmentGaps:
    def test_no_gaps_when_all_have_competencies(self):
        objs = [_obj("O1", ["RA1"], ["C1"])]
        assert detect_alignment_gaps(objs) == []

    def test_gap_detected_when_no_competencies(self):
        objs = [_obj("O1", ["RA1"], [])]
        gaps = detect_alignment_gaps(objs)
        assert len(gaps) == 1
        assert gaps[0].objective_id == "O1"


class TestCoverageRatioPBT:
    @given(
        st.integers(min_value=0, max_value=10),
        st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30)
    def test_coverage_ratio_always_in_0_1(self, covered: int, total: int):
        """PBT-03 invariant: coverage_ratio siempre en [0.0, 1.0]."""
        covered = min(covered, total)
        objs = [_obj(f"O{i}", [f"RA{i}"]) for i in range(covered)]
        los = [_lo(f"RA{i}") for i in range(total)]
        ratio = coverage_ratio(objs, los)
        assert 0.0 <= ratio <= 1.0

    @given(st.lists(st.text(min_size=2, max_size=5), min_size=1, max_size=8, unique=True))
    @settings(max_examples=20)
    def test_full_coverage_returns_1(self, ra_ids: list[str]):
        """PBT-03 invariant: cobertura total siempre retorna 1.0."""
        objs = [_obj(f"O{i}", [ra_id]) for i, ra_id in enumerate(ra_ids)]
        los = [_lo(ra_id) for ra_id in ra_ids]
        assert coverage_ratio(objs, los) == 1.0
