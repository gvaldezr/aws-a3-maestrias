"""
JSON Schema v1.0 para SubjectJSON — Fuente Única de Verdad del pipeline académico.
Definido como dict Python para evitar dependencia de archivo JSON externo.
"""

SUBJECT_SCHEMA_V1: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "academic-pipeline/subject/v1.0",
    "title": "SubjectJSON",
    "description": "Fuente única de verdad del pipeline académico por asignatura",
    "type": "object",
    "required": [
        "subject_id", "schema_version", "created_at", "updated_at",
        "metadata", "academic_inputs", "pipeline_state",
    ],
    "additionalProperties": False,
    "properties": {
        "subject_id": {"type": "string"},
        "schema_version": {"type": "string", "const": "1.0"},
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"},
        "metadata": {
            "type": "object",
            "required": ["subject_name", "program_name", "program_type", "subject_type", "language"],
            "additionalProperties": False,
            "properties": {
                "subject_name": {"type": "string", "minLength": 1, "maxLength": 255},
                "program_name": {"type": "string", "minLength": 1, "maxLength": 255},
                "program_type": {"type": "string", "enum": ["MAESTRIA", "OTRO"]},
                "subject_type": {"type": "string", "enum": ["FUNDAMENTOS", "CONCENTRACION", "PROYECTO"]},
                "language": {"type": "string", "enum": ["ES", "EN", "BILINGUAL"]},
                "academic_period": {"type": "string"},
            },
        },
        "academic_inputs": {
            "type": "object",
            "required": ["graduation_profile", "competencies", "learning_outcomes"],
            "additionalProperties": False,
            "properties": {
                "graduation_profile": {"type": "string", "minLength": 1},
                "competencies": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["competency_id", "description"],
                        "additionalProperties": False,
                        "properties": {
                            "competency_id": {"type": "string", "minLength": 1},
                            "description": {"type": "string", "minLength": 1},
                            "level": {"type": "string"},
                        },
                    },
                },
                "learning_outcomes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["ra_id", "description"],
                        "additionalProperties": False,
                        "properties": {
                            "ra_id": {"type": "string", "minLength": 1},
                            "description": {"type": "string", "minLength": 1},
                        },
                    },
                },
                "syllabus": {"type": "string"},
            },
        },
        "research": {"type": "object"},
        "instructional_design": {"type": "object"},
        "content_package": {"type": "object"},
        "qa_report": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "ra_coverage": {"type": "object"},
                "bloom_alignment": {"type": "object"},
                "maestria_artifacts_present": {"type": ["boolean", "null"]},
                "retry_count": {"type": "integer", "minimum": 0, "maximum": 3},
                "status": {"type": "string", "enum": ["PASS", "FAIL"]},
                "validated_at": {"type": "string"},
            },
        },
        "validation": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {"type": "string", "enum": ["PENDING_APPROVAL", "APPROVED", "REJECTED"]},
                "decided_by": {"type": "string"},
                "decided_at": {"type": ["string", "null"]},
                "comments": {"type": "string"},
                "manual_edits": {"type": "array"},
                "reminder_sent_at": {"type": ["string", "null"]},
            },
        },
        "publication": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "canvas_course_id": {"type": ["string", "null"]},
                "canvas_course_url": {"type": ["string", "null"]},
                "module_urls": {"type": "array", "items": {"type": "string"}},
                "published_at": {"type": ["string", "null"]},
            },
        },
        "pipeline_state": {
            "type": "object",
            "required": ["current_state", "state_history"],
            "additionalProperties": False,
            "properties": {
                "current_state": {
                    "type": "string",
                    "enum": [
                        "INGESTED", "KNOWLEDGE_MATRIX_READY", "DI_READY", "CONTENT_READY",
                        "PENDING_APPROVAL", "APPROVED", "REJECTED", "PUBLISHED", "FAILED",
                        "RESEARCH_ESCALATED", "DI_ALIGNMENT_GAP", "QA_FAILED", "CONTENT_QA_FAILED",
                    ],
                },
                "state_history": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["state", "agent", "timestamp", "result_hash"],
                        "additionalProperties": False,
                        "properties": {
                            "state": {"type": "string"},
                            "agent": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "llm_version": {"type": ["string", "null"]},
                            "result_hash": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
}

VALID_STATE_TRANSITIONS: dict[str, list[str]] = {
    "INGESTED": ["KNOWLEDGE_MATRIX_READY", "RESEARCH_ESCALATED", "FAILED"],
    "KNOWLEDGE_MATRIX_READY": ["DI_READY", "DI_ALIGNMENT_GAP", "FAILED"],
    "DI_READY": ["CONTENT_READY", "CONTENT_QA_FAILED", "FAILED"],
    "CONTENT_READY": ["PENDING_APPROVAL", "QA_FAILED", "FAILED"],
    "PENDING_APPROVAL": ["APPROVED", "REJECTED"],
    "APPROVED": ["PUBLISHED", "FAILED"],
    "REJECTED": ["CONTENT_READY"],
    "RESEARCH_ESCALATED": ["KNOWLEDGE_MATRIX_READY"],
    "DI_ALIGNMENT_GAP": ["DI_READY"],
    "QA_FAILED": ["CONTENT_READY"],
    "CONTENT_QA_FAILED": ["CONTENT_READY"],
    "PUBLISHED": [],
    "FAILED": [],
}
