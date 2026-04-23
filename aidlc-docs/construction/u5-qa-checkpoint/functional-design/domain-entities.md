# Entidades de Dominio — U5: QA Gate + Checkpoint Humano

## QAReport
```python
@dataclass
class QAReport:
    subject_id: str
    ra_coverage: RACoverageResult
    bloom_alignment: BloomAlignmentResult
    maestria_artifacts_present: bool | None   # None si no es Maestría
    overall_status: str   # "PASS" | "FAIL"
    validated_at: str     # ISO-8601
    retry_count: int

@dataclass
class RACoverageResult:
    total_ras: int
    covered_ras: int
    gaps: list[str]       # ra_ids sin cobertura

@dataclass
class BloomAlignmentResult:
    total_objectives: int
    aligned_objectives: int
    gaps: list[str]       # objective_ids sin competencia
```

## ValidationDecision
```python
@dataclass
class ValidationDecision:
    subject_id: str
    decision: str         # "APPROVED" | "REJECTED"
    decided_by: str       # username del Staff
    decided_at: str       # ISO-8601
    comments: str         # obligatorio si REJECTED
    manual_edits: list[dict]   # ediciones manuales si aplica
```

## CheckpointSummary
```python
@dataclass
class CheckpointSummary:
    subject_id: str
    subject_name: str
    program_name: str
    qa_report: QAReport
    descriptive_card_preview: str   # resumen de la Carta Descriptiva
    content_preview: dict           # conteo de recursos generados
    maestria_artifacts_present: bool
    pending_since: str              # ISO-8601
    timeout_at: str                 # ISO-8601 (pending_since + 48h)
```
