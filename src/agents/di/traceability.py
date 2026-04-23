"""
Construcción y validación de la matriz de trazabilidad Bloom–Competencias.
Funciones puras — U3: Agente DI.
"""
from __future__ import annotations

from src.agents.di.models import AlignmentGap, LearningObjective, TraceabilityEntry


def build_traceability_matrix(
    objectives: list[LearningObjective],
    learning_outcomes: list[dict],
) -> list[TraceabilityEntry]:
    """
    Construye la matriz de trazabilidad objetivo → Bloom → competencia(s) → RA.
    Una entrada por cada par (objetivo, RA). (BR-DI07)
    """
    entries: list[TraceabilityEntry] = []
    for obj in objectives:
        for ra_id in obj.ra_ids:
            entries.append(TraceabilityEntry(
                objective_id=obj.objective_id,
                bloom_level=obj.bloom_level.value,
                competency_ids=obj.competency_ids,
                ra_id=ra_id,
            ))
    return entries


def validate_ra_coverage(
    objectives: list[LearningObjective],
    learning_outcomes: list[dict],
) -> list[str]:
    """
    Verifica que todos los RA tienen al menos un objetivo asociado. (BR-DI03)
    Retorna lista de ra_ids sin cobertura (vacía si cobertura 100%).
    """
    covered_ras: set[str] = set()
    for obj in objectives:
        covered_ras.update(obj.ra_ids)

    all_ras = {lo["ra_id"] for lo in learning_outcomes}
    return sorted(all_ras - covered_ras)


def detect_alignment_gaps(
    objectives: list[LearningObjective],
) -> list[AlignmentGap]:
    """
    Detecta objetivos sin competencia asociada. (BR-DI02, BR-DI06)
    Retorna lista de AlignmentGap (vacía si todos los objetivos tienen competencias).
    """
    gaps: list[AlignmentGap] = []
    for obj in objectives:
        if not obj.competency_ids:
            gaps.append(AlignmentGap(
                objective_id=obj.objective_id,
                description=obj.description,
                ra_ids=obj.ra_ids,
                reason="No se encontró competencia del programa con afinidad semántica suficiente",
            ))
    return gaps


def coverage_ratio(
    objectives: list[LearningObjective],
    learning_outcomes: list[dict],
) -> float:
    """
    Calcula el ratio de cobertura de RA: covered / total.
    Invariante: resultado en [0.0, 1.0].
    """
    if not learning_outcomes:
        return 1.0
    uncovered = validate_ra_coverage(objectives, learning_outcomes)
    covered = len(learning_outcomes) - len(uncovered)
    return round(covered / len(learning_outcomes), 4)
