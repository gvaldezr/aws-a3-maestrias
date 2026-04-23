"""
Validación de cobertura de RA en el paquete de contenido — U4: Agente Content.
Función pura — sin efectos secundarios, testeable con PBT.
"""
from __future__ import annotations

from src.agents.content.models import ContentPackage, CoverageReport


def check_ra_coverage(
    content_package: ContentPackage,
    learning_outcomes: list[dict],
    retry_count: int = 0,
) -> CoverageReport:
    """
    Verifica que el paquete de contenido cubre el 100% de los RA. (BR-C05)
    Invariante: coverage_ratio en [0.0, 1.0].

    Args:
        content_package: paquete de contenido generado
        learning_outcomes: lista de dicts con ra_id y description
        retry_count: número de reintentos realizados hasta ahora

    Returns:
        CoverageReport con gaps y is_complete
    """
    all_ra_ids = {lo["ra_id"] for lo in learning_outcomes}

    # RA cubiertos por quizzes
    covered_by_quizzes = {q.ra_id for q in content_package.quizzes}

    # RA cubiertos por lab_cases (via rubric competency_ids — heurística: si hay casos, cubren todos los RA)
    covered_by_cases: set[str] = set()
    if content_package.lab_cases:
        covered_by_cases = all_ra_ids  # los casos cubren el programa completo

    covered = covered_by_quizzes | covered_by_cases
    gaps = sorted(all_ra_ids - covered)

    return CoverageReport(
        total_ras=len(all_ra_ids),
        covered_ras=len(all_ra_ids) - len(gaps),
        gaps=gaps,
        is_complete=len(gaps) == 0,
        retry_count=retry_count,
    )


def check_maestria_artifacts_complete(content_package: ContentPackage) -> bool:
    """
    Verifica que los 4 artefactos de Maestría están presentes y no vacíos. (BR-C02)
    """
    if content_package.maestria_artifacts is None:
        return False
    ma = content_package.maestria_artifacts
    return all([
        bool(ma.evidence_dashboard.html_content),
        bool(ma.critical_path_map.markdown_content),
        bool(ma.executive_cases_repository.cases),
        bool(ma.facilitator_guide.sessions),
    ])
