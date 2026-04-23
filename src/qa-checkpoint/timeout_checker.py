"""
Timeout Checker — U5: Verifica asignaturas en PENDING_APPROVAL sin respuesta en 48h.
Lambda invocada por EventBridge Scheduler cada hora.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.observability.metrics import record_metric, send_notification
from src.infrastructure.state.models import SubjectState
from src.infrastructure.state.state_manager import get_subject_json, list_subjects_by_state

logger = get_logger(__name__)

_TIMEOUT_HOURS = 48


def is_past_timeout(pending_since: str, now: datetime | None = None) -> bool:
    """
    Verifica si han pasado más de 48h desde pending_since.
    Función pura — testeable con PBT.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        pending_dt = datetime.fromisoformat(pending_since.replace("Z", "+00:00"))
        return now >= pending_dt + timedelta(hours=_TIMEOUT_HOURS)
    except (ValueError, AttributeError):
        return False


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Verifica todas las asignaturas en PENDING_APPROVAL.
    Envía recordatorio SNS si han pasado > 48h sin respuesta. (BR-QA08)
    """
    now = datetime.now(timezone.utc)
    pending_subjects = list_subjects_by_state(SubjectState.PENDING_APPROVAL)
    reminders_sent = 0

    for summary in pending_subjects:
        try:
            subject_json = get_subject_json(summary.subject_id)
            pending_since = subject_json.get("validation", {}).get("pending_since", "")
            reminder_sent_at = subject_json.get("validation", {}).get("reminder_sent_at")

            if not pending_since:
                continue

            # Only send reminder if past timeout AND no reminder sent yet
            if is_past_timeout(pending_since, now) and not reminder_sent_at:
                _send_reminder(summary.subject_id, subject_json, pending_since)
                subject_json["validation"]["reminder_sent_at"] = now.isoformat()
                reminders_sent += 1
                record_metric("TimeoutReminders", 1, "Count")
                logger.warning("timeout_reminder_sent", extra={
                    "subject_id": summary.subject_id,
                    "pending_since": pending_since,
                })

        except Exception as exc:
            logger.error("timeout_checker_error", extra={
                "subject_id": summary.subject_id, "error": str(exc),
            })

    logger.info("timeout_checker_complete", extra={"checked": len(pending_subjects), "reminders": reminders_sent})
    return {"statusCode": 200, "body": json.dumps({"reminders_sent": reminders_sent})}


def _send_reminder(subject_id: str, subject_json: dict, pending_since: str) -> None:
    topic_arn = os.environ.get("STAFF_NOTIFICATIONS_TOPIC_ARN", "")
    if topic_arn:
        send_notification(
            topic_arn,
            subject=f"[RECORDATORIO] Validación pendiente — {subject_json['metadata']['subject_name']}",
            message=json.dumps({
                "subject_id": subject_id,
                "subject_name": subject_json["metadata"]["subject_name"],
                "pending_since": pending_since,
                "message": "Han pasado más de 48 horas. Por favor revise y apruebe o rechace el contenido.",
            }),
        )
