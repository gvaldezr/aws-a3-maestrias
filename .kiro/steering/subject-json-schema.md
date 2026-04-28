---
inclusion: fileMatch
fileMatchPattern: "**/subject*,**/schema*,**/state*,**/qa*,**/checkpoint*,**/publish*"
---

# Subject JSON — Fuente Única de Verdad

## Concepto
Cada asignatura tiene un único JSON en S3 que se enriquece progresivamente por cada agente del pipeline. Es la fuente de verdad para todo el sistema.

## Ubicación
- **S3**: `s3://{bucket}/subjects/{subject_id}/subject.json` (versionado, SSE-KMS)
- **DynamoDB**: Índice de estado con PK=`subject_id`, SK=`STATE`
- **Schema**: Definido en `src/infrastructure/schema/subject_schema_v1.py`

## Estructura principal

```json
{
  "subject_id": "string",
  "schema_version": "1.0",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "metadata": {
    "subject_name": "string (1-255 chars)",
    "program_name": "string",
    "program_type": "MAESTRIA | OTRO",
    "subject_type": "FUNDAMENTOS | CONCENTRACION | PROYECTO",
    "language": "ES | EN | BILINGUAL"
  },
  "academic_inputs": {
    "graduation_profile": "string",
    "competencies": [{"competency_id": "C1", "description": "..."}],
    "learning_outcomes": [{"ra_id": "RA1", "description": "..."}],
    "syllabus": "string"
  },
  "research": {},
  "instructional_design": {},
  "content_package": {},
  "qa_report": {},
  "validation": {},
  "publication": {},
  "pipeline_state": {
    "current_state": "INGESTED",
    "state_history": [{"state": "...", "agent": "...", "timestamp": "...", "result_hash": "..."}]
  }
}
```

## Secciones por agente

| Sección | Escrita por | Estado resultante |
|---------|------------|-------------------|
| `metadata` + `academic_inputs` | Document Parser (Ingesta) | `INGESTED` |
| `research` (top20_papers, knowledge_matrix) | Scholar Agent | `KNOWLEDGE_MATRIX_READY` |
| `instructional_design` (objectives, card, traceability) | DI Agent | `DI_READY` |
| `content_package` (readings, quizzes, forums, maestria) | Content Agent | `CONTENT_READY` |
| `qa_report` | QA Gate Lambda | `PENDING_APPROVAL` o `QA_FAILED` |
| `validation` | Checkpoint Lambda | `APPROVED` o `REJECTED` |
| `publication` | Canvas Publisher | `PUBLISHED` |

## Transiciones de estado válidas

```
INGESTED → KNOWLEDGE_MATRIX_READY | RESEARCH_ESCALATED | FAILED
KNOWLEDGE_MATRIX_READY → DI_READY | DI_ALIGNMENT_GAP | FAILED
DI_READY → CONTENT_READY | CONTENT_QA_FAILED | FAILED
CONTENT_READY → PENDING_APPROVAL | QA_FAILED | FAILED
PENDING_APPROVAL → APPROVED | REJECTED
APPROVED → PUBLISHED | FAILED
REJECTED → CONTENT_READY
```

## Reglas de negocio clave
- **BR-03**: State history es append-only — nunca eliminar entradas
- **BR-04**: Solo transiciones válidas (ver `VALID_STATE_TRANSITIONS`)
- **BR-09**: Validar contra schema antes de persistir (excepto QA report y checkpoint)
- **BR-10**: Siempre actualizar S3 Y DynamoDB en la misma operación
- **State regression guard**: Los agentes verifican que no retroceden el estado (ej: si ya está en `CONTENT_READY`, Scholar no puede volver a `KNOWLEDGE_MATRIX_READY`)
