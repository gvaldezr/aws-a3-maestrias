"""
Lógica de mapeo Bloom–Competencias — U3: Agente DI.
Funciones puras para validación y asignación de niveles Bloom.
"""
from __future__ import annotations

from src.agents.di.models import BloomLevel, BLOOM_VERBS, SUBJECT_TYPE_BLOOM_MAP


def get_bloom_level_for_verb(verb: str) -> BloomLevel | None:
    """
    Retorna el BloomLevel correspondiente a un verbo dado.
    Retorna None si el verbo no está en ningún nivel.
    Búsqueda case-insensitive.
    """
    verb_lower = verb.lower().strip()
    for level, verbs in BLOOM_VERBS.items():
        if verb_lower in verbs:
            return level
    return None


def get_preferred_bloom_levels(subject_type: str) -> list[BloomLevel]:
    """
    Retorna los niveles Bloom preferidos para un tipo de materia (BR-DI04).
    Retorna [ANALIZAR, EVALUAR] como default si el tipo no está mapeado.
    """
    return SUBJECT_TYPE_BLOOM_MAP.get(subject_type, [BloomLevel.ANALIZAR, BloomLevel.EVALUAR])


def select_bloom_verb(subject_type: str, index: int = 0) -> tuple[str, BloomLevel]:
    """
    Selecciona un verbo Bloom apropiado para el tipo de materia.
    Retorna (verbo, nivel).
    """
    levels = get_preferred_bloom_levels(subject_type)
    level = levels[index % len(levels)]
    verbs = BLOOM_VERBS[level]
    verb = verbs[index % len(verbs)]
    return verb, level


def validate_objective_bloom(verb: str, bloom_level: BloomLevel) -> bool:
    """
    Valida que el verbo corresponde al nivel Bloom declarado.
    Retorna True si son consistentes.
    """
    expected_level = get_bloom_level_for_verb(verb)
    return expected_level == bloom_level


def map_objective_to_competencies(
    objective_description: str,
    competencies: list[dict],
) -> list[str]:
    """
    Mapea un objetivo a competencias por afinidad semántica de keywords.
    Retorna lista de competency_ids (puede ser vacía si no hay match → AlignmentGap).
    """
    obj_words = set(objective_description.lower().split())
    matched_ids: list[str] = []

    for comp in competencies:
        comp_words = set(comp["description"].lower().split())
        # Intersección de palabras significativas (longitud > 4)
        overlap = {w for w in obj_words & comp_words if len(w) > 4}
        if overlap:
            matched_ids.append(comp["competency_id"])

    return matched_ids
