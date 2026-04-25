"""
QA Gate — U5: Validación de calidad antes del checkpoint humano.
Lambda handler + lógica de negocio pura.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.observability.metrics import record_metric, send_notification
from src.infrastructure.state.models import StateMetadata, SubjectState
from src.infrastructure.state.state_manager import get_subject_json, update_subject_state
try:
    from models import BloomAlignmentResult, QAReport, RACoverageResult
except ImportError:
    from src.qa_checkpoint.models import BloomAlignmentResult, QAReport, RACoverageResult

logger = get_logger(__name__)


# ── Pure business logic ───────────────────────────────────────────────────────

def validate_ra_coverage(subject_json: dict) -> RACoverageResult:
    """
    Valida que cada RA tiene al menos un quiz asociado. (BR-QA02)
    Función pura — sin efectos secundarios.
    """
    learning_outcomes = subject_json["academic_inputs"]["learning_outcomes"]
    quizzes = subject_json.get("content_package", {}).get("quizzes", [])
    covered_ra_ids = {q["ra_id"] for q in quizzes}
    all_ra_ids = {lo["ra_id"] for lo in learning_outcomes}
    gaps = sorted(all_ra_ids - covered_ra_ids)
    return RACoverageResult(
        total_ras=len(all_ra_ids),
        covered_ras=len(all_ra_ids) - len(gaps),
        gaps=gaps,
    )


def validate_bloom_alignment(subject_json: dict) -> BloomAlignmentResult:
    """
    Valida que cada objetivo tiene nivel Bloom y competencia mapeada. (BR-QA03)
    Función pura — sin efectos secundarios.
    """
    objectives = subject_json.get("instructional_design", {}).get("learning_objectives", [])
    gaps = [
        o["objective_id"] for o in objectives
        if not o.get("bloom_level") or not o.get("competency_ids")
    ]
    return BloomAlignmentResult(
        total_objectives=len(objectives),
        aligned_objectives=len(objectives) - len(gaps),
        gaps=gaps,
    )


def validate_maestria_artifacts(subject_json: dict) -> bool | None:
    """
    Para Maestría: valida que los 4 artefactos están presentes. (BR-QA04)
    Retorna None si no es Maestría.
    """
    if subject_json["metadata"]["program_type"] != "MAESTRIA":
        return None
    ma = subject_json.get("content_package", {}).get("maestria_artifacts")
    if not ma:
        return False
    return all([
        bool(ma.get("evidence_dashboard", {}).get("html_content")),
        bool(ma.get("critical_path_map", {}).get("markdown_content")),
        bool(ma.get("executive_cases_repository", {}).get("cases")),
        bool(ma.get("facilitator_guide", {}).get("sessions")),
    ])


def run_qa_gate(subject_json: dict, retry_count: int = 0) -> QAReport:
    """
    Ejecuta todas las validaciones del QA Gate. (BR-QA01)
    Función pura — sin efectos secundarios.
    Idempotente: mismo input → mismo output.
    """
    now = datetime.now(timezone.utc).isoformat()
    ra_result = validate_ra_coverage(subject_json)
    bloom_result = validate_bloom_alignment(subject_json)
    maestria_result = validate_maestria_artifacts(subject_json)

    # Determinar status global
    all_pass = (
        ra_result.is_complete
        and bloom_result.is_complete
        and (maestria_result is None or maestria_result is True)
    )

    return QAReport(
        subject_id=subject_json["subject_id"],
        ra_coverage=ra_result,
        bloom_alignment=bloom_result,
        maestria_artifacts_present=maestria_result,
        overall_status="PASS" if all_pass else "FAIL",
        validated_at=now,
        retry_count=retry_count,
    )


# ── Lambda Handler ────────────────────────────────────────────────────────────

def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda entry point para el QA Gate.
    Invocado por el orquestador del pipeline tras CONTENT_READY.
    """
    subject_id: str = event.get("subject_id", "")
    retry_count: int = event.get("retry_count", 0)

    if not subject_id:
        return {"statusCode": 400, "body": json.dumps({"error": "subject_id required"})}

    logger.info("qa_gate_start", extra={"subject_id": subject_id, "retry": retry_count})

    try:
        subject_json = get_subject_json(subject_id)
        report = run_qa_gate(subject_json, retry_count)

        # Store QA report in JSON
        subject_json["qa_report"] = report.to_dict()

        if report.overall_status == "PASS":
            # Advance to PENDING_APPROVAL
            _notify_staff_for_review(subject_id, subject_json, report)
            update_subject_state(
                subject_id,
                SubjectState.PENDING_APPROVAL,
                StateMetadata(agent="qa-gate"),
            )
            record_metric("QAGatePassed", 1, "Count")
            logger.info("qa_gate_passed", extra={"subject_id": subject_id})
            return {"statusCode": 200, "body": json.dumps({"status": "PENDING_APPROVAL", "subject_id": subject_id})}
        else:
            record_metric("QAGateFailed", 1, "Count")
            logger.warning("qa_gate_failed", extra={
                "subject_id": subject_id,
                "ra_gaps": report.ra_coverage.gaps,
                "bloom_gaps": report.bloom_alignment.gaps,
            })
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "status": "QA_FAILED",
                    "subject_id": subject_id,
                    "ra_gaps": report.ra_coverage.gaps,
                    "bloom_gaps": report.bloom_alignment.gaps,
                    "maestria_ok": report.maestria_artifacts_present,
                }),
            }

    except Exception as exc:
        logger.error("qa_gate_error", extra={"subject_id": subject_id, "error": str(exc)})
        return {"statusCode": 500, "body": json.dumps({"error": str(exc)})}


def _notify_staff_for_review(subject_id: str, subject_json: dict, report: QAReport) -> None:
    """Notifica al Staff que el contenido está listo para revisión."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    timeout_at = (now + timedelta(hours=48)).isoformat()

    topic_arn = os.environ.get("STAFF_NOTIFICATIONS_TOPIC_ARN", "")
    if topic_arn:
        summary = {
            "subject_id": subject_id,
            "subject_name": subject_json["metadata"]["subject_name"],
            "program_name": subject_json["metadata"]["program_name"],
            "qa_status": report.overall_status,
            "quizzes_count": len(subject_json.get("content_package", {}).get("quizzes", [])),
            "maestria_artifacts": report.maestria_artifacts_present,
            "review_deadline": timeout_at,
            "action_required": "Aprobar, rechazar o editar el contenido antes del plazo.",
        }
        send_notification(
            topic_arn,
            subject=f"[Pipeline] Contenido listo para revisión — {subject_json['metadata']['subject_name']}",
            message=json.dumps(summary),
        )

    # Store pending_since and timeout_at in JSON
    subject_json.setdefault("validation", {})
    subject_json["validation"]["status"] = "PENDING_APPROVAL"
    subject_json["validation"]["pending_since"] = now.isoformat()
    subject_json["validation"]["reminder_sent_at"] = None
