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
    course_name = metadata["subject_name"]

    # Crear o encontrar curso
    existing = client.find_course_by_code(_CANVAS_ACCOUNT_ID, course_code)
    if existing:
        course_id = str(existing["id"])
        course_url = existing.get("html_url", "")
    else:
        course_resp = client.create_course(_CANVAS_ACCOUNT_ID, {
            "course": {
                "name": course_name,
                "course_code": f"MADTFIN-{course_name[:30].replace(' ', '-')}",
                "workflow_state": "unpublished",
                "language": metadata.get("language", "es").lower()[:2],
            }
        })
        course_id = str(course_resp["id"])
        course_url = course_resp.get("html_url", "")
        logger.info("canvas_course_created", extra={"subject_id": subject_id, "course_id": course_id})

    try:
        from html_helpers import rubric_to_html, schedule_to_html
    except ImportError:
        from src.canvas_publisher.html_helpers import rubric_to_html, schedule_to_html

    module_urls: list[str] = []
    position = 1

    # ── Módulo 0: Información General ──
    mod0 = client.create_module(course_id, "Informacion General", position=position)
    mod0_id = str(mod0["id"])
    position += 1

    # Carta Descriptiva
    card = instructional.get("descriptive_card", {})
    objectives = instructional.get("learning_objectives", [])
    content_map_weeks = instructional.get("content_map", {}).get("weeks", []) if isinstance(instructional.get("content_map"), dict) else []

    card_html = f"<h1>Carta Descriptiva: {metadata['subject_name']}</h1>"
    card_html += f"<p><strong>Programa</strong>: {metadata.get('program_name', '')}</p>"
    card_html += f"<p><strong>Tipo</strong>: {metadata.get('subject_type', '')} | <strong>Idioma</strong>: {metadata.get('language', '')}</p>"

    if card.get("general_objective"):
        card_html += f"<h2>Objetivo General</h2><p>{card['general_objective']}</p>"

    if objectives:
        card_html += "<h2>Objetivos de Aprendizaje</h2>"
        card_html += '<table style="width:100%;border-collapse:collapse;margin:1rem 0;">'
        card_html += '<thead><tr style="background:#394B58;color:white;">'
        card_html += '<th style="padding:8px;">ID</th><th style="padding:8px;">Nivel Bloom</th>'
        card_html += '<th style="padding:8px;">Descripcion</th><th style="padding:8px;">Competencias</th>'
        card_html += '<th style="padding:8px;">RAs</th></tr></thead><tbody>'
        for o in objectives:
            if not isinstance(o, dict):
                continue
            card_html += '<tr style="border-bottom:1px solid #E2E8F0;">'
            card_html += f'<td style="padding:8px;font-weight:bold;">{o.get("objective_id", "")}</td>'
            card_html += f'<td style="padding:8px;text-align:center;">{o.get("bloom_level", "")}</td>'
            card_html += f'<td style="padding:8px;">{o.get("description", "")}</td>'
            card_html += f'<td style="padding:8px;">{", ".join(o.get("competency_ids", []))}</td>'
            card_html += f'<td style="padding:8px;">{", ".join(o.get("ra_ids", []))}</td>'
            card_html += '</tr>'
        card_html += '</tbody></table>'

    if card.get("specific_objectives"):
        card_html += "<h2>Objetivos Especificos</h2><ol>"
        for so in card.get("specific_objectives", []):
            text = so.get("text", so) if isinstance(so, dict) else str(so)
            card_html += f"<li>{text}</li>"
        card_html += "</ol>"

    if content_map_weeks:
        card_html += "<h2>Mapa de Contenidos</h2>"
        card_html += '<table style="width:100%;border-collapse:collapse;margin:1rem 0;">'
        card_html += '<thead><tr style="background:#394B58;color:white;">'
        card_html += '<th style="padding:8px;">Semana</th><th style="padding:8px;">Tema</th>'
        card_html += '<th style="padding:8px;">Nivel Bloom</th></tr></thead><tbody>'
        for w in content_map_weeks:
            if not isinstance(w, dict):
                continue
            card_html += f'<tr style="border-bottom:1px solid #E2E8F0;">'
            card_html += f'<td style="padding:8px;text-align:center;">{w.get("week", "")}</td>'
            card_html += f'<td style="padding:8px;">{w.get("theme", "")}</td>'
            card_html += f'<td style="padding:8px;text-align:center;">{w.get("bloom_level", "")}</td>'
            card_html += '</tr>'
        card_html += '</tbody></table>'

    if card.get("evaluation_criteria"):
        card_html += "<h2>Criterios de Evaluacion</h2><ul>"
        ec = card["evaluation_criteria"]
        if isinstance(ec, dict):
            for k, v in ec.items():
                if isinstance(v, dict):
                    card_html += f"<li><strong>{k}</strong>: {v.get('instrument', '')} ({v.get('weight_percentage', '')}%) - Nivel {v.get('bloom_level', '')}</li>"
                else:
                    card_html += f"<li><strong>{k}</strong>: {v}</li>"
        card_html += "</ul>"

    page = client.create_page(course_id, {"wiki_page": {"title": "Carta Descriptiva", "body": card_html, "published": False}})
    _add_page_to_module(client, course_id, mod0_id, page)

    # Masterclass
    mc = content.get("masterclass_script", {})
    if mc and isinstance(mc, dict):
        mc_html = f"<h1>{mc.get('title', 'Masterclass')}</h1>"
        mc_html += f"<p><strong>Duracion</strong>: {mc.get('duration_minutes', 20)} minutos</p>"
        for sec in mc.get("structure", []):
            if isinstance(sec, dict):
                mc_html += f"<h2>{sec.get('section', '')} ({sec.get('time', '')})</h2>"
                mc_html += f"<p>{sec.get('content', '')}</p>"
                if sec.get("notes"):
                    mc_html += f"<p><em>{sec['notes']}</em></p>"
        page = client.create_page(course_id, {"wiki_page": {"title": "Guion de Masterclass", "body": mc_html, "published": False}})
        _add_page_to_module(client, course_id, mod0_id, page)

    # Guía del Facilitador
    ma = content.get("maestria_artifacts", {})
    if isinstance(ma, dict):
        fg = ma.get("facilitator_guide", {})
        sessions = fg.get("sessions", []) if isinstance(fg, dict) else []
        if sessions:
            fg_html = "<h1>Guia del Facilitador</h1>"
            for s in sessions:
                if not isinstance(s, dict):
                    continue
                fg_html += f"<h2>Semana {s.get('week', '')}: {s.get('objective', '')}</h2>"
                fg_html += f"<p><strong>Duracion</strong>: {s.get('duration_minutes', 90)} minutos</p>"
                fg_html += schedule_to_html(s.get("sequence", []))
                tqs = s.get("trigger_questions", [])
                if tqs:
                    fg_html += "<p><strong>Preguntas detonadoras</strong>:</p><ul>"
                    for tq in tqs:
                        fg_html += f"<li>{tq}</li>"
                    fg_html += "</ul>"
            page = client.create_page(course_id, {"wiki_page": {"title": "Guia del Facilitador", "body": fg_html, "published": False}})
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
            forum_html = f"<h1>{forum.get('title', f'Foro Semana {w}')}</h1>"
            case = forum.get("case", {})
            if isinstance(case, dict):
                forum_html += f"<h2>Caso de Negocio</h2><p>{case.get('description', '')}</p>"
            forum_html += "<h2>Preguntas de Discusion</h2><ol>"
            for fq in forum.get("questions", []):
                forum_html += f"<li>{fq}</li>"
            forum_html += "</ol>"
            frubric = forum.get("rubric", {})
            if isinstance(frubric, dict) and frubric.get("criteria"):
                forum_html += "<h2>Rubrica de Evaluacion</h2>"
                forum_html += rubric_to_html(frubric["criteria"])
            page = client.create_page(course_id, {"wiki_page": {"title": forum.get("title", f"Foro Semana {w}"), "body": forum_html, "published": False}})
            _add_page_to_module(client, course_id, mod_id, page)

    # ── Módulo: Reto de Aprendizaje Agéntico ──
    challenge = content.get("agentic_challenge", {})
    if challenge and isinstance(challenge, dict) and challenge.get("scenario"):
        mod_reto = client.create_module(course_id, "Reto de Aprendizaje Agentico", position=position)
        position += 1
        ch_html = f"<h1>{challenge.get('title', 'Reto de Aprendizaje Agentico')}</h1>"
        ch_html += f"<p><strong>Semana</strong>: {challenge.get('week', 2)}</p>"
        ch_html += f"<h2>Escenario</h2><p>{challenge.get('scenario', '')}</p>"
        ch_html += f"<h2>Pregunta Directiva Central</h2><p><strong>{challenge.get('central_question', '')}</strong></p>"
        ch_html += f"<h2>Entregable</h2><p>{challenge.get('deliverable', '')}</p>"
        ch_rubric = challenge.get("rubric", {})
        ch_criteria = ch_rubric.get("criteria", []) if isinstance(ch_rubric, dict) else []
        if ch_criteria:
            ch_html += "<h2>Rubrica de Evaluacion</h2>"
            ch_html += rubric_to_html(ch_criteria)
        page = client.create_page(course_id, {"wiki_page": {"title": "Reto de Aprendizaje Agentico", "body": ch_html, "published": False}})
        _add_page_to_module(client, course_id, str(mod_reto["id"]), page)

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
