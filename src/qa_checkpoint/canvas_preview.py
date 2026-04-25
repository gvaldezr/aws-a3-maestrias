"""
Canvas Preview Builder — generates HTML preview of content as it would appear in Canvas LMS.
Pure function — no side effects.
"""
from __future__ import annotations

import re


def _md_to_html(md: str) -> str:
    """Simple markdown to HTML converter matching Canvas formatting."""
    if not md:
        return ""
    html = md
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
    html = re.sub(r"^\|[-| :]+\|$", "", html, flags=re.MULTILINE)

    def _row(m):
        cells = [c.strip() for c in m.group(1).split("|") if c.strip()]
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
    html = re.sub(r"^\|(.+)\|$", _row, html, flags=re.MULTILINE)

    lines = html.split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if s and not s.startswith("<"):
            out.append(f"<p>{s}</p>")
        elif s:
            out.append(s)
    return "\n".join(out)


def build_canvas_preview(subject_json: dict) -> dict:
    """Build HTML preview of all content pages as they would appear in Canvas LMS."""
    meta = subject_json.get("metadata", {})
    di = subject_json.get("instructional_design", {})
    cp = subject_json.get("content_package", {})
    research = subject_json.get("research", {})
    card = di.get("descriptive_card", {})
    objectives = di.get("learning_objectives", [])
    weeks = di.get("content_map", {}).get("weeks", []) if isinstance(di.get("content_map"), dict) else []

    er = cp.get("executive_readings", {})
    readings = er.get("readings", []) if isinstance(er, dict) else (er if isinstance(er, list) else [])
    qz = cp.get("quizzes", {})
    quizzes = qz.get("quizzes", []) if isinstance(qz, dict) else (qz if isinstance(qz, list) else [])
    ma = cp.get("maestria_artifacts", {}) if isinstance(cp.get("maestria_artifacts"), dict) else {}

    pages = []

    # 1. Carta Descriptiva
    card_html = f"<h1>{meta.get('subject_name', '')}</h1>\n"
    card_html += f"<p><strong>Programa:</strong> {meta.get('program_name', '')}</p>\n"
    card_html += f"<p><strong>Tipo:</strong> {meta.get('subject_type', '')} | <strong>Idioma:</strong> {meta.get('language', '')}</p>\n"
    if card.get("general_objective"):
        card_html += f"<h2>Objetivo General</h2>\n<p>{card['general_objective']}</p>\n"
    if objectives:
        card_html += "<h2>Objetivos de Aprendizaje</h2>\n<table><tr><th>ID</th><th>Bloom</th><th>Descripción</th><th>Competencias</th><th>RAs</th></tr>\n"
        for o in objectives:
            card_html += f"<tr><td>{o.get('objective_id','')}</td><td>{o.get('bloom_level','')}</td><td>{o.get('description','')}</td><td>{', '.join(o.get('competency_ids',[]))}</td><td>{', '.join(o.get('ra_ids',[]))}</td></tr>\n"
        card_html += "</table>\n"
    if weeks:
        card_html += "<h2>Mapa de Contenidos</h2>\n<table><tr><th>Semana</th><th>Tema</th><th>Bloom</th></tr>\n"
        for w in weeks:
            card_html += f"<tr><td>{w.get('week','')}</td><td>{w.get('theme','')}</td><td>{w.get('bloom_level','')}</td></tr>\n"
        card_html += "</table>\n"
    pages.append({"title": "Carta Descriptiva", "type": "page", "html": card_html})

    # 2. Readings
    for r in readings:
        if isinstance(r, dict):
            pages.append({"title": r.get("title", ""), "type": "page", "html": _md_to_html(r.get("content_md", ""))})

    # 3. Quizzes
    for q in quizzes:
        if not isinstance(q, dict):
            continue
        qhtml = f"<h1>Quiz — {q.get('ra_id', '')}</h1>\n"
        if q.get("ra_description"):
            qhtml += f"<p><em>{q['ra_description']}</em></p>\n"
        for qi, qq in enumerate(q.get("questions", []), 1):
            if not isinstance(qq, dict):
                continue
            qhtml += f"<h3>Pregunta {qi}</h3>\n<p>{qq.get('question','')}</p>\n<ol type='A'>\n"
            for oi, opt in enumerate(qq.get("options", [])):
                mark = " ✓" if oi == qq.get("correct_answer", -1) else ""
                qhtml += f"<li>{opt}{mark}</li>\n"
            qhtml += "</ol>\n"
            if qq.get("feedback"):
                qhtml += f"<p><em>💡 {qq['feedback']}</em></p>\n"
        pages.append({"title": f"Quiz — {q.get('ra_id','')}", "type": "quiz", "html": qhtml})

    # 4. Maestria artifacts
    if ma.get("evidence_dashboard", {}).get("html_content"):
        pages.append({"title": "Dashboard de Evidencia", "type": "page",
                       "html": f"<h1>Dashboard de Evidencia</h1>\n<table>\n{_md_to_html(ma['evidence_dashboard']['html_content'])}\n</table>"})
    if ma.get("critical_path_map", {}).get("markdown_content"):
        pages.append({"title": "Mapa de Ruta Crítica", "type": "page",
                       "html": f"<h1>Mapa de Ruta Crítica</h1>\n<table>\n{_md_to_html(ma['critical_path_map']['markdown_content'])}\n</table>"})

    cases = ma.get("executive_cases_repository", {}).get("cases", []) if isinstance(ma.get("executive_cases_repository"), dict) else []
    for c in cases:
        if not isinstance(c, dict):
            continue
        ch = f"<h1>{c.get('title','')}</h1>\n<h2>Contexto</h2>\n<p>{c.get('context','')}</p>\n"
        if c.get("questions"):
            ch += "<h2>Preguntas</h2>\n<ol>\n" + "".join(f"<li>{cq}</li>\n" for cq in c["questions"]) + "</ol>\n"
        if c.get("rubric", {}).get("criteria"):
            ch += "<h2>Rúbrica</h2>\n<ul>\n" + "".join(f"<li>{cr}</li>\n" for cr in c["rubric"]["criteria"]) + "</ul>\n"
        pages.append({"title": c.get("title", "Caso"), "type": "page", "html": ch})

    sessions = ma.get("facilitator_guide", {}).get("sessions", []) if isinstance(ma.get("facilitator_guide"), dict) else []
    if sessions:
        gh = "<h1>Guía del Facilitador</h1>\n"
        for s in sessions:
            if not isinstance(s, dict):
                continue
            gh += f"<h2>Semana {s.get('week','')}: {s.get('objective','')}</h2>\n"
            gh += f"<p><strong>Duración:</strong> {s.get('duration_minutes',90)} min</p>\n"
            gh += "<table><tr><th>Tiempo</th><th>Actividad</th></tr>\n"
            for step in s.get("sequence", []):
                gh += f"<tr><td>{step.get('time','')}</td><td>{step.get('activity','')}</td></tr>\n"
            gh += "</table>\n"
            if s.get("trigger_questions"):
                gh += "<p><strong>Preguntas detonadoras:</strong></p>\n<ul>\n"
                for tq in s["trigger_questions"]:
                    gh += f"<li>{tq}</li>\n"
                gh += "</ul>\n"
        pages.append({"title": "Guía del Facilitador", "type": "page", "html": gh})

    # 5. Bibliography
    papers = research.get("top20_papers", [])
    if papers:
        bh = "<h1>Referencias Bibliográficas</h1>\n<ol>\n"
        for p in papers:
            if isinstance(p, dict):
                auth = ", ".join(p.get("authors", [])) if isinstance(p.get("authors"), list) else str(p.get("authors", ""))
                bh += f"<li>{auth} ({p.get('year','')}). <em>{p.get('title','')}</em>. {p.get('journal','')}.</li>\n"
        bh += "</ol>\n"
        pages.append({"title": "Referencias Bibliográficas (APA)", "type": "page", "html": bh})

    return {"pages": pages, "total_pages": len(pages)}
