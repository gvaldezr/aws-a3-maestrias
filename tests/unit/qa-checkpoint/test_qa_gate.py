"""Tests unitarios y PBT para qa_gate — U5."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.qa_checkpoint.qa_gate import (
    run_qa_gate,
    validate_bloom_alignment,
    validate_maestria_artifacts,
    validate_ra_coverage,
)


def _subject(ra_ids: list[str], quiz_ra_ids: list[str], program_type: str = "MAESTRIA",
             objectives: list[dict] | None = None, maestria_artifacts: dict | None = None) -> dict:
    return {
        "subject_id": "test-id",
        "metadata": {"program_type": program_type, "subject_name": "Test", "subject_type": "CONCENTRACION"},
        "academic_inputs": {
            "learning_outcomes": [{"ra_id": r, "description": f"RA {r}"} for r in ra_ids],
            "competencies": [{"competency_id": "C1", "description": "Competency"}],
        },
        "instructional_design": {
            "learning_objectives": objectives or [
                {"objective_id": "O1", "bloom_level": "ANALIZAR", "competency_ids": ["C1"], "ra_ids": ra_ids[:1]}
            ],
        },
        "content_package": {
            "quizzes": [{"ra_id": r, "questions": []} for r in quiz_ra_ids],
            "maestria_artifacts": maestria_artifacts,
        },
    }


def _full_maestria_artifacts() -> dict:
    return {
        "evidence_dashboard": {"html_content": "| Paper |"},
        "critical_path_map": {"markdown_content": "| Semana |"},
        "executive_cases_repository": {"cases": [{"title": "Case"}]},
        "facilitator_guide": {"sessions": [{"week": 1}]},
    }


class TestValidateRACoverage:
    def test_full_coverage_passes(self):
        subject = _subject(["RA1", "RA2"], ["RA1", "RA2"])
        result = validate_ra_coverage(subject)
        assert result.is_complete
        assert result.gaps == []

    def test_missing_ra_detected(self):
        subject = _subject(["RA1", "RA2"], ["RA1"])
        result = validate_ra_coverage(subject)
        assert not result.is_complete
        assert "RA2" in result.gaps

    def test_no_quizzes_all_gaps(self):
        subject = _subject(["RA1", "RA2"], [])
        result = validate_ra_coverage(subject)
        assert len(result.gaps) == 2


class TestValidateBloomAlignment:
    def test_aligned_objectives_pass(self):
        subject = _subject(["RA1"], ["RA1"], objectives=[
            {"objective_id": "O1", "bloom_level": "ANALIZAR", "competency_ids": ["C1"], "ra_ids": ["RA1"]}
        ])
        result = validate_bloom_alignment(subject)
        assert result.is_complete

    def test_missing_competency_detected(self):
        subject = _subject(["RA1"], ["RA1"], objectives=[
            {"objective_id": "O1", "bloom_level": "ANALIZAR", "competency_ids": [], "ra_ids": ["RA1"]}
        ])
        result = validate_bloom_alignment(subject)
        assert not result.is_complete
        assert "O1" in result.gaps

    def test_missing_bloom_level_detected(self):
        subject = _subject(["RA1"], ["RA1"], objectives=[
            {"objective_id": "O1", "bloom_level": "", "competency_ids": ["C1"], "ra_ids": ["RA1"]}
        ])
        result = validate_bloom_alignment(subject)
        assert not result.is_complete


class TestValidateMaestriaArtifacts:
    def test_complete_artifacts_pass(self):
        subject = _subject(["RA1"], ["RA1"], maestria_artifacts=_full_maestria_artifacts())
        assert validate_maestria_artifacts(subject) is True

    def test_missing_artifacts_fail(self):
        subject = _subject(["RA1"], ["RA1"], maestria_artifacts=None)
        assert validate_maestria_artifacts(subject) is False

    def test_non_maestria_returns_none(self):
        subject = _subject(["RA1"], ["RA1"], program_type="OTRO")
        assert validate_maestria_artifacts(subject) is None

    def test_empty_cases_fail(self):
        ma = _full_maestria_artifacts()
        ma["executive_cases_repository"]["cases"] = []
        subject = _subject(["RA1"], ["RA1"], maestria_artifacts=ma)
        assert validate_maestria_artifacts(subject) is False


class TestRunQAGate:
    def test_all_pass_returns_pass(self):
        subject = _subject(["RA1"], ["RA1"], maestria_artifacts=_full_maestria_artifacts())
        report = run_qa_gate(subject)
        assert report.overall_status == "PASS"

    def test_ra_gap_returns_fail(self):
        subject = _subject(["RA1", "RA2"], ["RA1"], maestria_artifacts=_full_maestria_artifacts())
        report = run_qa_gate(subject)
        assert report.overall_status == "FAIL"

    def test_report_has_subject_id(self):
        subject = _subject(["RA1"], ["RA1"], maestria_artifacts=_full_maestria_artifacts())
        report = run_qa_gate(subject)
        assert report.subject_id == "test-id"

    def test_idempotent_same_input_same_output(self):
        subject = _subject(["RA1"], ["RA1"], maestria_artifacts=_full_maestria_artifacts())
        r1 = run_qa_gate(subject)
        r2 = run_qa_gate(subject)
        assert r1.overall_status == r2.overall_status
        assert r1.ra_coverage.gaps == r2.ra_coverage.gaps


class TestQAGatePBT:
    @given(
        st.lists(st.text(min_size=2, max_size=5), min_size=1, max_size=8, unique=True),
    )
    @settings(max_examples=20)
    def test_full_coverage_always_passes_ra_check(self, ra_ids: list[str]):
        """PBT-03 invariant: quizzes para todos los RA → ra_coverage.is_complete = True."""
        subject = _subject(ra_ids, ra_ids, program_type="OTRO")
        result = validate_ra_coverage(subject)
        assert result.is_complete

    @given(st.integers(min_value=0, max_value=5))
    @settings(max_examples=20)
    def test_qa_report_status_is_always_pass_or_fail(self, n: int):
        """PBT-03 invariant: overall_status siempre es PASS o FAIL."""
        ra_ids = [f"RA{i}" for i in range(max(n, 1))]
        subject = _subject(ra_ids, ra_ids, program_type="OTRO")
        report = run_qa_gate(subject)
        assert report.overall_status in ("PASS", "FAIL")
