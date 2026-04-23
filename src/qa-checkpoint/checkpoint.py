"""
Checkpoint Handler — U5: Procesa decisiones del Staff (aprobación/rechazo/edición).
Lambda handler invocado por API Gateway con JWT Cognito.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.observability.metrics import record_metric
from src.infrastructure.state.models import StateMetadata, SubjectState
from src.infrastructure.state.state_manager import get_subject_json, update_subject_state
from src.qa_checkpoint.models import ValidationDecision

logger = get_logger(__name__)

_MAX_REJECTION_CYCLES = 3


def process_approval(subject_json: dict, staff_user: str) -> ValidationDecision:
    """
    Procesa la aprobación del Staff. (BR-QA06, BR-QA09)
    Función pura — retorna ValidationDecision sin efectos secundarios.
    """
    now = datetime.now(timezone.utc).isoformat()
    return ValidationDecision(
        subject_id=subject_json["subject_id"],
        decision="APPROVED",
        decided_by=staff_user,
        decided_at=now,
    )


def process_rejection(subject_json: dict, staff_user: str, comments: str) -> ValidationDecision:
    """
    Procesa el rechazo del Staff. (BR-QA07, BR-QA09, BR-QA10)
    Lanza ValueError si comments está vacío (BR-QA07).
    """
    if not comments or not comments.strip():
        raise ValueError("Los comentarios son obligatorios al rechazar contenido (BR-QA07)")

    now = datetime.now(timezone.utc).isoformat()
    return ValidationDecision(
        subject_id=subject_json["subject_id"],
        decision="REJECTED",
        decided_by=staff_user,
        decided_at=now,
        comments=comments,
    )


def count_rejection_cycles(subject_json: dict) -> int:
    """Cuenta cuántos ciclos de rechazo ha tenido la asignatura."""
    history = subject_json.get("pipeline_state", {}).get("state_history", [])
    return sum(1 for entry in history if entry.get("state") == "REJECTED")


def apply_manual_edits(subject_json: dict, edits: dict, staff_user: str) -> None:
    """
    Aplica ediciones manuales del Staff al JSON. (BR-QA09)
    Registra cada edición con: campo, valor_anterior, valor_nuevo, usuario, timestamp.
    """
    now = datetime.now(timezone.utc).isoformat()
    subject_json.setdefault("validation", {}).setdefault("manual_edits", [])

    for field_path, new_value in edits.items():
        # Navegar el JSON por el path (ej: "instructional_design.descriptive_card.general_objective")
        parts = field_path.split(".")
        obj = subject_json
        for part in parts[:-1]:
            obj = obj.setdefault(part, {})
        old_value = obj.get(parts[-1])
        obj[parts[-1]] = new_value

        subject_json["validation"]["manual_edits"].append({
            "field": field_path,
            "old_value": old_value,
            "new_value": new_value,
            "edited_by": staff_user,
            "edited_at": now,
        })


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda entry point para el Checkpoint Handler.
    Invocado por API Gateway: POST /subjects/{subject_id}/decision
    JWT Cognito requerido — staff_user extraído del token.
    """
    # Extract subject_id from path parameters
    subject_id = event.get("pathParameters", {}).get("subject_id", "")
    if not subject_id:
        return _response(400, {"error": "subject_id required in path"})

    # Extract staff_user from JWT claims (Cognito authorizer injects this)
    claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    staff_user = claims.get("cognito:username") or claims.get("email", "unknown")

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    decision_type = body.get("decision", "").upper()
    comments = body.get("comments", "")
    manual_edits = body.get("manual_edits", {})

    logger.info("checkpoint_decision_received", extra={
        "subject_id": subject_id, "decision": decision_type, "staff_user": staff_user,
    })

    try:
        subject_json = get_subject_json(subject_id)

        # Validate current state is PENDING_APPROVAL
        current_state = subject_json["pipeline_state"]["current_state"]
        if current_state != "PENDING_APPROVAL":
            return _response(409, {"error": f"Subject is not pending approval. Current state: {current_state}"})

        if decision_type == "APPROVED":
            decision = process_approval(subject_json, staff_user)
            subject_json["validation"] = decision.to_dict()
            update_subject_state(
                subject_id, SubjectState.APPROVED,
                StateMetadata(agent=f"staff:{staff_user}"),
            )
            record_metric("ApprovalsReceived", 1, "Count")
            logger.info("checkpoint_approved", extra={"subject_id": subject_id, "staff_user": staff_user})
            return _response(200, {"status": "APPROVED", "subject_id": subject_id})

        elif decision_type == "REJECTED":
            try:
                decision = process_rejection(subject_json, staff_user, comments)
            except ValueError as ve:
                return _response(400, {"error": str(ve)})

            # Check rejection cycle limit (BR-QA10)
            rejection_count = count_rejection_cycles(subject_json) + 1
            if rejection_count >= _MAX_REJECTION_CYCLES:
                logger.warning("checkpoint_max_rejections_reached", extra={
                    "subject_id": subject_id, "rejection_count": rejection_count,
                })
                # Escalate to technical support
                _escalate_to_support(subject_id, rejection_count)

            subject_json["validation"] = decision.to_dict()
            update_subject_state(
                subject_id, SubjectState.REJECTED,
                StateMetadata(agent=f"staff:{staff_user}"),
            )
            record_metric("RejectionsReceived", 1, "Count")
            logger.info("checkpoint_rejected", extra={
                "subject_id": subject_id, "staff_user": staff_user, "comments_length": len(comments),
            })
            return _response(200, {
                "status": "REJECTED", "subject_id": subject_id,
                "next_step": "Content agent will be re-invoked with feedback",
            })

        elif decision_type == "EDIT":
            if not manual_edits:
                return _response(400, {"error": "manual_edits required for EDIT decision"})
            apply_manual_edits(subject_json, manual_edits, staff_user)
            # State remains PENDING_APPROVAL — Staff must still approve
            logger.info("checkpoint_manual_edit", extra={
                "subject_id": subject_id, "fields_edited": list(manual_edits.keys()),
            })
            return _response(200, {
                "status": "PENDING_APPROVAL",
                "subject_id": subject_id,
                "edits_applied": len(manual_edits),
                "message": "Edits applied. Please approve or reject to finalize.",
            })

        else:
            return _response(400, {"error": f"Invalid decision: {decision_type}. Must be APPROVED, REJECTED, or EDIT"})

    except KeyError as exc:
        return _response(404, {"error": f"Subject not found: {subject_id}"})
    except Exception as exc:
        logger.error("checkpoint_error", extra={"subject_id": subject_id, "error": str(exc)})
        return _response(500, {"error": "Internal server error"})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "X-Content-Type-Options": "nosniff",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Frame-Options": "DENY",
        },
        "body": json.dumps(body),
    }


def _escalate_to_support(subject_id: str, rejection_count: int) -> None:
    from src.infrastructure.observability.metrics import send_notification
    topic_arn = os.environ.get("PIPELINE_ALERTS_TOPIC_ARN", "")
    if topic_arn:
        send_notification(
            topic_arn,
            subject=f"[Pipeline] Máximo de rechazos alcanzado — {subject_id}",
            message=json.dumps({"subject_id": subject_id, "rejection_count": rejection_count,
                                "action": "Manual technical support required"}),
        )
