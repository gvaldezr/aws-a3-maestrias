"""Modelos de dominio — U4: Agente Content."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuizQuestion:
    question: str
    options: list[str]
    correct_answer: int  # índice 0-based
    feedback: str

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "feedback": self.feedback,
        }


@dataclass
class Quiz:
    ra_id: str
    questions: list[QuizQuestion]

    def to_dict(self) -> dict:
        return {"ra_id": self.ra_id, "questions": [q.to_dict() for q in self.questions]}


@dataclass
class LabRubric:
    criteria: list[str]
    competency_ids: list[str]

    def to_dict(self) -> dict:
        return {"criteria": self.criteria, "competency_ids": self.competency_ids}


@dataclass
class LabCase:
    title: str
    context: str
    data: str
    questions: list[str]
    rubric: LabRubric

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "context": self.context,
            "data": self.data,
            "questions": self.questions,
            "rubric": self.rubric.to_dict(),
        }


@dataclass
class ExecutiveReading:
    week: int
    title: str
    content_md: str
    language: str

    def to_dict(self) -> dict:
        return {"week": self.week, "title": self.title, "content_md": self.content_md, "language": self.language}


@dataclass
class MasterclassScript:
    session: int
    title: str
    script_md: str
    duration_minutes: int
    language: str

    def to_dict(self) -> dict:
        return {
            "session": self.session, "title": self.title,
            "script_md": self.script_md, "duration_minutes": self.duration_minutes,
            "language": self.language,
        }


@dataclass
class EvidenceDashboard:
    html_content: str

    def to_dict(self) -> dict:
        return {"html_content": self.html_content}


@dataclass
class CriticalPathMap:
    markdown_content: str

    def to_dict(self) -> dict:
        return {"markdown_content": self.markdown_content}


@dataclass
class ExecutiveCasesRepository:
    cases: list[dict]

    def to_dict(self) -> dict:
        return {"cases": self.cases}


@dataclass
class FacilitatorGuide:
    sessions: list[dict]

    def to_dict(self) -> dict:
        return {"sessions": self.sessions}


@dataclass
class MaestriaArtifacts:
    evidence_dashboard: EvidenceDashboard
    critical_path_map: CriticalPathMap
    executive_cases_repository: ExecutiveCasesRepository
    facilitator_guide: FacilitatorGuide

    def to_dict(self) -> dict:
        return {
            "evidence_dashboard": self.evidence_dashboard.to_dict(),
            "critical_path_map": self.critical_path_map.to_dict(),
            "executive_cases_repository": self.executive_cases_repository.to_dict(),
            "facilitator_guide": self.facilitator_guide.to_dict(),
        }


@dataclass
class ContentPackage:
    executive_readings: list[ExecutiveReading] = field(default_factory=list)
    masterclass_scripts: list[MasterclassScript] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)
    lab_cases: list[LabCase] = field(default_factory=list)
    maestria_artifacts: MaestriaArtifacts | None = None
    apa_bibliography: list[str] = field(default_factory=list)
    language: str = "ES"

    def to_dict(self) -> dict:
        return {
            "executive_readings": [r.to_dict() for r in self.executive_readings],
            "masterclass_scripts": [s.to_dict() for s in self.masterclass_scripts],
            "quizzes": [q.to_dict() for q in self.quizzes],
            "lab_cases": [c.to_dict() for c in self.lab_cases],
            "maestria_artifacts": self.maestria_artifacts.to_dict() if self.maestria_artifacts else None,
            "apa_bibliography": self.apa_bibliography,
        }


@dataclass
class CoverageReport:
    total_ras: int
    covered_ras: int
    gaps: list[str]
    is_complete: bool
    retry_count: int = 0

    @property
    def coverage_ratio(self) -> float:
        """Ratio de cobertura en [0.0, 1.0]. Invariante PBT-03."""
        if self.total_ras == 0:
            return 1.0
        return round(self.covered_ras / self.total_ras, 4)
