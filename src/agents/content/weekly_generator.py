"""
Weekly Content Generator — generates Canvas-ready content per week.
Each week = 1 Canvas Module with: Introduction, 3 Readings, 1 Quiz (8 questions), 1 Forum.
Plus global resources: Reto Agéntico, Masterclass, Carta Descriptiva, Guía Facilitador.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)


def generate_weekly_content(
    weeks: list,
    subject_name: str,
    language: str,
    papers: list,
    knowledge_matrix: list,
    learning_outcomes: list,
    objectives: list,
    competencies: list,
    generate_reading_llm=None,
    generate_quiz_llm=None,
    generate_masterclass_llm=None,
    generate_challenge_llm=None,
) -> dict:
    """Generate the complete content package organized by week for Canvas."""

    km = knowledge_matrix if isinstance(knowledge_matrix, list) else []
    km_by_topic = {}
    for km_entry in km:
        if isinstance(km_entry, dict):
            for topic in km_entry.get("syllabus_topics_covered", []):
                km_by_topic.setdefault(topic.lower().strip(), []).append(km_entry)

    total_weeks = len(weeks)
    weekly_units = []

    for week in weeks:
        w = week.get("week", 1)
        theme = week.get("theme", "")
        bloom = week.get("bloom_level", "")
        subtopics = week.get("subtopics", [])

        log.info(f"WEEKLY: Generating week {w}/{total_weeks}: {theme}")

        # Find KM concepts for this week
        theme_lower = theme.lower().strip()
        relevant_km = km_by_topic.get(theme_lower, [])
        if not relevant_km:
            theme_words = {wd for wd in theme_lower.split() if len(wd) > 4}
            for tk, entries in km_by_topic.items():
                if theme_words & {wd for wd in tk.split() if len(wd) > 4}:
                    relevant_km.extend(entries)

        concepts = []
        methodologies = []
        for kme in relevant_km:
            for c in kme.get("core_concepts", []):
                if isinstance(c, dict):
                    concepts.append(c)
            for m in kme.get("key_methodologies", []):
                if isinstance(m, str):
                    methodologies.append(m)

        theme_words_list = [wd.lower() for wd in theme.split() if len(wd) > 4]
        rel_papers = [p for p in papers if any(wd in p.get("title", "").lower() for wd in theme_words_list)][:5] or papers[:3]

        # 1. Introduction
        intro = _generate_introduction(w, total_weeks, theme, subject_name, bloom, subtopics, generate_reading_llm)
        log.info(f"WEEKLY: Week {w} intro done ({len(intro.get('content_md',''))} chars)")

        # 2. Three readings (split concepts across 3)
        readings = _generate_three_readings(w, total_weeks, theme, subject_name, bloom, subtopics, concepts, rel_papers, methodologies, generate_reading_llm)
        log.info(f"WEEKLY: Week {w} readings done ({len(readings)})")

        # 3. Quiz (8 questions for this week's theme)
        quiz = _generate_weekly_quiz(w, theme, subject_name, bloom, learning_outcomes, objectives, generate_quiz_llm)
        log.info(f"WEEKLY: Week {w} quiz done ({len(quiz.get('questions',[]))} questions)")

        # 4. Forum (case + 3 questions + rubric)
        forum = _generate_forum(w, theme, subject_name, bloom, competencies, rel_papers)
        log.info(f"WEEKLY: Week {w} forum done")

        weekly_units.append({
            "week": w,
            "theme": theme,
            "bloom_level": bloom,
            "introduction": intro,
            "readings": readings,
            "quiz": quiz,
            "forum": forum,
        })

    # Global resources
    log.info("WEEKLY: Generating global resources")

    # Masterclass
    mid_week = weeks[len(weeks) // 2] if weeks else {}
    mc_theme = mid_week.get("theme", subject_name)
    obj_descs = [o.get("description", "")[:60] for o in objectives[:3]]
    comp_ids = [c.get("competency_id", "") for c in competencies]
    masterclass = {}
    if generate_masterclass_llm:
        masterclass = generate_masterclass_llm(subject_name, mc_theme, obj_descs, papers[:5], comp_ids)
    if not masterclass or not masterclass.get("structure"):
        masterclass = _default_masterclass(subject_name, mc_theme, obj_descs, papers, comp_ids)

    # Agentic challenge
    ra_descs = [lo.get("description", "") for lo in learning_outcomes]
    w2_theme = weeks[1].get("theme", subject_name) if len(weeks) > 1 else subject_name
    challenge = {}
    if generate_challenge_llm:
        challenge = generate_challenge_llm(subject_name, ra_descs, comp_ids, w2_theme)
    if not challenge or not challenge.get("scenario"):
        challenge = _default_challenge(subject_name, ra_descs, comp_ids, w2_theme)

    return {
        "weekly_units": weekly_units,
        "masterclass_script": masterclass,
        "agentic_challenge": challenge,
        "total_weeks": total_weeks,
        "subject_name": subject_name,
    }


def _generate_introduction(w, total, theme, subject_name, bloom, subtopics, llm_fn):
    """Generate week introduction."""
    if llm_fn:
        try:
            prompt_text = (
                f"Genera una introduccion de 150-200 palabras para la Semana {w} de {total} "
                f"de la asignatura '{subject_name}'. Tema: {theme}. Nivel Bloom: {bloom}. "
                f"Subtemas: {', '.join(subtopics[:3])}. "
                f"Tono ejecutivo, prosa narrativa, contexto financiero mexicano. "
                f"Explica que aprendera el estudiante esta semana y como se conecta con la anterior."
            )
            from llm_generator import _call_llm
            content = _call_llm(prompt_text)
            return {"title": f"Introduccion Semana {w}: {theme}", "content_md": content}
        except Exception:
            pass
    # Deterministic fallback
    sub_text = ", ".join(subtopics[:3]) if subtopics else theme
    return {
        "title": f"Introduccion Semana {w}: {theme}",
        "content_md": (
            f"# Semana {w} de {total}: {theme}\n\n"
            f"**Nivel cognitivo**: {bloom}\n\n"
            f"Esta semana aborda {theme} dentro de {subject_name}. "
            f"Los subtemas incluyen: {sub_text}. "
            f"Al finalizar, el estudiante podra aplicar estos conceptos en el contexto financiero mexicano.\n"
        ),
    }


def _generate_three_readings(w, total, theme, subject_name, bloom, subtopics, concepts, papers, methods, llm_fn):
    """Generate 3 readings for a week, splitting content across them."""
    readings = []
    # Split concepts into 3 groups
    third = max(1, len(concepts) // 3)
    concept_groups = [concepts[:third], concepts[third:2*third], concepts[2*third:]]
    paper_groups = [papers[:2], papers[1:3], papers[2:4]]
    method_groups = [methods[:2], methods[2:4], methods[4:]]

    labels = ["Fundamentos", "Aplicacion", "Analisis critico"]

    for i in range(3):
        reading_concepts = concept_groups[i] if i < len(concept_groups) else []
        reading_papers = paper_groups[i] if i < len(paper_groups) else papers[:2]
        reading_methods = method_groups[i] if i < len(method_groups) else []

        if llm_fn:
            try:
                content = llm_fn(w, total, f"{theme} - {labels[i]}", subject_name, bloom,
                                 subtopics, reading_concepts, reading_papers, reading_methods)
                readings.append({
                    "week": w, "reading_num": i + 1,
                    "title": f"Semana {w} Lectura {i+1}: {theme} - {labels[i]}",
                    "bloom_level": bloom, "content_md": content, "language": "ES",
                })
                continue
            except Exception:
                pass

        # Deterministic fallback
        concept_text = "\n".join(f"### {c.get('concept','')}\n{c.get('definition','')}\n" for c in reading_concepts[:3])
        paper_text = "\n".join(f"- {p.get('title','')[:50]} ({p.get('year','')})" for p in reading_papers[:2])
        readings.append({
            "week": w, "reading_num": i + 1,
            "title": f"Semana {w} Lectura {i+1}: {theme} - {labels[i]}",
            "bloom_level": bloom, "language": "ES",
            "content_md": (
                f"# Lectura {i+1}: {theme} - {labels[i]}\n\n"
                f"**Semana {w} de {total}** | **Nivel**: {bloom}\n\n"
                f"## Conceptos\n{concept_text or f'Tema: {theme}'}\n\n"
                f"## Referencias\n{paper_text}\n\n"
                f"## Reflexion\nComo aplica {theme.lower()} en su contexto profesional?\n"
            ),
        })
    return readings


def _generate_weekly_quiz(w, theme, subject_name, bloom, learning_outcomes, objectives, llm_fn):
    """Generate 1 quiz per week with 8 questions."""
    ra_descs = [lo.get("description", "") for lo in learning_outcomes if isinstance(lo, dict)]
    obj_descs = [o.get("description", "") for o in objectives if isinstance(o, dict)]
    ra_ids = [lo.get("ra_id", "") for lo in learning_outcomes if isinstance(lo, dict)]

    if llm_fn:
        try:
            questions = llm_fn(f"{subject_name} - Semana {w}: {theme}", ra_descs, obj_descs)
            if questions and len(questions) >= 6:
                return {
                    "quiz_id": f"QUIZ-S{w}",
                    "title": f"Quiz Semana {w}: {theme}",
                    "week": w, "type": "critical_reasoning",
                    "total_questions": len(questions),
                    "ra_ids": ra_ids,
                    "questions": questions,
                }
        except Exception:
            pass

    # Deterministic fallback (4 questions)
    questions = [
        {"question_id": f"S{w}-Q{i+1}", "bloom_level": ["RECORDAR","COMPRENDER","ANALIZAR","EVALUAR"][i],
         "question": f"Pregunta {i+1} sobre {theme} en {subject_name}",
         "options": ["Respuesta correcta", "Distractor A", "Distractor B", "Distractor C"],
         "correct_answer": 0, "feedback": f"Retroalimentacion sobre {theme}."}
        for i in range(min(8, 4))
    ]
    return {"quiz_id": f"QUIZ-S{w}", "title": f"Quiz Semana {w}: {theme}", "week": w,
            "type": "critical_reasoning", "total_questions": len(questions), "ra_ids": ra_ids, "questions": questions}


def _generate_forum(w, theme, subject_name, bloom, competencies, papers):
    """Generate a discussion forum with business case, 3 questions, and peer review rubric."""
    comp_ids = [c.get("competency_id", "") for c in competencies if isinstance(c, dict)]
    paper_ref = papers[0].get("title", "")[:50] if papers else "investigacion reciente"

    return {
        "forum_id": f"FORO-S{w}",
        "title": f"Foro Semana {w}: Caso de Negocio - {theme}",
        "week": w,
        "case": {
            "title": f"Caso: {theme} en el sector financiero mexicano",
            "description": (
                f"Una empresa del sector financiero mexicano regulada por la CNBV enfrenta un reto "
                f"relacionado con {theme.lower()}. El director financiero debe tomar una decision "
                f"estrategica considerando el marco regulatorio vigente (CNBV, Banxico, NIF) y la "
                f"evidencia academica disponible, incluyendo hallazgos de '{paper_ref}'."
            ),
        },
        "questions": [
            f"Analice las variables financieras clave que impactan {theme.lower()} en el contexto mexicano. Fundamente con evidencia academica.",
            f"Proponga una estrategia para abordar el reto planteado. Justifique su decision con al menos 2 referencias del corpus academico.",
            f"Evalue criticamente la propuesta de al menos un companero. Identifique fortalezas, areas de mejora y sugiera alternativas fundamentadas.",
        ],
        "rubric": {
            "title": f"Rubrica de Evaluacion - Foro Semana {w}",
            "criteria": [
                {
                    "criterion": "Pertinencia de la respuesta",
                    "weight": "40%",
                    "excelente": "Respuesta fundamentada en evidencia academica Q1/Q2 con aplicacion directa al caso mexicano",
                    "bueno": "Respuesta con referencias academicas y vinculacion parcial al contexto",
                    "regular": "Respuesta generica sin fundamentacion academica solida",
                    "deficiente": "Respuesta sin relacion con el caso o sin evidencia",
                },
                {
                    "criterion": "Retroalimentacion entre pares",
                    "weight": "30%",
                    "excelente": "Retroalimentacion constructiva con alternativas fundamentadas y referencias adicionales",
                    "bueno": "Retroalimentacion con observaciones pertinentes y sugerencias",
                    "regular": "Retroalimentacion superficial sin aporte sustantivo",
                    "deficiente": "Sin retroalimentacion o comentarios irrelevantes",
                },
                {
                    "criterion": "Calidad argumentativa",
                    "weight": "30%",
                    "excelente": "Argumento logico con premisas, evidencia y conclusion coherentes",
                    "bueno": "Estructura argumentativa clara con gaps menores",
                    "regular": "Ideas desconectadas o saltos logicos",
                    "deficiente": "Sin estructura argumentativa",
                },
            ],
            "competency_ids": comp_ids,
        },
    }


def _default_masterclass(subject_name, theme, objectives, papers, comp_ids):
    """Deterministic masterclass fallback."""
    paper_refs = "; ".join(f"{p.get('title','')[:40]} ({p.get('year','')})" for p in papers[:3])
    return {
        "title": f"Masterclass: {subject_name}",
        "duration_minutes": 20, "theme": theme, "total_slides": 8,
        "competencies_covered": ", ".join(comp_ids),
        "structure": [
            {"section": "Gancho directivo", "time": "0:00-2:00", "duration_minutes": 2,
             "content": f"[SLIDE: Titulo] Bienvenidos. Hoy: {theme}. [DATO EN PANTALLA] {paper_refs[:60]}",
             "notes": "Pregunta provocadora del sector financiero mexicano."},
            {"section": "Desarrollo conceptual con caso", "time": "2:00-16:00", "duration_minutes": 14,
             "content": f"[SLIDE: Marco] Objetivos: {'; '.join(objectives[:2])}. [CASO VISUAL] Institucion financiera mexicana.",
             "notes": "Alternar teoria y caso practico."},
            {"section": "Sintesis y decision", "time": "16:00-20:00", "duration_minutes": 4,
             "content": f"[SLIDE: Sintesis] Conceptos clave de {theme}. Contexto CNBV/Banxico.",
             "notes": "Conectar con reto agentico."},
            {"section": "Llamada a la accion", "time": "20:00-22:00", "duration_minutes": 2,
             "content": "[SLIDE: Siguiente paso] Complete el reto de aprendizaje agentico.",
             "notes": "Vincular con lecturas y foro."},
        ],
    }


def _default_challenge(subject_name, ra_descs, comp_ids, week_theme):
    """Deterministic agentic challenge fallback."""
    return {
        "title": f"Reto de Aprendizaje Agentico: {subject_name}",
        "week": 2,
        "scenario": (
            f"Usted es director de planeacion financiera de una empresa del sector financiero mexicano "
            f"que cotiza en la BMV. La CNBV ha emitido nuevas disposiciones que impactan {week_theme.lower()}. "
            f"Debe presentar un analisis fundamentado al consejo de administracion."
        ),
        "central_question": f"Que estrategia financiera recomendaria para {week_theme.lower()} en el contexto actual?",
        "deliverable": "Documento ejecutivo de 1-2 paginas con diagnostico, analisis y recomendacion.",
        "rubric": {"criteria": [
            {"criterion": "Fundamentacion en evidencia", "weight": "25%", "excelente": "3+ papers Q1/Q2", "bueno": "2 papers", "regular": "1 paper", "deficiente": "Sin referencias"},
            {"criterion": "Coherencia argumentativa", "weight": "25%", "excelente": "Logica impecable", "bueno": "Clara con gaps menores", "regular": "Desconectada", "deficiente": "Sin estructura"},
            {"criterion": "Pertinencia regulatoria", "weight": "25%", "excelente": "CNBV/Banxico/NIF integrados", "bueno": "Mencion parcial", "regular": "Generica", "deficiente": "Ignora regulacion"},
            {"criterion": "Claridad directiva", "weight": "25%", "excelente": "Accionable con metricas", "bueno": "Clara", "regular": "Vaga", "deficiente": "Incoherente"},
        ]},
    }
