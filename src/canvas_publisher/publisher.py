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
    Estructura: 1 módulo por semana + módulos globales.
    """
    subject_id = subject_json["subject_id"]
    metadata = subject_json["metadata"]
    content = subject_json.get("content_package", {})
    instructional = subject_json.get("instructional_design", {})
    competencies = subject_json["academic_inputs"]["competencies"]

    course_code = f"AP-{subject_id[:8].upper()}"

    # Crear o encontrar curso
    existing = client.find_course_by_code(_CANVAS_ACCOUNT_ID, course_code)
    if existing:
        course_id = str(existing["id"])
        course_url = existing.get("html_url", "")
    else:
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

    module_urls: list[str] = []
    position = 1

    # ── Módulo 0: Carta Descriptiva + Recursos Globales ──
    mod0 = client.create_module(course_id, "Información General", position=position)
    mod0_id = str(mod0["id"])
    position += 1

    # Carta Descriptiva
    card = instructional.get("descriptive_card", {})
    if card:
        card_md = f"# Carta Descriptiva: {metadata['subject_name']}\n\n"
        card_md += f"**Objetivo General**: {card.get('general_objective', '')}\n\n"
        for so in card.get("specific_objectives", []):
            text = so.get("text", so) if isinstance(so, dict) else str(so)
            card_md += f"- {text}\n"
        page = client.create_page(course_id, format_page_payload("Carta Descriptiva", card_md))
        _add_page_to_module(client, course_id, mod0_id, page)

    # Masterclass
    mc = content.get("masterclass_script", {})
    if mc and isinstance(mc, dict):
        mc_md = f"# Masterclass: {mc.get('title', metadata['subject_name'])}\n\n"
        mc_md += f"**Duración**: {mc.get('duration_minutes', 20)} minutos\n\n"
        for sec in mc.get("structure", []):
            if isinstance(sec, dict):
                mc_md += f"## {sec.get('section', '')} ({sec.get('time', '')})\n\n"
                mc_md += f"{sec.get('content', '')}\n\n"
                if sec.get("notes"):
                    mc_md += f"*Nota: {sec['notes']}*\n\n"
        page = client.create_page(course_id, format_page_payload("Guion de Masterclass", mc_md))
        _add_page_to_module(client, course_id, mod0_id, page)

    # Reto de Aprendizaje Agéntico
    challenge = content.get("agentic_challenge", {})
    if challenge and isinstance(challenge, dict):
        ch_md = f"# {challenge.get('title', 'Reto de Aprendizaje Agentico')}\n\n"
        ch_md += f"**Semana**: {challenge.get('week', 2)}\n\n"
        ch_md += f"## Escenario\n\n{challenge.get('scenario', '')}\n\n"
        ch_md += f"## Pregunta Directiva Central\n\n{challenge.get('central_question', '')}\n\n"
        ch_md += f"## Entregable\n\n{challenge.get('deliverable', '')}\n\n"
        rubric = challenge.get("rubric", {})
        criteria = rubric.get("criteria", []) if isinstance(rubric, dict) else []
        if criteria:
            ch_md += "## Rubrica de Evaluacion\n\n"
            ch_md += "| Criterio | Peso | Excelente | Bueno | Regular | Deficiente |\n"
            ch_md += "|---|---|---|---|---|---|\n"
            for cr in criteria:
                if isinstance(cr, dict):
                    ch_md += f"| {cr.get('criterion','')} | {cr.get('weight','')} | {cr.get('excelente','')} | {cr.get('bueno','')} | {cr.get('regular','')} | {cr.get('deficiente','')} |\n"
        page = client.create_page(course_id, format_page_payload("Reto de Aprendizaje Agentico", ch_md))
        _add_page_to_module(client, course_id, mod0_id, page)

    # Guía del Facilitador
    ma = content.get("maestria_artifacts", {})
    if isinstance(ma, dict):
        fg = ma.get("facilitator_guide", {})
        sessions = fg.get("sessions", []) if isinstance(fg, dict) else []
        if sessions:
            fg_md = "# Guia del Facilitador\n\n"
            for s in sessions:
                if not isinstance(s, dict):
                    continue
                fg_md += f"## Semana {s.get('week', '')}: {s.get('objective', '')}\n\n"
                fg_md += f"**Duracion**: {s.get('duration_minutes', 90)} minutos\n\n"
                fg_md += "| Tiempo | Actividad |\n|---|---|\n"
                for step in s.get("sequence", []):
                    if isinstance(step, dict):
                        fg_md += f"| {step.get('time', '')} | {step.get('activity', '')} |\n"
                tqs = s.get("trigger_questions", [])
                if tqs:
                    fg_md += "\n**Preguntas detonadoras**:\n\n"
                    for tq in tqs:
                        fg_md += f"- {tq}\n"
                fg_md += "\n"
            page = client.create_page(course_id, format_page_payload("Guia del Facilitador", fg_md))
            _add_page_to_module(client, course_id, mod0_id, page)

    # ── Módulos semanales ──
    weekly_units = content.get("weekly_units", [])
    readings_data = content.get("executive_readings", {})
    all_readings = readings_data.get("readings", []) if isinstance(readings_data, dict) else (readings_data if isinstance(readings_data, list) else [])
    quizzes_data = content.get("quizzes", {})
    all_quizzes = quizzes_data.get("quizzes", []) if isinstance(quizzes_data, dict) else (quizzes_data if isinstance(quizzes_data, list) else [])
    all_forums = content.get("forums", [])

    # Group readings by week
    readings_by_week = {}
    for r in all_readings:
        if isinstance(r, dict):
            readings_by_week.setdefault(r.get("week", 0), []).append(r)

    # Group quizzes by week
    quizzes_by_week = {}
    for q in all_quizzes:
        if isinstance(q, dict):
            quizzes_by_week.setdefault(q.get("week", 0), []).append(q)

    # Group forums by week
    forums_by_week = {}
    for f in all_forums:
        if isinstance(f, dict):
            forums_by_week.setdefault(f.get("week", 0), []).append(f)

    # Determine weeks from weekly_units or content map
    weeks = []
    if weekly_units:
        weeks = [{"week": u.get("week"), "theme": u.get("theme", "")} for u in weekly_units]
    else:
        cmap = subject_json.get("instructional_design", {}).get("content_map", {})
        weeks = cmap.get("weeks", []) if isinstance(cmap, dict) else []

    for week_info in weeks:
        w = week_info.get("week", 0)
        theme = week_info.get("theme", f"Semana {w}")

        mod = client.create_module(course_id, f"Semana {w}: {theme}", position=position)
        mod_id = str(mod["id"])
        position += 1

        # Introduction (from weekly_units)
        unit = next((u for u in weekly_units if u.get("week") == w), None)
        if unit and unit.get("introduction"):
            intro = unit["introduction"]
            page = client.create_page(course_id, format_page_payload(
                intro.get("title", f"Introduccion Semana {w}"),
                intro.get("content_md", ""),
            ))
            _add_page_to_module(client, course_id, mod_id, page)

        # 3 Readings
        week_readings = readings_by_week.get(w, [])
        for reading in week_readings[:3]:
            page = client.create_page(course_id, format_page_payload(
                reading.get("title", ""),
                reading.get("content_md", ""),
            ))
            _add_page_to_module(client, course_id, mod_id, page)
            module_urls.append(page.get("html_url", ""))

        # Quiz
        week_quizzes = quizzes_by_week.get(w, [])
        for quiz_data in week_quizzes[:1]:
            quiz_title = quiz_data.get("title", f"Quiz Semana {w}")
            quiz_ra = quiz_data.get("ra_id", ", ".join(quiz_data.get("ra_ids", [])))
            quiz_resp = client.create_quiz(course_id, format_quiz_payload(title=quiz_title, ra_id=quiz_ra))
            quiz_id = str(quiz_resp["id"])
            for q in quiz_data.get("questions", []):
                if isinstance(q, dict):
                    client.create_quiz_question(course_id, quiz_id, format_quiz_question_payload(q))
            _add_quiz_to_module(client, course_id, mod_id, quiz_id, quiz_title)

        # Forum
        week_forums = forums_by_week.get(w, [])
        for forum in week_forums[:1]:
            forum_md = f"# {forum.get('title', f'Foro Semana {w}')}\n\n"
            case = forum.get("case", {})
            if isinstance(case, dict):
                forum_md += f"## Caso de Negocio\n\n{case.get('description', '')}\n\n"
            forum_md += "## Preguntas de Discusion\n\n"
            for qi, fq in enumerate(forum.get("questions", []), 1):
                forum_md += f"{qi}. {fq}\n\n"
            frubric = forum.get("rubric", {})
            if isinstance(frubric, dict) and frubric.get("criteria"):
                forum_md += "## Rubrica de Evaluacion\n\n"
                forum_md += "| Criterio | Peso | Excelente | Bueno | Regular | Deficiente |\n|---|---|---|---|---|---|\n"
                for cr in frubric["criteria"]:
                    if isinstance(cr, dict):
                        forum_md += f"| {cr.get('criterion','')} | {cr.get('weight','')} | {cr.get('excelente','')} | {cr.get('bueno','')} | {cr.get('regular','')} | {cr.get('deficiente','')} |\n"
            page = client.create_page(course_id, format_page_payload(
                forum.get("title", f"Foro Semana {w}"),
                forum_md,
            ))
            _add_page_to_module(client, course_id, mod_id, page)

    # ── Módulo: Dashboard de Evidencia ──
    if isinstance(ma, dict) and ma.get("evidence_dashboard", {}).get("html_content"):
        mod_ev = client.create_module(course_id, "Dashboard de Evidencia", position=position)
        position += 1
        page = client.create_page(course_id, format_page_payload(
            "Dashboard de Evidencia",
            f"# Dashboard de Evidencia\n\n{ma['evidence_dashboard']['html_content']}",
        ))
        _add_page_to_module(client, course_id, str(mod_ev["id"]), page)

    now = datetime.now(timezone.utc).isoformat()
    return PublicationResult(
        subject_id=subject_id,
        canvas_course_id=course_id,
        canvas_course_url=course_url or f"https://anahuacmerida.instructure.com/courses/{course_id}",
        module_urls=module_urls,
        published_at=now,
        status="PUBLISHED",
    )


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
