"""Validación del corpus de papers — U2: Agente Scholar."""
from __future__ import annotations

from src.agents.scholar.models import CorpusValidation, Paper

_MIN_PAPERS = 5


def validate_corpus(
    papers: list[Paper],
    learning_outcomes: list[dict],
) -> CorpusValidation:
    """
    Valida que el corpus tiene suficiente cantidad y cobertura de RA.
    BR-S01: mínimo 5 papers.
    BR-S08: al menos 1 paper cubre el dominio de cada RA.
    """
    if len(papers) < _MIN_PAPERS:
        return CorpusValidation(
            is_sufficient=False,
            paper_count=len(papers),
            min_required=_MIN_PAPERS,
            gaps=[lo["ra_id"] for lo in learning_outcomes],
        )

    # Verificar cobertura temática por RA (heurística: keyword del RA en título/abstract)
    uncovered_ras: list[str] = []
    for lo in learning_outcomes:
        ra_keywords = lo["description"].lower().split()
        covered = any(
            any(kw in (p.title + " " + (p.abstract or "")).lower() for kw in ra_keywords if len(kw) > 4)
            for p in papers
        )
        if not covered:
            uncovered_ras.append(lo["ra_id"])

    return CorpusValidation(
        is_sufficient=len(uncovered_ras) == 0,
        paper_count=len(papers),
        min_required=_MIN_PAPERS,
        gaps=uncovered_ras,
    )
