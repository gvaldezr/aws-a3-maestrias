"""
Construcción de la Carta Descriptiva V1 — U3: Agente DI.
Genera el documento estructurado a partir de objetivos y mapa de contenidos.
"""
from __future__ import annotations

from src.agents.di.models import BloomLevel, ContentMap, DescriptiveCard, LearningObjective, WeekPlan
from src.agents.di.bloom_mapper import get_preferred_bloom_levels

_WEEK_THEMES = ["Ingesta y Fundamentos", "Análisis y Aplicación", "Evaluación Crítica", "Síntesis e Integración"]


def build_content_map(subject_type: str, knowledge_matrix: list[dict]) -> ContentMap:
    """
    Construye el mapa de 4 semanas con progresión Ingesta → Síntesis. (BR-DI05)
    Asigna nivel Bloom por semana según el tipo de materia.
    """
    preferred_levels = get_preferred_bloom_levels(subject_type)
    # Distribuir niveles Bloom a lo largo de las 4 semanas
    bloom_progression = [
        BloomLevel.RECORDAR,
        BloomLevel.APLICAR,
        preferred_levels[0],
        preferred_levels[-1],
    ]

    weeks: list[WeekPlan] = []
    for i in range(4):
        # Asignar entradas de la matriz de conocimiento a la semana
        week_entries = knowledge_matrix[i::4] if knowledge_matrix else []
        activities = [e.get("executive_application", e.get("concept", "")) for e in week_entries[:3]]
        if not activities:
            activities = [f"Actividad de {_WEEK_THEMES[i]}"]

        weeks.append(WeekPlan(
            week=i + 1,
            theme=_WEEK_THEMES[i],
            bloom_level=bloom_progression[i],
            activities=activities,
        ))

    return ContentMap(weeks=weeks)


def build_weekly_map_markdown(content_map: ContentMap) -> str:
    """Genera el mapa semanal en formato Markdown (tabla)."""
    lines = [
        "| Semana | Tema | Nivel Bloom | Actividades |",
        "|--------|------|-------------|-------------|",
    ]
    for week in content_map.weeks:
        activities_str = "; ".join(week.activities[:2])
        lines.append(f"| {week.week} | {week.theme} | {week.bloom_level.value} | {activities_str} |")
    return "\n".join(lines)


def draft_descriptive_card(
    content_map: ContentMap,
    objectives: list[LearningObjective],
    subject_name: str,
    graduation_profile: str,
) -> DescriptiveCard:
    """
    Redacta la Carta Descriptiva V1 a partir del mapa de contenidos y objetivos.
    """
    # Objetivo general: síntesis del objetivo de mayor nivel Bloom
    top_objectives = sorted(objectives, key=lambda o: list(BloomLevel).index(o.bloom_level), reverse=True)
    general_objective = (
        top_objectives[0].description if top_objectives
        else f"Desarrollar competencias profesionales en {subject_name}"
    )

    specific_objectives = [obj.description for obj in objectives[:6]]  # máx 6 específicos
    weekly_map = build_weekly_map_markdown(content_map)

    case_studies = (
        f"Casos ejecutivos diseñados para vincular los contenidos de {subject_name} "
        f"con la práctica profesional del egresado: {graduation_profile[:100]}..."
    )
    evaluation_criteria = (
        "Evaluación basada en competencias: "
        + "; ".join(f"Competencia {obj.competency_ids[0]}: {obj.bloom_level.value}" for obj in objectives[:3] if obj.competency_ids)
    )

    return DescriptiveCard(
        version="V1",
        general_objective=general_objective,
        specific_objectives=specific_objectives,
        weekly_map=weekly_map,
        case_studies_design=case_studies,
        evaluation_criteria=evaluation_criteria,
    )
