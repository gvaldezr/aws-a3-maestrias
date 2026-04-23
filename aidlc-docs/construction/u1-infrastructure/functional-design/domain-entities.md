# Entidades de Dominio — U1: Infraestructura Base + JSON Schema

---

## SubjectJSON (Fuente Única de Verdad)

Objeto JSON principal que fluye y se enriquece a través de las 5 fases del pipeline. Un objeto por asignatura.

```json
{
  "subject_id": "uuid-v4",
  "schema_version": "1.0",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",

  "metadata": {
    "subject_name": "string",
    "program_name": "string",
    "program_type": "MAESTRIA | OTRO",
    "subject_type": "FUNDAMENTOS | CONCENTRACION | PROYECTO",
    "language": "ES | EN | BILINGUAL",
    "academic_period": "string"
  },

  "academic_inputs": {
    "graduation_profile": "string",
    "competencies": [
      {
        "competency_id": "string",
        "description": "string",
        "level": "string"
      }
    ],
    "learning_outcomes": [
      {
        "ra_id": "string",
        "description": "string"
      }
    ],
    "syllabus": "string"
  },

  "research": {
    "keywords": ["string"],
    "top20_papers": [
      {
        "scopus_id": "string",
        "title": "string",
        "authors": ["string"],
        "year": "integer",
        "journal": "string",
        "quartile": "Q1 | Q2",
        "key_finding": "string",
        "doi": "string"
      }
    ],
    "knowledge_matrix": [
      {
        "concept": "string",
        "source_paper_id": "string",
        "methodology": "string",
        "executive_application": "string",
        "ra_relevance": ["ra_id"]
      }
    ]
  },

  "instructional_design": {
    "content_map": {
      "weeks": [
        {
          "week": "integer",
          "theme": "string",
          "bloom_level": "RECORDAR | COMPRENDER | APLICAR | ANALIZAR | EVALUAR | CREAR",
          "activities": ["string"]
        }
      ]
    },
    "learning_objectives": [
      {
        "objective_id": "string",
        "description": "string",
        "bloom_verb": "string",
        "bloom_level": "string",
        "competency_ids": ["string"],
        "ra_ids": ["string"]
      }
    ],
    "traceability_matrix": [
      {
        "objective_id": "string",
        "bloom_level": "string",
        "competency_ids": ["string"],
        "ra_id": "string"
      }
    ],
    "descriptive_card": {
      "version": "string",
      "general_objective": "string",
      "specific_objectives": ["string"],
      "weekly_map": "string",
      "case_studies_design": "string",
      "evaluation_criteria": "string"
    }
  },

  "content_package": {
    "executive_readings": [
      {
        "week": "integer",
        "title": "string",
        "content_md": "string",
        "language": "string"
      }
    ],
    "masterclass_scripts": [
      {
        "session": "integer",
        "title": "string",
        "script_md": "string",
        "duration_minutes": "integer",
        "language": "string"
      }
    ],
    "quizzes": [
      {
        "ra_id": "string",
        "questions": [
          {
            "question": "string",
            "options": ["string"],
            "correct_answer": "integer",
            "feedback": "string"
          }
        ]
      }
    ],
    "lab_cases": [
      {
        "title": "string",
        "context": "string",
        "data": "string",
        "questions": ["string"],
        "rubric": {
          "criteria": ["string"],
          "competency_ids": ["string"]
        }
      }
    ],
    "maestria_artifacts": {
      "evidence_dashboard": {
        "html_content": "string",
        "papers_summary": ["object"]
      },
      "critical_path_map": {
        "markdown_content": "string",
        "weeks": ["object"]
      },
      "executive_cases_repository": {
        "cases": ["object"]
      },
      "facilitator_guide": {
        "sessions": ["object"]
      }
    },
    "apa_bibliography": ["string"]
  },

  "qa_report": {
    "ra_coverage": {
      "total_ras": "integer",
      "covered_ras": "integer",
      "gaps": ["ra_id"]
    },
    "bloom_alignment": {
      "total_objectives": "integer",
      "aligned_objectives": "integer",
      "gaps": ["objective_id"]
    },
    "maestria_artifacts_present": "boolean | null",
    "retry_count": "integer",
    "status": "PASS | FAIL",
    "validated_at": "ISO-8601"
  },

  "validation": {
    "status": "PENDING_APPROVAL | APPROVED | REJECTED",
    "decided_by": "string",
    "decided_at": "ISO-8601",
    "comments": "string",
    "manual_edits": ["object"],
    "reminder_sent_at": "ISO-8601 | null"
  },

  "publication": {
    "canvas_course_id": "string | null",
    "canvas_course_url": "string | null",
    "module_urls": ["string"],
    "published_at": "ISO-8601 | null"
  },

  "pipeline_state": {
    "current_state": "INGESTED | KNOWLEDGE_MATRIX_READY | DI_READY | CONTENT_READY | PENDING_APPROVAL | APPROVED | REJECTED | PUBLISHED | FAILED | RESEARCH_ESCALATED | DI_ALIGNMENT_GAP | QA_FAILED | CONTENT_QA_FAILED",
    "state_history": [
      {
        "state": "string",
        "agent": "string",
        "timestamp": "ISO-8601",
        "llm_version": "string | null",
        "result_hash": "string"
      }
    ]
  }
}
```

---

## SubjectStateRecord (DynamoDB)

Registro de índice en DynamoDB para consultas rápidas de estado sin leer el JSON completo de S3.

```
PK: subject_id (string)
SK: "STATE"
Attributes:
  - current_state: string
  - program_type: string
  - subject_name: string
  - updated_at: ISO-8601
  - s3_key: string (referencia al JSON en S3)
  - retry_count: integer
  - approval_deadline: ISO-8601 | null
```

**GSI-1**: `state-index` — PK: `current_state`, SK: `updated_at` (para listar asignaturas por estado)
**GSI-2**: `program-index` — PK: `program_name`, SK: `updated_at` (para filtrar por programa)
