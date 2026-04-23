# Entidades de Dominio — U3: Agente DI

## BloomLevel (enum)
```python
class BloomLevel(str, Enum):
    RECORDAR = "RECORDAR"
    COMPRENDER = "COMPRENDER"
    APLICAR = "APLICAR"
    ANALIZAR = "ANALIZAR"
    EVALUAR = "EVALUAR"
    CREAR = "CREAR"
```

## LearningObjective
```python
@dataclass
class LearningObjective:
    objective_id: str
    description: str
    bloom_verb: str
    bloom_level: BloomLevel
    competency_ids: list[str]   # mínimo 1 (BR-DI02)
    ra_ids: list[str]           # mínimo 1
```

## TraceabilityEntry
```python
@dataclass
class TraceabilityEntry:
    objective_id: str
    bloom_level: str
    competency_ids: list[str]
    ra_id: str
```

## ContentMap
```python
@dataclass
class ContentMap:
    weeks: list[WeekPlan]       # 4 semanas

@dataclass
class WeekPlan:
    week: int                   # 1–4
    theme: str
    bloom_level: BloomLevel
    activities: list[str]
```

## DescriptiveCard
```python
@dataclass
class DescriptiveCard:
    version: str                # "V1"
    general_objective: str
    specific_objectives: list[str]
    weekly_map: str             # Markdown
    case_studies_design: str
    evaluation_criteria: str
```

## AlignmentGap
```python
@dataclass
class AlignmentGap:
    objective_id: str
    description: str
    ra_ids: list[str]
    reason: str                 # por qué no se pudo mapear a competencia
```

## DIResult
```python
@dataclass
class DIResult:
    subject_id: str
    content_map: ContentMap
    learning_objectives: list[LearningObjective]
    traceability_matrix: list[TraceabilityEntry]
    descriptive_card: DescriptiveCard
    alignment_gaps: list[AlignmentGap]
```
