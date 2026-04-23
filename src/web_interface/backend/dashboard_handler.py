"""
Dashboard Handler — U7: Lista el estado de asignaturas para el Staff.
Lambda invocado por API Gateway: GET /api/subjects
"""
from __future__ import annotations

import json
import os
from typing import Any

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.state.models import SubjectState
from src.infrastructure.state.state_manager import list_subjects_by_state

logger = get_logger(__name__)

_SECURITY_HEADERS = {
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
    "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", ""),
}

_ALL_STATES = [s for s in SubjectState]


def lambda_handler(event: dict, context: Any) -> dict:
    """
    Retorna el estado de todas las asignaturas para el dashboard del Staff.
    Agrega conteos por estado para métricas del dashboard.
    """
    try:
        all_subjects = []
        for state in _ALL_STATES:
            subjects = list_subjects_by_state(state)
            all_subjects.extend([
                {
                    "subject_id": s.subject_id,
                    "subject_name": s.subject_name,
                    "program_name": s.program_name,
                    "current_state": s.current_state,
                    "updated_at": s.updated_at,
                    "pending_approval": s.current_state == "PENDING_APPROVAL",
                }
                for s in subjects
            ])

        pending = sum(1 for s in all_subjects if s["current_state"] == "PENDING_APPROVAL")
        published = sum(1 for s in all_subjects if s["current_state"] == "PUBLISHED")
        failed = sum(1 for s in all_subjects if s["current_state"] == "FAILED")

        return _response(200, {
            "subjects": all_subjects,
            "total": len(all_subjects),
            "pending_approval_count": pending,
            "published_count": published,
            "failed_count": failed,
        })

    except Exception as exc:
        logger.error("dashboard_error", extra={"error": str(exc)})
        return _response(500, {"error": "Error retrieving dashboard data"})


def _response(status_code: int, body: dict) -> dict:
    return {"statusCode": status_code, "headers": _SECURITY_HEADERS, "body": json.dumps(body)}
