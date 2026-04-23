"""
Formateadores de contenido para Canvas API — U6.
Funciones puras — sin efectos secundarios, testeables con PBT.
"""
from __future__ import annotations

import re


def markdown_to_html(markdown: str) -> str:
    """
    Convierte Markdown básico a HTML compatible con Canvas.
    Soporta: encabezados, negrita, cursiva, listas, tablas, párrafos.
    Función pura — invariante: retorna siempre un string no vacío si input no vacío.
    """
    if not markdown:
        return ""

    html = markdown

    # Encabezados
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

    # Negrita e itálica
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # Listas
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"(<li>.*</li>)", r"<ul>\1</ul>", html, flags=re.DOTALL)

    # Separadores de tabla Markdown → ignorar
    html = re.sub(r"^\|[-| :]+\|$", "", html, flags=re.MULTILINE)

    # Filas de tabla
    def _table_row(m: re.Match) -> str:
        cells = [c.strip() for c in m.group(1).split("|") if c.strip()]
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    html = re.sub(r"^\|(.+)\|$", _table_row, html, flags=re.MULTILINE)

    # Párrafos (líneas que no son tags HTML)
    lines = html.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("<"):
            result.append(f"<p>{stripped}</p>")
        else:
            result.append(stripped)

    return "\n".join(result)


def format_page_payload(title: str, content_md: str) -> dict:
    """
    Construye el payload para Canvas Pages API.
    Función pura.
    """
    return {
        "wiki_page": {
            "title": title,
            "body": markdown_to_html(content_md),
            "published": False,
            "editing_roles": "teachers",
        }
    }


def format_quiz_payload(title: str, ra_id: str, description: str = "") -> dict:
    """Construye el payload base para Canvas Quizzes API."""
    return {
        "quiz": {
            "title": title,
            "description": description or f"Quiz de evaluación — {ra_id}",
            "quiz_type": "assignment",
            "published": False,
            "show_correct_answers": True,
            "allowed_attempts": 2,
        }
    }


def format_quiz_question_payload(question: dict) -> dict:
    """Construye el payload para una pregunta de Canvas Quiz."""
    answers = [
        {
            "answer_text": opt,
            "answer_weight": 100 if i == question.get("correct_answer", 0) else 0,
            "answer_comments": question.get("feedback", "") if i == question.get("correct_answer", 0) else "",
        }
        for i, opt in enumerate(question.get("options", []))
    ]
    return {
        "question": {
            "question_name": question.get("question", "")[:255],
            "question_text": question.get("question", ""),
            "question_type": "multiple_choice_question",
            "answers": answers,
        }
    }


def format_rubric_payload(title: str, criteria: list[str], competency_ids: list[str]) -> dict:
    """Construye el payload para Canvas Rubrics API con vinculación a competencias."""
    rubric_criteria = [
        {
            "description": criterion,
            "points": 10,
            "ratings": [
                {"description": "Excelente", "points": 10},
                {"description": "Satisfactorio", "points": 7},
                {"description": "En desarrollo", "points": 4},
                {"description": "Insuficiente", "points": 0},
            ],
        }
        for criterion in criteria
    ]
    return {
        "rubric": {
            "title": f"{title} [Competencias: {', '.join(competency_ids)}]",
            "criteria": rubric_criteria,
            "free_form_criterion_comments": False,
        },
        "rubric_association": {
            "purpose": "grading",
            "use_for_grading": True,
        },
    }


def format_apa_page_payload(bibliography: list[str]) -> dict:
    """Construye la página de bibliografía APA para Canvas."""
    items_html = "\n".join(f"<p>{ref}</p>" for ref in bibliography)
    body = f"<h2>Referencias Bibliográficas</h2>\n{items_html}"
    return {
        "wiki_page": {
            "title": "Referencias Bibliográficas (APA 7)",
            "body": body,
            "published": False,
            "editing_roles": "teachers",
        }
    }
