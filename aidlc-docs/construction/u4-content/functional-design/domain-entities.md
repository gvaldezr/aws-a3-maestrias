# Entidades de Dominio — U4: Agente Content

## ContentPackage
```python
@dataclass
class ContentPackage:
    executive_readings: list[ExecutiveReading]
    masterclass_scripts: list[MasterclassScript]
    quizzes: list[Quiz]
    lab_cases: list[LabCase]
    maestria_artifacts: MaestriaArtifacts | None  # solo para MAESTRIA
    apa_bibliography: list[str]
    language: str  # ES | EN | BILINGUAL
```

## ExecutiveReading
```python
@dataclass
class ExecutiveReading:
    week: int
    title: str
    content_md: str
    language: str
```

## MasterclassScript
```python
@dataclass
class MasterclassScript:
    session: int
    title: str
    script_md: str
    duration_minutes: int
    language: str
```

## Quiz
```python
@dataclass
class Quiz:
    ra_id: str
    questions: list[QuizQuestion]  # mínimo 3 por RA (BR-C03)

@dataclass
class QuizQuestion:
    question: str
    options: list[str]
    correct_answer: int   # índice 0-based
    feedback: str
```

## LabCase
```python
@dataclass
class LabCase:
    title: str
    context: str
    data: str
    questions: list[str]
    rubric: LabRubric

@dataclass
class LabRubric:
    criteria: list[str]
    competency_ids: list[str]
```

## MaestriaArtifacts (RF-05a — todos los programas de Maestría)
```python
@dataclass
class MaestriaArtifacts:
    evidence_dashboard: EvidenceDashboard
    critical_path_map: CriticalPathMap
    executive_cases_repository: ExecutiveCasesRepository
    facilitator_guide: FacilitatorGuide

@dataclass
class EvidenceDashboard:
    html_content: str   # Markdown/HTML con tabla de papers clave

@dataclass
class CriticalPathMap:
    markdown_content: str   # Tabla 3 semanas de trabajo independiente

@dataclass
class ExecutiveCasesRepository:
    cases: list[dict]   # fichas técnicas con contexto, datos, preguntas, rúbrica

@dataclass
class FacilitatorGuide:
    sessions: list[dict]   # minuto a minuto por sesión
```

## CoverageReport
```python
@dataclass
class CoverageReport:
    total_ras: int
    covered_ras: int
    gaps: list[str]   # ra_ids sin cobertura
    is_complete: bool
    retry_count: int
```
