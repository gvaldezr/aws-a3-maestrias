"""Modelos de dominio — U3: Agente DI."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BloomLevel(str, Enum):
    RECORDAR = "RECORDAR"
    COMPRENDER = "COMPRENDER"
    APLICAR = "APLICAR"
    ANALIZAR = "ANALIZAR"
    EVALUAR = "EVALUAR"
    CREAR = "CREAR"


# Verbos canónicos por nivel Bloom (para validación y generación)
BLOOM_VERBS: dict[BloomLevel, list[str]] = {
    BloomLevel.RECORDAR:   ["identificar", "listar", "nombrar", "reconocer", "definir", "recordar"],
    BloomLevel.COMPRENDER: ["explicar", "describir", "resumir", "interpretar", "clasificar", "comparar"],
    BloomLevel.APLICAR:    ["aplicar", "demostrar", "ejecutar", "implementar", "resolver", "usar"],
    BloomLevel.ANALIZAR:   ["analizar", "diferenciar", "examinar", "descomponer", "relacionar", "distinguir"],
    BloomLevel.EVALUAR:    ["evaluar", "justificar", "criticar", "valorar", "argumentar", "defender"],
    BloomLevel.CREAR:      ["diseñar", "construir", "formular", "proponer", "desarrollar", "crear"],
}

# Nivel Bloom predominante por tipo de materia (BR-DI04)
SUBJECT_TYPE_BLOOM_MAP: dict[str, list[BloomLevel]] = {
    "FUNDAMENTOS":    [BloomLevel.RECORDAR, BloomLevel.COMPRENDER, BloomLevel.APLICAR],
    "CONCENTRACION":  [BloomLevel.ANALIZAR, BloomLevel.EVALUAR],
    "PROYECTO":       [BloomLevel.EVALUAR, BloomLevel.CREAR],
}


@dataclass
class LearningObjective:
    objective_id: str
    description: str
    bloom_verb: str
    bloom_level: BloomLevel
    competency_ids: list[str]
    ra_ids: list[str]

    def to_dict(self) -> dict:
        return {
            "objective_id": self.objective_id,
            "description": self.description,
            "bloom_verb": self.bloom_verb,
            "bloom_level": self.bloom_level.value,
            "competency_ids": self.competency_ids,
            "ra_ids": self.ra_ids,
        }


@dataclass
class TraceabilityEntry:
    objective_id: str
    bloom_level: str
    competency_ids: list[str]
    ra_id: str

    def to_dict(self) -> dict:
        return {
            "objective_id": self.objective_id,
            "bloom_level": self.bloom_level,
            "competency_ids": self.competency_ids,
            "ra_id": self.ra_id,
        }


@dataclass
class WeekPlan:
    week: int
    theme: str
    bloom_level: BloomLevel
    activities: list[str]


@dataclass
class ContentMap:
    weeks: list[WeekPlan]


@dataclass
class DescriptiveCard:
    version: str
    general_objective: str
    specific_objectives: list[str]
    weekly_map: str
    case_studies_design: str
    evaluation_criteria: str

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "general_objective": self.general_objective,
            "specific_objectives": self.specific_objectives,
            "weekly_map": self.weekly_map,
            "case_studies_design": self.case_studies_design,
            "evaluation_criteria": self.evaluation_criteria,
        }


@dataclass
class AlignmentGap:
    objective_id: str
    description: str
    ra_ids: list[str]
    reason: str


@dataclass
class DIResult:
    subject_id: str
    content_map: ContentMap
    learning_objectives: list[LearningObjective]
    traceability_matrix: list[TraceabilityEntry]
    descriptive_card: DescriptiveCard
    alignment_gaps: list[AlignmentGap] = field(default_factory=list)
