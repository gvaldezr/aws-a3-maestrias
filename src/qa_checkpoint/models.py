"""Modelos de dominio — U5: QA Gate + Checkpoint Humano."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RACoverageResult:
    total_ras: int
    covered_ras: int
    gaps: list[str]

    @property
    def is_complete(self) -> bool:
        return len(self.gaps) == 0

    def to_dict(self) -> dict:
        return {"total_ras": self.total_ras, "covered_ras": self.covered_ras, "gaps": self.gaps}


@dataclass
class BloomAlignmentResult:
    total_objectives: int
    aligned_objectives: int
    gaps: list[str]

    @property
    def is_complete(self) -> bool:
        return len(self.gaps) == 0

    def to_dict(self) -> dict:
        return {
            "total_objectives": self.total_objectives,
            "aligned_objectives": self.aligned_objectives,
            "gaps": self.gaps,
        }


@dataclass
class QAReport:
    subject_id: str
    ra_coverage: RACoverageResult
    bloom_alignment: BloomAlignmentResult
    maestria_artifacts_present: bool | None
    overall_status: str   # "PASS" | "FAIL"
    validated_at: str
    retry_count: int = 0

    def to_dict(self) -> dict:
        return {
            "ra_coverage": self.ra_coverage.to_dict(),
            "bloom_alignment": self.bloom_alignment.to_dict(),
            "maestria_artifacts_present": self.maestria_artifacts_present,
            "retry_count": self.retry_count,
            "status": self.overall_status,
            "validated_at": self.validated_at,
        }


@dataclass
class ValidationDecision:
    subject_id: str
    decision: str         # "APPROVED" | "REJECTED"
    decided_by: str
    decided_at: str
    comments: str = ""
    manual_edits: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.decision,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at,
            "comments": self.comments,
            "manual_edits": self.manual_edits,
        }


@dataclass
class CheckpointSummary:
    subject_id: str
    subject_name: str
    program_name: str
    qa_report: QAReport
    descriptive_card_preview: str
    content_preview: dict
    maestria_artifacts_present: bool
    pending_since: str
    timeout_at: str
