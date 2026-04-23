"""
Cálculo de relevance_score para papers de Scopus.
Función pura — sin efectos secundarios, testeable con PBT.
Invariante: score siempre en [0.0, 1.0].
"""
from __future__ import annotations

from src.agents.scholar.models import Paper

_CURRENT_YEAR = 2025
_RECENT_YEAR_THRESHOLD = 2022


def calculate_relevance_score(paper: Paper, keywords: list[str]) -> float:
    """
    Calcula el relevance_score de un paper dado las keywords de búsqueda.
    Score en [0.0, 1.0] — invariante garantizada.

    Componentes:
    - Coincidencia en título: hasta 0.40
    - Coincidencia en abstract: hasta 0.30
    - Cuartil Q1: +0.20, Q2: +0.10
    - Recencia (año >= 2022): +0.10
    """
    if not keywords:
        return 0.0

    title_lower = paper.title.lower()
    abstract_lower = (paper.abstract or "").lower()
    kw_lower = [k.lower() for k in keywords]

    title_hits = sum(1 for kw in kw_lower if kw in title_lower)
    abstract_hits = sum(1 for kw in kw_lower if kw in abstract_lower)

    title_score = min(title_hits / len(kw_lower), 1.0) * 0.40
    abstract_score = min(abstract_hits / len(kw_lower), 1.0) * 0.30
    quartile_score = 0.20 if paper.quartile == "Q1" else 0.10
    recency_score = 0.10 if paper.year >= _RECENT_YEAR_THRESHOLD else 0.0

    raw = title_score + abstract_score + quartile_score + recency_score
    return round(min(max(raw, 0.0), 1.0), 4)


def rank_and_select_top20(papers: list[Paper], keywords: list[str]) -> list[Paper]:
    """
    Asigna relevance_score a cada paper y retorna los Top 20 ordenados.
    Invariante: len(result) <= 20.
    """
    scored = []
    for paper in papers:
        paper.relevance_score = calculate_relevance_score(paper, keywords)
        scored.append(paper)
    scored.sort(key=lambda p: p.relevance_score, reverse=True)
    return scored[:20]
