# Arquitectura del Sistema

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PRESENTACIÓN                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  Login Page   │  │  Dashboard   │  │  Checkpoint Page      │  │
│  │  (Cognito)    │  │  (Subjects)  │  │  (6 tabs: Resumen,    │  │
│  │              │  │  (Upload)    │  │   Objetivos, Lecturas, │  │
│  │              │  │  (Status)    │  │   Quizzes, Papers,     │  │
│  │              │  │              │  │   Maestría)            │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                     React + TypeScript + Vite                    │
│                     S3 Static Website Hosting                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
          ┌─────────────────┐  ┌─────────────────┐
          │  Web API Gateway │  │Checkpoint API GW│
          │  /api/upload     │  │/subjects/{id}/   │
          │  /api/subjects   │  │  checkpoint      │
          │  Cognito Auth    │  │  decision        │
          │  CORS enabled    │  │  Cognito Auth    │
          └────────┬────────┘  └────────┬────────┘
                   │                    │
┌──────────────────┴────────────────────┴──────────────────────────┐
│                     CAPA DE APLICACIÓN                           │
│                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Upload    │ │ Ingestion  │ │ Dashboard  │ │  Checkpoint  │  │
│  │  Handler   │ │ Handler    │ │ Handler    │ │  Handler     │  │
│  │ (presigned │ │ (parse     │ │ (DynamoDB  │ │ (approve/    │  │
│  │  URL)      │ │  DOCX →    │ │  scan)     │ │  reject/     │  │
│  │           │ │  JSON →    │ │           │ │  edit)       │  │
│  │           │ │  StepFn)   │ │           │ │ → Canvas Pub │  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              Step Functions Orchestrator                  │    │
│  │                                                          │    │
│  │  WarmUp → Scholar → PersistScholar → DI → PersistDI     │    │
│  │  → Content → PersistContent → QA Gate → STOP            │    │
│  │                                                          │    │
│  │  (Pipeline se pausa en PENDING_APPROVAL)                 │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              AgentCore Runtimes (3 microVMs)             │    │
│  │                                                          │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │    │
│  │  │ Scholar  │  │   DI     │  │ Content  │              │    │
│  │  │ Agent    │  │  Agent   │  │  Agent   │              │    │
│  │  │          │  │          │  │          │              │    │
│  │  │ Scopus   │  │ Bloom    │  │ Readings │              │    │
│  │  │ Search   │  │ Mapper   │  │ Quizzes  │              │    │
│  │  │ Knowledge│  │ Card     │  │ Maestría │              │    │
│  │  │ Matrix   │  │ Builder  │  │ Artifacts│              │    │
│  │  └──────────┘  └──────────┘  └──────────┘              │    │
│  │  Strands SDK + Claude Sonnet 4.6                        │    │
│  │  Self-persist to S3 + DynamoDB                          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  QA Gate     │  │Canvas Publisher│                            │
│  │  Lambda      │  │  Lambda       │                            │
│  │  RA coverage │  │  Mock/Real    │                            │
│  │  Bloom align │  │  Canvas API   │                            │
│  │  Maestría    │  │              │                            │
│  └──────────────┘  └──────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴────────────────────────────────────┐
│                     CAPA DE DATOS                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  Amazon S3   │  │  DynamoDB    │  │  Secrets Manager     │   │
│  │              │  │              │  │                      │   │
│  │  subjects/   │  │  subject_id  │  │  scopus-api-key      │   │
│  │   {id}/      │  │  SK: STATE   │  │  canvas-oauth-token  │   │
│  │   subject.   │  │  current_    │  │                      │   │
│  │   json       │  │  state       │  │                      │   │
│  │              │  │  subject_    │  │                      │   │
│  │  uploads/    │  │  name        │  │                      │   │
│  │   {id}/      │  │  canvas_url  │  │                      │   │
│  │   file.docx  │  │              │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  Cognito     │  │  CloudWatch  │                             │
│  │  User Pool   │  │  Logs        │                             │
│  │  staff-admin │  │  Metrics     │                             │
│  └──────────────┘  └──────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┴────────────────────────────────────┐
│                   INTEGRACIONES EXTERNAS                         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  Scopus API  │  │  Canvas LMS  │                             │
│  │  (Elsevier)  │  │ (Instructure)│                             │
│  │  Q1/Q2 papers│  │  Courses     │                             │
│  │  Rate limited│  │  Modules     │                             │
│  │              │  │  Pages       │                             │
│  │              │  │  Quizzes     │                             │
│  └──────────────┘  └──────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
```

## Subject JSON — Fuente Única de Verdad

Cada asignatura tiene un JSON en S3 que se enriquece progresivamente:

```json
{
  "subject_id": "uuid",
  "metadata": {
    "subject_name": "Fundamentos estratégicos de finanzas",
    "program_name": "Maestría en Dirección y Tecnología Financiera",
    "program_type": "MAESTRIA",
    "subject_type": "FUNDAMENTOS",
    "language": "ES"
  },
  "academic_inputs": {
    "graduation_profile": "...",
    "competencies": [{"competency_id": "C1", "description": "..."}],
    "learning_outcomes": [{"ra_id": "RA1", "description": "..."}],
    "syllabus": "Contenido temático: 1) ... 2) ... 3) ..."
  },
  "research": {
    "keywords": ["financial data analytics", ...],
    "top20_papers": [{...}],
    "knowledge_matrix": [{...}]
  },
  "instructional_design": {
    "learning_objectives": [{
      "objective_id": "OBJ-001",
      "bloom_level": "ANALIZAR",
      "competency_ids": ["C1", "C3"],
      "ra_ids": ["RA1"]
    }],
    "descriptive_card": {...},
    "content_map": {"weeks": [...]}
  },
  "content_package": {
    "executive_readings": {"readings": [...]},
    "quizzes": {"quizzes": [...]},
    "maestria_artifacts": {
      "evidence_dashboard": {...},
      "critical_path_map": {...},
      "executive_cases_repository": {...},
      "facilitator_guide": {...}
    }
  },
  "qa_report": {
    "status": "PASS",
    "ra_coverage": {"total_ras": 2, "covered_ras": 2, "gaps": []},
    "bloom_alignment": {"total_objectives": 5, "aligned_objectives": 5, "gaps": []}
  },
  "pipeline_state": {
    "current_state": "PUBLISHED",
    "state_history": [...]
  },
  "publication": {
    "canvas_course_id": "90001",
    "canvas_course_url": "https://anahuacmerida.instructure.com/courses/90001"
  }
}
```

## Estados del Pipeline

```
UPLOADED → KNOWLEDGE_MATRIX_READY → DI_READY → CONTENT_READY
→ PENDING_APPROVAL → APPROVED → PUBLISHED
                   → REJECTED (→ re-process)
```

## Decisiones de Diseño

1. **Auto-persistencia de agentes**: Cada agente escribe directamente a S3/DynamoDB después de completar, eliminando la dependencia del orquestador para persistir.

2. **State regression guard**: Los agentes verifican el estado actual antes de escribir — nunca regresan un estado más avanzado (ej: no sobrescriben PENDING_APPROVAL con CONTENT_READY).

3. **Mock Canvas mode**: `CANVAS_MOCK_MODE=true` permite probar el flujo completo sin hacer llamadas reales a Canvas API.

4. **DOCX table parsing**: Los documentos de Anáhuac tienen datos en tablas, no en párrafos. El parser extrae de ambas fuentes.

5. **Compact prompts**: Los prompts de los agentes se compactaron para evitar `MaxTokensReachedException` en el agent loop de Strands SDK.

6. **Type coercion in tools**: `_ensure_dicts()` maneja el caso donde el LLM pasa items como strings JSON en vez de dicts.
