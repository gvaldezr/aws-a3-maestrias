"""Tests unitarios y PBT para coverage_checker — U4."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.agents.content.coverage_checker import check_maestria_artifacts_complete, check_ra_coverage
from src.agents.content.models import (
    ContentPackage, CriticalPathMap, EvidenceDashboard,
    ExecutiveCasesRepository, FacilitatorGuide, LabCase, LabRubric,
    MaestriaArtifacts, Quiz, QuizQuestion,
)


def _quiz(ra_id: str) -> Quiz:
    q = QuizQuestion(question="Q?", options=["A", "B", "C", "D"], correct_answer=0, feedback="OK")
    return Quiz(ra_id=ra_id, questions=[q, q, q])


def _lo(ra_id: str) -> dict:
    return {"ra_id": ra_id, "description": f"Resultado {ra_id}"}


def _full_maestria_artifacts() -> MaestriaArtifacts:
    return MaestriaArtifacts(
        evidence_dashboard=EvidenceDashboard(html_content="| Paper |"),
        critical_path_map=CriticalPathMap(markdown_content="| Semana |"),
        executive_cases_repository=ExecutiveCasesRepository(cases=[{"title": "Case 1"}]),
        facilitator_guide=FacilitatorGuide(sessions=[{"week": 1}]),
    )


class TestCheckRACoverage:
    def test_full_coverage_is_complete(self):
        pkg = ContentPackage(quizzes=[_quiz("RA1"), _quiz("RA2")])
        report = check_ra_coverage(pkg, [_lo("RA1"), _lo("RA2")])
        assert report.is_complete
        assert report.gaps == []

    def test_missing_ra_detected(self):
        pkg = ContentPackage(quizzes=[_quiz("RA1")])
        report = check_ra_coverage(pkg, [_lo("RA1"), _lo("RA2")])
        assert not report.is_complete
        assert "RA2" in report.gaps

    def test_empty_package_all_gaps(self):
        pkg = ContentPackage()
        report = check_ra_coverage(pkg, [_lo("RA1"), _lo("RA2")])
        assert not report.is_complete
        assert len(report.gaps) == 2

    def test_coverage_ratio_correct(self):
        pkg = ContentPackage(quizzes=[_quiz("RA1")])
        report = check_ra_coverage(pkg, [_lo("RA1"), _lo("RA2")])
        assert report.coverage_ratio == 0.5

    def test_retry_count_stored(self):
        pkg = ContentPackage(quizzes=[_quiz("RA1")])
        report = check_ra_coverage(pkg, [_lo("RA1")], retry_count=2)
        assert report.retry_count == 2


class TestCheckMaestriaArtifactsComplete:
    def test_complete_artifacts_returns_true(self):
        pkg = ContentPackage(maestria_artifacts=_full_maestria_artifacts())
        assert check_maestria_artifacts_complete(pkg)

    def test_none_artifacts_returns_false(self):
        pkg = ContentPackage()
        assert not check_maestria_artifacts_complete(pkg)

    def test_empty_dashboard_returns_false(self):
        ma = _full_maestria_artifacts()
        ma.evidence_dashboard.html_content = ""
        pkg = ContentPackage(maestria_artifacts=ma)
        assert not check_maestria_artifacts_complete(pkg)

    def test_empty_cases_returns_false(self):
        ma = _full_maestria_artifacts()
        ma.executive_cases_repository.cases = []
        pkg = ContentPackage(maestria_artifacts=ma)
        assert not check_maestria_artifacts_complete(pkg)


class TestCoverageCheckerPBT:
    @given(
        st.integers(min_value=0, max_value=10),
        st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=30)
    def test_coverage_ratio_always_in_0_1(self, covered: int, total: int):
        """PBT-03 invariant: coverage_ratio siempre en [0.0, 1.0]."""
        covered = min(covered, total)
        quizzes = [_quiz(f"RA{i}") for i in range(covered)]
        los = [_lo(f"RA{i}") for i in range(total)]
        pkg = ContentPackage(quizzes=quizzes)
        report = check_ra_coverage(pkg, los)
        assert 0.0 <= report.coverage_ratio <= 1.0

    @given(st.lists(st.text(min_size=2, max_size=5), min_size=1, max_size=8, unique=True))
    @settings(max_examples=20)
    def test_full_quiz_coverage_is_complete(self, ra_ids: list[str]):
        """PBT-03 invariant: quizzes para todos los RA → is_complete = True."""
        quizzes = [_quiz(ra_id) for ra_id in ra_ids]
        los = [_lo(ra_id) for ra_id in ra_ids]
        pkg = ContentPackage(quizzes=quizzes)
        report = check_ra_coverage(pkg, los)
        assert report.is_complete
