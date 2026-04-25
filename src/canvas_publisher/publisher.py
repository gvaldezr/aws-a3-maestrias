"""
Canvas Publisher — U6: Publicación del curso en Canvas LMS.
Lambda handler — Fase 5: Curaduría y Montaje.
Supports CANVAS_MOCK_MODE=true for testing without real Canvas API calls.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

try:
    from canvas_client import CanvasAPIError, CanvasClient
    from mock_client import MockCanvasClient
    from formatters import format_apa_page_payload, format_page_payload, format_quiz_payload, format_quiz_question_payload, format_rubric_payload
    from models import PublicationResult
except ImportError:
    from src.canvas_publisher.canvas_client import CanvasAPIError, CanvasClient
    from src.canvas_publisher.mock_client import MockCanvasClient
    from src.canvas_publisher.formatters import format_apa_page_payload, format_page_payload, format_quiz_payload, format_quiz_question_payload, format_rubric_payload
    from src.canvas_publisher.models import PublicationResult

from src.infrastructure.observability.logger import get_logger
from src.infrastructure.observability.metrics import record_metric, send_notification

logger = get_logger(__name__)

_CANVAS_ACCOUNT_ID = os.environ.get("CANVAS_ACCOUNT_ID", "1")


def publish_course(subject_json: dict, client: CanvasClient) -> PublicationResult:
    """
    Publica el curso completo en Canvas LMS.
    Función orquestadora — llama a helpers especializados.
    """
    subject_id = subject_json["subject_id"]
    metadata = subject_json["metadata"]
    content = subject_json.get("content_package", {})
    instructional = subject_json.get("instructional_design", {})
    competencies = subject_json["academic_inputs"]["competencies"]

    course_code = f"AP-{subject_id[:8].upper()}"

    # BR-CV09 — Idempotencia: verificar si ya existe
    existing = client.find_course_by_code(_CANVAS_ACCOUNT_ID, course_code)
    if existing:
        logger.info("canvas_course_already_exists", extra={"subject_id": subject_id, "course_id": existing["id"]})
        course_id = str(existing["id"])
        course_url = existing.get("html_url", "")
    else:
        # BR-CV02 — Crear en estado borrador
        course_resp = client.create_course(_CANVAS_ACCOUNT_ID, {
            "course": {
                "name": metadata["subject_name"],
                "course_code": course_code,
                "workflow_state": "unpublished",
                "language": metadata.get("language", "es").lower()[:2],
            }
        })
        course_id = str(course_resp["id"])
        course_url = course_resp.get("html_url", "")
        logger.info("canvas_course_created", extra={"subject_id": subject_id, "course_id": course_id})

    # Crear módulo principal
    module_resp = client.create_module(course_id, metadata["subject_name"], position=1)
    module_id = str(module_resp["id"])
    module_urls: list[str] = []

    # Publicar lecturas ejecutivas
    readings_data = content.get("executive_readings", {})
    readings = readings_data.get("readings", []) if isinstance(readings_data, dict) else (readings_data if isinstance(readings_data, list) else [])
    for reading in readings:
        if not isinstance(reading, dict):
            continue
        page = client.create_page(course_id, format_page_payload(reading.get("title", ""), reading.get("content_md", "")))
        _add_page_to_module(client, course_id, module_id, page)
        module_urls.append(page.get("html_url", ""))

    # Publicar quizzes (BR-C03: mínimo 3 preguntas por RA)
    quizzes_data = content.get("quizzes", {})
    quizzes = quizzes_data.get("quizzes", []) if isinstance(quizzes_data, dict) else (quizzes_data if isinstance(quizzes_data, list) else [])
    for quiz_data in quizzes:
        if not isinstance(quiz_data, dict):
            continue
        quiz_resp = client.create_quiz(course_id, format_quiz_payload(
            title=f"Quiz — {quiz_data['ra_id']}",
            ra_id=quiz_data["ra_id"],
        ))
        quiz_id = str(quiz_resp["id"])
        for q in quiz_data.get("questions", []):
            client.create_quiz_question(course_id, quiz_id, format_quiz_question_payload(q))
        _add_quiz_to_module(client, course_id, module_id, quiz_id, f"Quiz — {quiz_data['ra_id']}")

    # Publicar casos de laboratorio con rúbricas (BR-CV04)
    for case in content.get("lab_cases", []):
        rubric = case.get("rubric", {})
        if rubric.get("criteria") and rubric.get("competency_ids"):
            client.create_rubric(course_id, format_rubric_payload(
                title=case["title"],
                criteria=rubric["criteria"],
                competency_ids=rubric["competency_ids"],
            ))

    # Bibliografía APA (BR-CV05)
    if content.get("apa_bibliography"):
        apa_page = client.create_page(course_id, format_apa_page_payload(content["apa_bibliography"]))
        _add_page_to_module(client, course_id, module_id, apa_page)

    # Artefactos Maestría (BR-CV03)
    if metadata["program_type"] == "MAESTRIA":
        _publish_maestria_artifacts(client, course_id, module_id, content, module_urls)

    now = datetime.now(timezone.utc).isoformat()
    return PublicationResult(
        subject_id=subject_id,
        canvas_course_id=course_id,
        canvas_course_url=course_url,
        module_urls=module_urls,
        published_at=now,
        status="PUBLISHED",
    )


def _publish_maestria_artifacts(
    client: CanvasClient,
    course_id: str,
    module_id: str,
    content: dict,
    module_urls: list[str],
) -> None:
    """Publica los 4 artefactos de Maestría como páginas independientes (BR-CV03)."""
    ma = content.get("maestria_artifacts") or {}
    artifacts = [
        ("Dashboard de Evidencia", ma.get("evidence_dashboard", {}).get("html_content", "")),
        ("Mapa de Ruta Crítica", ma.get("critical_path_map", {}).get("markdown_content", "")),
        ("Guía del Facilitador", json.dumps(ma.get("facilitator_guide", {}).get("sessions", []), ensure_ascii=False)),
    ]
    for title, content_str in artifacts:
        if content_str:
            page = client.create_page(course_id, format_page_payload(title, content_str))
            _add_page_to_module(client, course_id, module_id, page)
            module_urls.append(page.get("html_url", ""))

    # Repositorio de Casos Ejecutivos
    cases = ma.get("executive_cases_repository", {}).get("cases", [])
    for case in cases:
        case_md = f"# {case.get('title','')}\n\n{case.get('context','')}\n\n{case.get('data','')}"
        page = client.create_page(course_id, format_page_payload(case.get("title", "Caso Ejecutivo"), case_md))
        _add_page_to_module(client, course_id, module_id, page)


def _add_page_to_module(client: CanvasClient, course_id: str, module_id: str, page: dict) -> None:
    page_url = page.get("url", "")
    if page_url:
        client.create_module_item(course_id, module_id, {
            "type": "Page", "page_url": page_url, "title": page.get("title", ""),
        })


def _add_quiz_to_module(client: CanvasClient, course_id: str, module_id: str, quiz_id: str, title: str) -> None:
    client.create_module_item(course_id, module_id, {
        "type": "Quiz", "content_id": quiz_id, "title": title,
    })


# ── Lambda Handler ────────────────────────────────────────────────────────────

def lambda_handler(event: dict, context: Any) -> dict:
    """
    Lambda entry point para Canvas Publisher.
    Invocado por el checkpoint handler tras estado APPROVED.
    Set CANVAS_MOCK_MODE=true to simulate without real Canvas API calls.
    """
    subject_id: str = event.get("subject_id", "")
    if not subject_id:
        return _response(400, {"error": "subject_id required"})

    mock_mode = os.environ.get("CANVAS_MOCK_MODE", "true").lower() == "true"
    logger.info("canvas_publisher_start", extra={"subject_id": subject_id, "mock_mode": mock_mode})

    try:
        # Load subject JSON directly from S3
        import boto3
        s3 = boto3.client("s3")
        bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
        obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
        subject_json = json.loads(obj["Body"].read().decode("utf-8"))

        # Create client (mock or real)
        if mock_mode:
            canvas_client = MockCanvasClient(
                base_url=os.environ.get("CANVAS_BASE_URL", "https://anahuacmerida.instructure.com"),
            )
        else:
            canvas_client = CanvasClient(
                base_url=os.environ["CANVAS_BASE_URL"],
                secret_arn=os.environ["CANVAS_SECRET_ARN"],
            )

        result = publish_course(subject_json, canvas_client)

        # Persist publication result to S3
        subject_json["publication"] = result.to_dict()
        subject_json["publication"]["mock_mode"] = mock_mode
        subject_json["pipeline_state"]["current_state"] = "PUBLISHED"
        subject_json["pipeline_state"]["state_history"].append({
            "state": "PUBLISHED", "agent": "canvas-publisher",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "llm_version": "", "result_hash": "",
        })
        subject_json["updated_at"] = datetime.now(timezone.utc).isoformat()

        s3.put_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json",
                      Body=json.dumps(subject_json, ensure_ascii=False, indent=2).encode("utf-8"),
                      ContentType="application/json")

        # Update DynamoDB
        ddb = boto3.resource("dynamodb")
        ddb.Table(os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")).put_item(Item={
            "subject_id": subject_id, "SK": "STATE",
            "current_state": "PUBLISHED",
            "subject_name": subject_json["metadata"]["subject_name"],
            "program_name": subject_json["metadata"]["program_name"],
            "updated_at": subject_json["updated_at"],
            "s3_key": f"subjects/{subject_id}/subject.json",
            "canvas_course_url": result.canvas_course_url,
        })

        # Log mock summary if applicable
        if mock_mode and hasattr(canvas_client, "get_summary"):
            summary = canvas_client.get_summary()
            logger.info("mock_canvas_summary", extra=summary)

        record_metric("CoursesPublished", 1, "Count")
        logger.info("canvas_publisher_complete", extra={
            "subject_id": subject_id,
            "course_id": result.canvas_course_id,
            "course_url": result.canvas_course_url,
            "mock_mode": mock_mode,
        })

        return _response(200, {
            "status": "PUBLISHED",
            "subject_id": subject_id,
            "canvas_course_url": result.canvas_course_url,
            "mock_mode": mock_mode,
        })

    except Exception as exc:
        logger.error("canvas_publisher_error", extra={"subject_id": subject_id, "error": str(exc)})
        return _response(500, {"error": str(exc)})


def _response(code: int, body: dict) -> dict:
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
