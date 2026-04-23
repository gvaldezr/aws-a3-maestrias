"""Modelos de dominio para gestión de estado del pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SubjectState(str, Enum):
    INGESTED = "INGESTED"
    KNOWLEDGE_MATRIX_READY = "KNOWLEDGE_MATRIX_READY"
    DI_READY = "DI_READY"
    CONTENT_READY = "CONTENT_READY"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    RESEARCH_ESCALATED = "RESEARCH_ESCALATED"
    DI_ALIGNMENT_GAP = "DI_ALIGNMENT_GAP"
    QA_FAILED = "QA_FAILED"
    CONTENT_QA_FAILED = "CONTENT_QA_FAILED"


@dataclass
class StateMetadata:
    agent: str
    llm_version: str | None = None
    result_hash: str = ""


@dataclass
class SubjectSummary:
    subject_id: str
    subject_name: str
    program_name: str
    current_state: str
    updated_at: str
    s3_key: str


@dataclass
class S3Reference:
    bucket: str
    key: str
    version_id: str | None = None
