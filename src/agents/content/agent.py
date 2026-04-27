"""
Agente Content — AgentCore Runtime + Strands SDK.
Fase 4: Generación de Recursos — paquete multimedia + 4 artefactos Maestría.

Patrón: BedrockAgentCoreApp + @app.entrypoint + lazy Strands Agent
"""
from __future__ import annotations

import json
import os
import re

import boto3
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext

app = BedrockAgentCoreApp()

_content_agent = None


def _get_agent():
    """Lazy init — only create Strands Agent on first invocation."""
    global _content_agent
    if _content_agent is not None:
        return _content_agent

    from strands import Agent, tool
    from strands.models import BedrockModel

    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-6",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        temperature=0.3,
        max_tokens=32768,
    )

    @tool
    def generate_executive_readings(weekly_map: list, subject_name: str, language: str, papers: list = None, knowledge_matrix: list = None) -> dict:
        """Generate executive readings for each week of the course map.

        Args:
            weekly_map: List of week dicts with week, theme, bloom_level, activities, subtopics
            subject_name: Name of the subject
            language: Content language: ES, EN, or BILINGUAL
            papers: Optional list of research papers to reference in readings
            knowledge_matrix: Optional knowledge matrix with core_concepts and methodologies
        """
        def _ensure_dicts(items):
            result = []
            for item in (items or []):
                if isinstance(item, dict):
                    result.append(item)
                elif isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            result.append(parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass
            return result

        weekly_map = _ensure_dicts(weekly_map)
        papers = _ensure_dicts(papers)
        knowledge_matrix = _ensure_dicts(knowledge_matrix) if knowledge_matrix else []
        readings = []
        total_weeks = len(weekly_map)

        # Index KM concepts by syllabus topic for matching
        km_by_topic = {}
        for km_entry in knowledge_matrix:
            for topic in km_entry.get("syllabus_topics_covered", []):
                km_by_topic.setdefault(topic.lower().strip(), []).append(km_entry)

        for week in weekly_map:
            w = week.get("week", 1)
            theme = week.get("theme", "")
            bloom = week.get("bloom_level", "")
            subtopics = week.get("subtopics", [])
            activities = week.get("activities", [])

            # Find relevant KM entries for this week's theme
            theme_lower = theme.lower().strip()
            relevant_km = km_by_topic.get(theme_lower, [])
            if not relevant_km:
                # Fuzzy match: find KM entries whose topics share words with this theme
                theme_words = {w for w in theme_lower.split() if len(w) > 4}
                for topic_key, entries in km_by_topic.items():
                    topic_words = {w for w in topic_key.split() if len(w) > 4}
                    if theme_words & topic_words:
                        relevant_km.extend(entries)
                # Deduplicate
                seen = set()
                unique_km = []
                for e in relevant_km:
                    eid = e.get("ra_id", "")
                    if eid not in seen:
                        seen.add(eid)
                        unique_km.append(e)
                relevant_km = unique_km

            # Collect concepts and methodologies from KM
            concepts = []
            methodologies = []
            for km_entry in relevant_km:
                for c in km_entry.get("core_concepts", []):
                    if isinstance(c, dict):
                        concepts.append(c)
                for m in km_entry.get("key_methodologies", []):
                    if isinstance(m, str):
                        methodologies.append(m)

            # Find relevant papers
            theme_words = [word.lower() for word in theme.split() if len(word) > 4]
            relevant_papers = []
            for p in papers:
                title_lower = p.get("title", "").lower()
                syllabus_topic = p.get("syllabus_topic", "").lower()
                if any(word in title_lower or word in syllabus_topic for word in theme_words):
                    relevant_papers.append(p)
            relevant_papers = relevant_papers[:5] or papers[:3]

            # Build rich content
            sections = []

            # Header
            sections.append(f"# Lectura Ejecutiva — Semana {w} de {total_weeks}: {theme}")
            sections.append(f"\n**Asignatura**: {subject_name}")
            sections.append(f"**Nivel cognitivo**: {bloom} (Taxonomía de Bloom)")
            sections.append(f"**Semana**: {w} de {total_weeks}\n")

            # Introduction
            sections.append("## Introducción")
            bloom_action = {
                "RECORDAR": "identificar y reconocer los conceptos fundamentales",
                "COMPRENDER": "comprender y explicar las relaciones entre conceptos",
                "APLICAR": "aplicar los conceptos en contextos profesionales reales",
                "ANALIZAR": "descomponer y examinar críticamente las variables involucradas",
                "EVALUAR": "juzgar, fundamentar y defender decisiones con evidencia",
                "CREAR": "diseñar y proponer soluciones originales e integradoras",
            }.get(bloom, "desarrollar competencias en")
            sections.append(
                f"Esta semana aborda **{theme}** dentro del programa de {subject_name}. "
                f"El nivel cognitivo esperado es **{bloom}**, lo que implica que el estudiante "
                f"deberá {bloom_action} presentados en esta lectura.\n"
            )

            # Core concepts from Knowledge Matrix
            if concepts:
                sections.append("## Conceptos Clave")
                for i, c in enumerate(concepts[:6], 1):
                    concept_name = c.get("concept", "")
                    definition = c.get("definition", "")
                    supporting = c.get("supporting_papers", [])
                    comp_ids = c.get("competencies", [])

                    sections.append(f"\n### {i}. {concept_name}")
                    if definition:
                        sections.append(f"\n{definition}\n")
                    if comp_ids:
                        sections.append(f"*Competencias vinculadas: {', '.join(comp_ids)}*\n")
                    if supporting:
                        sections.append("**Evidencia académica:**")
                        for sp in supporting[:3]:
                            sections.append(f"- {sp}")
                        sections.append("")
            elif subtopics:
                sections.append("## Contenido Temático")
                for i, st in enumerate(subtopics, 1):
                    sections.append(f"\n### {i}. {st}")
                    sections.append(
                        f"Este subtema examina los aspectos fundamentales de {st.lower()} "
                        f"en el contexto de {subject_name.lower()}.\n"
                    )

            # Methodologies
            if methodologies:
                sections.append("## Metodologías y Herramientas")
                sections.append("Las siguientes metodologías son aplicables a los conceptos de esta semana:\n")
                for m in methodologies[:8]:
                    sections.append(f"- {m}")
                sections.append("")

            # Academic evidence from papers
            if relevant_papers:
                sections.append("## Evidencia Académica de Vanguardia")
                for p in relevant_papers[:4]:
                    authors = p.get("authors", [""])
                    author_str = authors[0] if isinstance(authors, list) and authors else str(authors)
                    finding = p.get("key_finding", "")
                    sections.append(
                        f"- **{p.get('title', '')}** ({author_str}, {p.get('year', '')}). "
                        f"*{p.get('journal', '')}*. {finding}\n"
                    )

            # Professional application
            sections.append("## Aplicación Profesional")
            sections.append(
                f"En el ejercicio profesional, los conceptos de {theme.lower()} se aplican "
                f"directamente en la toma de decisiones estratégicas. El egresado utilizará "
                f"estos conocimientos para analizar situaciones complejas, evaluar alternativas "
                f"y fundamentar sus recomendaciones ante la alta dirección.\n"
            )

            # Activities
            if activities:
                sections.append("## Actividades de Aprendizaje")
                for a in activities:
                    sections.append(f"- {a}")
                sections.append("")

            # Reflection questions
            sections.append("## Preguntas de Reflexión")
            sections.append(f"1. ¿Cómo se relaciona {theme.lower()} con su experiencia profesional actual?")
            sections.append(f"2. ¿Qué decisiones estratégicas en su organización podrían beneficiarse de estos conceptos?")
            sections.append(f"3. ¿Cómo integraría la evidencia académica presentada en su práctica profesional?\n")

            # References
            if relevant_papers:
                sections.append("## Referencias")
                for p in relevant_papers[:5]:
                    authors = p.get("authors", [""])
                    author_str = authors[0] if isinstance(authors, list) and authors else str(authors)
                    sections.append(
                        f"- {author_str} ({p.get('year', '')}). *{p.get('title', '')}*. {p.get('journal', '')}."
                    )

            content = "\n".join(sections)

            if language == "BILINGUAL":
                content += f"\n\n---\n# Executive Reading — Week {w}: {theme}\n\n[English version available upon request]"

            title = f"Semana {w}: {theme}" if language == "ES" else f"Semana {w} / Week {w}: {theme}"
            readings.append({
                "week": w,
                "title": title,
                "bloom_level": bloom,
                "content_md": content,
                "language": language,
                "activities": activities,
            })
        return {"readings": readings}

    @tool
    def generate_quizzes(learning_outcomes: list, subject_name: str, language: str, objectives: list = None, syllabus: str = "") -> dict:
        """Generate quizzes with minimum 3 questions per learning outcome.

        Args:
            learning_outcomes: List of dicts with ra_id and description
            subject_name: Name of the subject
            language: Content language
            objectives: Optional list of learning objectives from DI agent
            syllabus: Optional syllabus text for context
        """
        def _ensure_dicts(items):
            result = []
            for item in (items or []):
                if isinstance(item, dict):
                    result.append(item)
                elif isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            result.append(parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass
            return result

        learning_outcomes = _ensure_dicts(learning_outcomes)
        objectives = _ensure_dicts(objectives)
        quizzes = []
        for lo in learning_outcomes:
            ra_id = lo["ra_id"]
            ra_desc = lo["description"]

            # Find matching objectives for richer question context
            related_objs = [o for o in objectives if ra_id in o.get("ra_ids", [])]
            obj_context = related_objs[0].get("description", "") if related_objs else ra_desc

            questions = [
                {
                    "question_id": f"{ra_id}-Q1",
                    "question": f"En el contexto de {subject_name}, ¿cuál es el objetivo principal de '{ra_desc[:80]}'?",
                    "options": [
                        f"Aplicar {obj_context[:60]} para la toma de decisiones",
                        "Memorizar definiciones teóricas sin aplicación práctica",
                        "Replicar modelos existentes sin análisis crítico",
                        "Delegar el análisis a herramientas automatizadas"
                    ],
                    "correct_answer": 0,
                    "feedback": f"Correcto — el resultado de aprendizaje {ra_id} se enfoca en la aplicación práctica en {subject_name}."
                },
                {
                    "question_id": f"{ra_id}-Q2",
                    "question": f"¿Cómo se aplica '{ra_desc[:60]}' en un contexto profesional de {subject_name}?",
                    "options": [
                        "Mediante análisis de datos y modelos para sustentar decisiones estratégicas",
                        "Solo a través de reportes descriptivos sin análisis",
                        "Exclusivamente con herramientas de ofimática básica",
                        "Sin considerar el contexto organizacional"
                    ],
                    "correct_answer": 0,
                    "feedback": f"La aplicación profesional de {ra_id} implica decisiones estratégicas basadas en evidencia."
                },
                {
                    "question_id": f"{ra_id}-Q3",
                    "question": f"¿Qué tipo de evidencia académica respalda las prácticas de '{ra_desc[:60]}'?",
                    "options": [
                        "Investigación publicada en revistas Q1/Q2 con revisión por pares",
                        "Opiniones de expertos sin respaldo empírico",
                        "Artículos de divulgación general sin rigor metodológico",
                        "Datos anecdóticos de casos aislados"
                    ],
                    "correct_answer": 0,
                    "feedback": "La evidencia de investigación académica de alto impacto (Q1/Q2) es el estándar para programas de maestría."
                },
            ]
            quizzes.append({"ra_id": ra_id, "ra_description": ra_desc, "questions": questions})
        return {"quizzes": quizzes}

    @tool
    def generate_maestria_artifacts(papers: list, subject_name: str, competencies: list, language: str, weekly_map: list = None, learning_outcomes: list = None) -> dict:
        """Generate the 4 mandatory Maestría artifacts.

        Args:
            papers: Top 20 papers from Scholar agent
            subject_name: Name of the subject
            competencies: Program competencies
            language: Content language
            weekly_map: Optional weekly content map for facilitator guide
            learning_outcomes: Optional learning outcomes for case rubrics
        """
        weekly_map = weekly_map or []
        learning_outcomes = learning_outcomes or []

        # Coerce string items to dicts (LLM sometimes passes JSON strings)
        def _ensure_dicts(items: list) -> list:
            result = []
            for item in items:
                if isinstance(item, dict):
                    result.append(item)
                elif isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            result.append(parsed)
                    except (json.JSONDecodeError, TypeError):
                        pass
            return result

        papers = _ensure_dicts(papers)
        competencies = _ensure_dicts(competencies)
        weekly_map = _ensure_dicts(weekly_map)
        learning_outcomes = _ensure_dicts(learning_outcomes)

        # 1. Dashboard de Evidencia — use ACTUAL papers
        rows = ["| # | Título | Año | Revista | Hallazgo |", "|---|--------|-----|---------|----------|"]
        for i, p in enumerate(papers[:20], 1):
            title = p.get("title", "")[:60]
            year = p.get("year", "")
            journal = p.get("journal", "")[:35]
            finding = p.get("key_finding", "")[:50]
            rows.append(f"| {i} | {title} | {year} | {journal} | {finding} |")

        # 2. Mapa de Ruta Crítica — use actual weeks
        num_weeks = len(weekly_map) if weekly_map else 3
        critical_rows = ["| Semana | Actividad | Entregable | Criterio |", "|---|---|---|---|"]
        for w in weekly_map[:num_weeks]:
            week_num = w.get("week", "")
            theme = w.get("theme", "")[:40]
            bloom = w.get("bloom_level", "")
            critical_rows.append(
                f"| {week_num} | Estudio: {theme} | Análisis aplicado | Nivel {bloom} alcanzado |"
            )
        critical_path = "\n".join(critical_rows)

        # 3. Casos Ejecutivos — subject-specific
        comp_ids = [c["competency_id"] for c in competencies]
        ra_ids = [lo["ra_id"] for lo in learning_outcomes] if learning_outcomes else ["RA1"]
        cases = [{
            "case_id": "CASE-001",
            "title": f"Caso Ejecutivo: Aplicación de {subject_name}",
            "context": f"Una organización del sector financiero requiere implementar técnicas de {subject_name.lower()} para optimizar su toma de decisiones estratégicas.",
            "data": f"Datos financieros históricos, indicadores de mercado, y variables macroeconómicas relevantes para {subject_name}.",
            "questions": [
                f"¿Cómo aplicaría las técnicas de {subject_name.lower()} para resolver este problema?",
                "¿Qué métricas utilizaría para evaluar la efectividad de la solución propuesta?",
                "¿Qué riesgos identifica y cómo los mitigaría?",
                "¿Cómo comunicaría los resultados a la alta dirección?"
            ],
            "rubric": {
                "criteria": [
                    "Análisis del problema (25%)",
                    "Aplicación metodológica (30%)",
                    "Propuesta de solución (25%)",
                    "Comunicación ejecutiva (20%)"
                ],
                "competency_ids": comp_ids,
                "ra_ids": ra_ids,
            }
        }]

        # 4. Guía del Facilitador — match actual weeks
        sessions = []
        for w in weekly_map:
            week_num = w.get("week", 1)
            theme = w.get("theme", "")
            bloom = w.get("bloom_level", "")
            activities = w.get("activities", [])
            sessions.append({
                "week": week_num,
                "duration_minutes": 90,
                "objective": f"Semana {week_num}: {theme} — Nivel {bloom}",
                "sequence": [
                    {"time": "0-10min", "activity": "Apertura y conexión con semana anterior"},
                    {"time": "10-35min", "activity": f"Exposición: {theme}"},
                    {"time": "35-65min", "activity": f"Caso práctico aplicado a {subject_name}"},
                    {"time": "65-80min", "activity": "Discusión y síntesis grupal"},
                    {"time": "80-90min", "activity": "Cierre y asignación de trabajo independiente"},
                ],
                "trigger_questions": [
                    f"¿Cómo se relaciona {theme.lower()} con su experiencia profesional?",
                    f"¿Qué decisiones financieras podrían beneficiarse de {theme.lower()}?",
                ],
                "formative_criteria": f"Participación activa y vinculación con competencias {', '.join(comp_ids)}"
            })
        # Fallback if no weekly_map
        if not sessions:
            sessions = [{"week": w, "duration_minutes": 90,
                         "objective": f"Semana {w} de {subject_name}",
                         "sequence": [{"time": "0-10min", "activity": "Apertura"}, {"time": "10-40min", "activity": "Exposición"},
                                      {"time": "40-70min", "activity": "Caso práctico"}, {"time": "70-90min", "activity": "Cierre"}],
                         "trigger_questions": [f"¿Cómo conecta con su experiencia?"],
                         "formative_criteria": "Participación y vinculación con competencias"} for w in range(1, 5)]

        return {
            "evidence_dashboard": {"html_content": "\n".join(rows), "papers_indexed": len(papers)},
            "critical_path_map": {"markdown_content": critical_path},
            "executive_cases_repository": {"cases": cases},
            "facilitator_guide": {"sessions": sessions},
        }

    _content_agent = Agent(
        model=model,
        tools=[generate_executive_readings, generate_quizzes, generate_maestria_artifacts],
        system_prompt=(
            "You are Content, a content generation agent. "
            "Call all 3 tools with the data from the prompt, then return a single JSON block. "
            "Format: ```json\n{...}\n``` with keys: executive_readings, quizzes, maestria_artifacts. "
            "Use EXACT IDs from input. Subject name must match input exactly. No extra text."
        ),
    )
    return _content_agent


def _load_subject_context(subject_id: str) -> dict:
    """Load the subject JSON from S3 to get all prior pipeline results."""
    bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
    s3 = boto3.client("s3")
    try:
        obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
        return json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return {}


def _build_content_prompt(subject_id: str, sj: dict) -> str:
    """Build the content package prompt using the Anáhuac MADTFIN template."""
    meta = sj.get("metadata", {})
    inputs = sj.get("academic_inputs", {})
    research = sj.get("research", {})
    di = sj.get("instructional_design", {})

    subject_name = meta.get("subject_name", "Unknown")
    subject_type = meta.get("subject_type", "CONCENTRACION")
    language = meta.get("language", "ES")
    competencies = inputs.get("competencies", [])
    learning_outcomes = inputs.get("learning_outcomes", [])
    papers = research.get("top20_papers", [])
    knowledge_matrix = research.get("knowledge_matrix", [])
    objectives = di.get("learning_objectives", [])
    content_map = di.get("content_map", {})
    weeks = content_map.get("weeks", []) if isinstance(content_map, dict) else []
    num_weeks = len(weeks) if weeks else 5

    try:
        from content_package_prompt import build_content_package_prompt
    except ImportError:
        from src.agents.content.content_package_prompt import build_content_package_prompt

    return build_content_package_prompt(
        subject_name=subject_name,
        subject_type=subject_type,
        language=language,
        num_weeks=num_weeks,
        objectives=objectives,
        weekly_map=weeks,
        competencies=competencies,
        learning_outcomes=learning_outcomes,
        papers=papers,
        knowledge_matrix=knowledge_matrix,
    )


@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint for Content Agent.
    
    Calls tools directly instead of using the agent loop to avoid MaxTokensReachedException.
    The tools generate all content deterministically from the subject data.
    """
    subject_id = payload.get("subject_id", "")

    if not subject_id:
        return {"result": "Content Agent ready. Send a subject_id to begin content generation."}

    sj = _load_subject_context(subject_id)
    if not sj:
        return {"result": f"Subject {subject_id} not found in S3."}

    meta = sj.get("metadata", {})
    inputs = sj.get("academic_inputs", {})
    research = sj.get("research", {})
    di = sj.get("instructional_design", {})

    subject_name = meta.get("subject_name", "Unknown")
    language = meta.get("language", "ES")
    competencies = inputs.get("competencies", [])
    learning_outcomes = inputs.get("learning_outcomes", [])
    papers = research.get("top20_papers", [])
    knowledge_matrix = research.get("knowledge_matrix", [])
    objectives = di.get("learning_objectives", [])
    content_map = di.get("content_map", {})
    weeks = content_map.get("weeks", []) if isinstance(content_map, dict) else []

    # Initialize tools (lazy init the agent just to define tools)
    _get_agent()

    # Call tools directly — no agent loop, no token accumulation
    import logging
    log = logging.getLogger(__name__)

    log.info(f"CONTENT_DIRECT: Generating content for {subject_name} ({subject_id})")

    # Try LLM-powered generation first, fall back to deterministic
    try:
        from llm_generator import generate_reading_llm, generate_quiz_llm, generate_masterclass_llm, generate_challenge_llm
    except ImportError:
        try:
            from src.agents.content.llm_generator import generate_reading_llm, generate_quiz_llm, generate_masterclass_llm, generate_challenge_llm
        except ImportError:
            generate_reading_llm = None
            generate_quiz_llm = None
            generate_masterclass_llm = None
            generate_challenge_llm = None

    use_llm = generate_reading_llm is not None

    # 1. Executive readings — LLM per week
    if use_llm:
        log.info("CONTENT_LLM: Generating readings with LLM")
        km = knowledge_matrix if isinstance(knowledge_matrix, list) else []
        km_by_topic = {}
        for km_entry in km:
            if isinstance(km_entry, dict):
                for topic in km_entry.get("syllabus_topics_covered", []):
                    km_by_topic.setdefault(topic.lower().strip(), []).append(km_entry)

        llm_readings = []
        for week in weeks:
            w = week.get("week", 1)
            theme = week.get("theme", "")
            bloom = week.get("bloom_level", "")
            subtopics = week.get("subtopics", [])

            # Find KM concepts for this week
            theme_lower = theme.lower().strip()
            relevant_km = km_by_topic.get(theme_lower, [])
            if not relevant_km:
                theme_words = {wd for wd in theme_lower.split() if len(wd) > 4}
                for tk, entries in km_by_topic.items():
                    if theme_words & {wd for wd in tk.split() if len(wd) > 4}:
                        relevant_km.extend(entries)

            concepts = []
            methodologies_list = []
            for kme in relevant_km:
                for c in kme.get("core_concepts", []):
                    if isinstance(c, dict):
                        concepts.append(c)
                for m in kme.get("key_methodologies", []):
                    if isinstance(m, str):
                        methodologies_list.append(m)

            theme_words_list = [wd.lower() for wd in theme.split() if len(wd) > 4]
            rel_papers = [p for p in papers if any(wd in p.get("title", "").lower() for wd in theme_words_list)][:3] or papers[:2]

            content_md = generate_reading_llm(w, len(weeks), theme, subject_name, bloom, subtopics, concepts, rel_papers, methodologies_list)
            llm_readings.append({"week": w, "title": f"Semana {w}: {theme}", "bloom_level": bloom, "content_md": content_md, "language": language})
            log.info(f"CONTENT_LLM: Reading week {w} done ({len(content_md)} chars)")

        readings_result = {"readings": llm_readings}
    else:
        readings_result = _call_generate_readings(weeks, subject_name, language, papers, knowledge_matrix)
    log.info(f"CONTENT: Readings: {len(readings_result.get('readings', []))}")

    # 2. Quiz — LLM generates 8 critical reasoning questions
    if use_llm:
        log.info("CONTENT_LLM: Generating quiz with LLM")
        ra_descs = [lo.get("description", "") for lo in learning_outcomes]
        obj_descs = [o.get("description", "") for o in objectives]
        ra_ids_list = [lo.get("ra_id", "") for lo in learning_outcomes]
        llm_questions = generate_quiz_llm(subject_name, ra_descs, obj_descs)
        if llm_questions and len(llm_questions) >= 6:
            quizzes_result = {"quizzes": [{
                "quiz_id": "QUIZ-RC-001",
                "title": f"Quiz de Razonamiento Critico: {subject_name}",
                "type": "critical_reasoning",
                "week": 3,
                "total_questions": len(llm_questions),
                "ra_ids": ra_ids_list,
                "questions": llm_questions,
            }]}
            log.info(f"CONTENT_LLM: Quiz done ({len(llm_questions)} questions)")
        else:
            log.warning("CONTENT_LLM: Quiz LLM failed, using deterministic fallback")
            quizzes_result = _call_generate_quizzes(learning_outcomes, subject_name, language, objectives)
    else:
        quizzes_result = _call_generate_quizzes(learning_outcomes, subject_name, language, objectives)
    log.info(f"CONTENT: Quizzes: {len(quizzes_result.get('quizzes', []))}")

    # 3. Maestria artifacts (deterministic — structure-heavy, not narrative)
    maestria_result = _call_generate_maestria(papers, subject_name, competencies, language, weeks, learning_outcomes)
    log.info(f"CONTENT: Maestria artifacts generated")

    # Assemble result
    content_package = {
        "executive_readings": readings_result,
        "quizzes": quizzes_result,
        "maestria_artifacts": maestria_result,
    }

    # 4. Masterclass script — LLM
    if use_llm:
        log.info("CONTENT_LLM: Generating masterclass with LLM")
        mid_week = weeks[len(weeks) // 2] if weeks else {}
        mc_theme = mid_week.get("theme", subject_name)
        obj_descs_short = [o.get("description", "")[:60] for o in objectives[:3]]
        comp_ids_list = [c.get("competency_id", "") for c in competencies]
        mc = generate_masterclass_llm(subject_name, mc_theme, obj_descs_short, papers[:5], comp_ids_list)
        if mc and mc.get("structure"):
            content_package["masterclass_script"] = mc
            log.info("CONTENT_LLM: Masterclass done")
        else:
            content_package["masterclass_script"] = _call_generate_masterclass(subject_name, weeks, objectives, papers, competencies)
    else:
        content_package["masterclass_script"] = _call_generate_masterclass(subject_name, weeks, objectives, papers, competencies)

    # 5. Agentic challenge — LLM
    if use_llm:
        log.info("CONTENT_LLM: Generating agentic challenge with LLM")
        ra_descs = [lo.get("description", "") for lo in learning_outcomes]
        comp_ids_list = [c.get("competency_id", "") for c in competencies]
        w2_theme = weeks[1].get("theme", subject_name) if len(weeks) > 1 else subject_name
        ch = generate_challenge_llm(subject_name, ra_descs, comp_ids_list, w2_theme)
        if ch and (ch.get("scenario") or ch.get("rubric")):
            content_package["agentic_challenge"] = ch
            log.info("CONTENT_LLM: Challenge done")
        else:
            content_package["agentic_challenge"] = _call_generate_agentic_challenge(subject_name, learning_outcomes, competencies, weeks)
    else:
        content_package["agentic_challenge"] = _call_generate_agentic_challenge(subject_name, learning_outcomes, competencies, weeks)

    # Persist directly to S3
    _direct_persist_content(subject_id, sj, content_package)
    log.info(f"CONTENT_DIRECT: Persisted to S3 for {subject_id}")

    return {"result": json.dumps(content_package, ensure_ascii=False)[:500]}


def _call_generate_readings(weeks, subject_name, language, papers, knowledge_matrix):
    """Call the readings generation logic directly."""
    def _ensure_dicts(items):
        result = []
        for item in (items or []):
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                try:
                    p = json.loads(item)
                    if isinstance(p, dict):
                        result.append(p)
                except (json.JSONDecodeError, TypeError):
                    pass
        return result

    weeks = _ensure_dicts(weeks)
    papers = _ensure_dicts(papers)
    km = _ensure_dicts(knowledge_matrix) if isinstance(knowledge_matrix, list) else []

    # Reuse the same logic from generate_executive_readings tool
    # (imported from the tool definition inside _get_agent)
    # We duplicate the core logic here to avoid tool decorator issues
    import re as _re

    km_by_topic = {}
    for km_entry in km:
        for topic in km_entry.get("syllabus_topics_covered", []):
            km_by_topic.setdefault(topic.lower().strip(), []).append(km_entry)

    readings = []
    total_weeks = len(weeks)

    for week in weeks:
        w = week.get("week", 1)
        theme = week.get("theme", "")
        bloom = week.get("bloom_level", "")
        subtopics = week.get("subtopics", [])
        activities = week.get("activities", [])

        # Find relevant KM
        theme_lower = theme.lower().strip()
        relevant_km = km_by_topic.get(theme_lower, [])
        if not relevant_km:
            theme_words = {wd for wd in theme_lower.split() if len(wd) > 4}
            for topic_key, entries in km_by_topic.items():
                if theme_words & {wd for wd in topic_key.split() if len(wd) > 4}:
                    relevant_km.extend(entries)

        concepts = []
        methodologies = []
        for km_entry in relevant_km:
            for c in km_entry.get("core_concepts", []):
                if isinstance(c, dict):
                    concepts.append(c)
            for m in km_entry.get("key_methodologies", []):
                if isinstance(m, str):
                    methodologies.append(m)

        # Find relevant papers
        theme_words = [wd.lower() for wd in theme.split() if len(wd) > 4]
        relevant_papers = [p for p in papers if any(wd in p.get("title", "").lower() for wd in theme_words)][:4] or papers[:3]

        bloom_action = {"RECORDAR": "identificar y reconocer", "COMPRENDER": "comprender y explicar",
                        "APLICAR": "aplicar en contextos reales", "ANALIZAR": "examinar criticamente",
                        "EVALUAR": "juzgar y fundamentar", "CREAR": "disenar soluciones"}.get(bloom, "desarrollar")

        sections = [
            f"# Lectura Ejecutiva, Semana {w} de {total_weeks}: {theme}",
            f"\n**Asignatura**: {subject_name}\n**Nivel cognitivo**: {bloom} (Bloom)\n**Semana**: {w} de {total_weeks}\n",
            "## Introduccion",
            f"Esta semana aborda {theme} dentro de {subject_name}. El nivel cognitivo es {bloom}, lo que implica {bloom_action} los conceptos presentados.\n",
        ]

        if concepts:
            sections.append("## Conceptos Clave")
            for i, c in enumerate(concepts[:5], 1):
                sections.append(f"\n### {i}. {c.get('concept', '')}")
                if c.get("definition"):
                    sections.append(f"\n{c['definition']}\n")
                if c.get("supporting_papers"):
                    for sp in c["supporting_papers"][:2]:
                        sections.append(f"- {sp}")
        elif subtopics:
            sections.append("## Contenido Tematico")
            for st in subtopics:
                sections.append(f"\n### {st}\nConcepto fundamental en {subject_name.lower()}.\n")

        if methodologies:
            sections.append("## Metodologias")
            for m in methodologies[:6]:
                sections.append(f"- {m}")

        if relevant_papers:
            sections.append("\n## Evidencia Academica")
            for p in relevant_papers[:3]:
                auth = p.get("authors", [""])[0] if isinstance(p.get("authors"), list) else str(p.get("authors", ""))
                sections.append(f"- **{p.get('title','')}** ({auth}, {p.get('year','')}). *{p.get('journal','')}*.")

        sections.append(f"\n## Aplicacion Profesional\nLos conceptos de {theme.lower()} se aplican en la toma de decisiones estrategicas.\n")
        sections.append(f"## Preguntas de Reflexion\n1. Como se relaciona {theme.lower()} con su experiencia?\n2. Que decisiones se beneficiarian de estos conceptos?\n")

        if relevant_papers:
            sections.append("## Referencias")
            for p in relevant_papers[:4]:
                auth = p.get("authors", [""])[0] if isinstance(p.get("authors"), list) else str(p.get("authors", ""))
                sections.append(f"- {auth} ({p.get('year','')}). *{p.get('title','')}*. {p.get('journal','')}.")

        readings.append({"week": w, "title": f"Semana {w}: {theme}", "bloom_level": bloom,
                         "content_md": "\n".join(sections), "language": language, "activities": activities})

    return {"readings": readings}


def _call_generate_quizzes(learning_outcomes, subject_name, language, objectives):
    """Generate 1 quiz per subject: 8 critical reasoning questions, 4 options each.
    At least 3 questions at Bloom Analyze/Evaluate level.
    Each question includes 2-3 line feedback for the correct answer.
    """
    def _ensure_dicts(items):
        result = []
        for item in (items or []):
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                try:
                    p = json.loads(item)
                    if isinstance(p, dict):
                        result.append(p)
                except (json.JSONDecodeError, TypeError):
                    pass
        return result

    learning_outcomes = _ensure_dicts(learning_outcomes)
    objectives = _ensure_dicts(objectives)

    # Build context from all RAs and objectives
    ra_descriptions = [lo.get("description", "") for lo in learning_outcomes]
    obj_descriptions = [o.get("description", "") for o in objectives]
    ra_ids = [lo.get("ra_id", "") for lo in learning_outcomes]

    # Generate 8 questions — at least 3 at Analyze/Evaluate level
    questions = [
        # Q1 — RECORDAR
        {
            "question_id": "Q1",
            "bloom_level": "RECORDAR",
            "question": f"En el contexto de {subject_name}, cual de los siguientes enunciados describe correctamente el alcance de esta asignatura?",
            "options": [
                f"Integra {ra_descriptions[0][:60] if ra_descriptions else subject_name} con enfoque en la toma de decisiones estrategicas",
                "Se limita a la memorizacion de formulas y procedimientos sin aplicacion practica",
                "Aborda exclusivamente aspectos teoricos sin vinculacion con el entorno organizacional",
                "Se enfoca en habilidades operativas basicas sin componente analitico"
            ],
            "correct_answer": 0,
            "feedback": f"Esta asignatura integra conocimientos de {subject_name} con un enfoque aplicado a la toma de decisiones en el contexto financiero mexicano. Los resultados de aprendizaje exigen que el estudiante vaya mas alla de la teoria para sustentar juicios profesionales fundamentados."
        },
        # Q2 — COMPRENDER
        {
            "question_id": "Q2",
            "bloom_level": "COMPRENDER",
            "question": f"Cual es la relacion entre los resultados de aprendizaje de {subject_name} y las competencias del programa MADTFIN?",
            "options": [
                "Los RAs operacionalizan las competencias del programa al definir desempenos observables y medibles en contextos financieros reales",
                "Los RAs son independientes de las competencias y se evaluan por separado",
                "Las competencias del programa no se relacionan con asignaturas individuales",
                "Los RAs solo aplican a evaluaciones teoricas, no a competencias profesionales"
            ],
            "correct_answer": 0,
            "feedback": f"Los resultados de aprendizaje de {subject_name} son la operacionalizacion de las competencias del programa. Cada RA define un desempeno observable que contribuye al desarrollo de una o mas competencias, asegurando la trazabilidad entre la formacion y el perfil de egreso."
        },
        # Q3 — APLICAR
        {
            "question_id": "Q3",
            "bloom_level": "APLICAR",
            "question": f"Un directivo financiero necesita aplicar los conceptos de {subject_name} para fundamentar una decision ante el consejo de administracion. Cual seria el enfoque mas apropiado?",
            "options": [
                "Integrar evidencia academica Q1/Q2 con datos del contexto regulatorio mexicano (CNBV, Banxico) para construir un argumento fundamentado",
                "Presentar solo datos historicos de la empresa sin referencia a investigacion academica",
                "Basarse exclusivamente en la intuicion y experiencia personal del directivo",
                "Copiar las recomendaciones de un informe de consultoria sin adaptacion al contexto"
            ],
            "correct_answer": 0,
            "feedback": f"La aplicacion profesional de {subject_name} requiere integrar multiples fuentes de evidencia. La investigacion academica Q1/Q2 proporciona el sustento teorico, mientras que el contexto regulatorio mexicano (CNBV, Banxico, NIF) asegura la pertinencia y viabilidad de las recomendaciones."
        },
        # Q4 — ANALIZAR (Bloom alto)
        {
            "question_id": "Q4",
            "bloom_level": "ANALIZAR",
            "question": f"Al analizar un caso de {subject_name} en el sector financiero mexicano, que elementos debe descomponer el estudiante para identificar las relaciones causa-efecto?",
            "options": [
                "Variables financieras clave, marco regulatorio aplicable, evidencia academica y contexto macroeconomico de Mexico",
                "Unicamente los estados financieros de la empresa sin considerar factores externos",
                "Solo las opiniones de los directivos involucrados en la decision",
                "Los resultados financieros del ultimo trimestre sin analisis de tendencias"
            ],
            "correct_answer": 0,
            "feedback": f"El analisis en {subject_name} requiere descomponer el problema en sus componentes fundamentales: las variables financieras internas, el entorno regulatorio (CNBV, Banxico), la evidencia academica que sustenta las relaciones causales, y el contexto macroeconomico mexicano. Solo integrando estos elementos se pueden identificar patrones e impactos relevantes."
        },
        # Q5 — ANALIZAR (Bloom alto)
        {
            "question_id": "Q5",
            "bloom_level": "ANALIZAR",
            "question": f"Dos investigaciones Q1 sobre {subject_name} llegan a conclusiones aparentemente contradictorias. Como deberia proceder el estudiante?",
            "options": [
                "Examinar las diferencias metodologicas, contextos de estudio y supuestos de cada investigacion para determinar la aplicabilidad al caso mexicano",
                "Descartar ambas investigaciones por ser contradictorias",
                "Elegir la investigacion mas reciente sin analizar las diferencias",
                "Ignorar la evidencia academica y basarse en la practica comun del sector"
            ],
            "correct_answer": 0,
            "feedback": f"El pensamiento critico en {subject_name} exige analizar las diferencias metodologicas entre estudios. Las conclusiones contradictorias frecuentemente se explican por diferencias en el contexto (mercados desarrollados vs. emergentes), la muestra, el periodo de estudio o los supuestos. El estudiante debe evaluar cual es mas aplicable al contexto financiero mexicano."
        },
        # Q6 — EVALUAR (Bloom alto)
        {
            "question_id": "Q6",
            "bloom_level": "EVALUAR",
            "question": f"Un colega propone una estrategia financiera basada en un unico paper academico sin considerar el marco regulatorio de la CNBV. Como evaluaria esta propuesta?",
            "options": [
                "La propuesta es insuficiente porque carece de triangulacion de evidencia y omite restricciones regulatorias que podrian invalidar la estrategia en Mexico",
                "La propuesta es adecuada porque un paper Q1 es suficiente para fundamentar cualquier decision",
                "La propuesta es correcta porque la regulacion mexicana no afecta las decisiones financieras estrategicas",
                "La propuesta es valida si el paper fue publicado en los ultimos 2 anos"
            ],
            "correct_answer": 0,
            "feedback": f"Evaluar propuestas en {subject_name} requiere verificar la solidez de la fundamentacion. Un unico paper, por mas riguroso que sea, no constituye evidencia suficiente para una decision estrategica. Ademas, omitir el marco regulatorio mexicano (CNBV, Banxico, LFPDPPP) puede resultar en estrategias inviables o que expongan a la organizacion a riesgos legales."
        },
        # Q7 — EVALUAR (Bloom alto)
        {
            "question_id": "Q7",
            "bloom_level": "EVALUAR",
            "question": f"Al evaluar la calidad de la evidencia utilizada en un analisis de {subject_name}, que criterios son mas relevantes?",
            "options": [
                "Validez metodologica del estudio, pertinencia al contexto mexicano, nivel de la revista (Q1/Q2) y replicabilidad de los hallazgos",
                "Unicamente el numero de citas del articulo",
                "La reputacion del autor sin considerar la metodologia",
                "La extension del articulo y la cantidad de graficas incluidas"
            ],
            "correct_answer": 0,
            "feedback": f"La evaluacion de evidencia en {subject_name} debe considerar multiples criterios de calidad. La validez metodologica asegura que los hallazgos son confiables, la pertinencia al contexto mexicano garantiza aplicabilidad, el nivel de la revista (Q1/Q2) indica rigor en la revision por pares, y la replicabilidad permite verificar los resultados."
        },
        # Q8 — APLICAR
        {
            "question_id": "Q8",
            "bloom_level": "APLICAR",
            "question": f"En el reto de aprendizaje agentico de {subject_name}, el estudiante debe entregar un documento ejecutivo. Cual de los siguientes elementos es indispensable?",
            "options": [
                "Diagnostico fundamentado en evidencia academica, analisis del contexto regulatorio mexicano y recomendacion estrategica accionable",
                "Un resumen extenso de todos los papers leidos durante el curso",
                "Una lista de definiciones teoricas sin aplicacion al caso",
                "Un documento con formato libre sin estructura argumentativa"
            ],
            "correct_answer": 0,
            "feedback": f"El reto agentico de {subject_name} evalua la capacidad del estudiante para integrar conocimiento en una decision profesional. El documento debe demostrar fundamentacion en evidencia (papers Q1/Q2), comprension del contexto regulatorio mexicano (CNBV, Banxico, NIF) y claridad directiva en la recomendacion estrategica."
        },
    ]

    # Single quiz per subject
    quiz = {
        "quiz_id": "QUIZ-RC-001",
        "title": f"Quiz de Razonamiento Critico: {subject_name}",
        "type": "critical_reasoning",
        "week": 3,
        "total_questions": 8,
        "bloom_distribution": {
            "RECORDAR": 1,
            "COMPRENDER": 1,
            "APLICAR": 2,
            "ANALIZAR": 2,
            "EVALUAR": 2,
        },
        "ra_ids": ra_ids,
        "questions": questions,
    }

    return {"quizzes": [quiz]}


def _call_generate_maestria(papers, subject_name, competencies, language, weeks, learning_outcomes):
    """Call maestria artifacts generation directly."""
    def _ensure_dicts(items):
        result = []
        for item in (items or []):
            if isinstance(item, dict):
                result.append(item)
            elif isinstance(item, str):
                try:
                    p = json.loads(item)
                    if isinstance(p, dict):
                        result.append(p)
                except (json.JSONDecodeError, TypeError):
                    pass
        return result

    papers = _ensure_dicts(papers)
    competencies = _ensure_dicts(competencies)
    weeks = _ensure_dicts(weeks)
    learning_outcomes = _ensure_dicts(learning_outcomes)

    # Dashboard
    rows = ["| # | Titulo | Ano | Revista | Hallazgo |", "|---|--------|-----|---------|----------|"]
    for i, p in enumerate(papers[:20], 1):
        rows.append(f"| {i} | {p.get('title','')[:55]} | {p.get('year','')} | {p.get('journal','')[:30]} | {p.get('key_finding','')[:40]} |")

    # Critical path
    cp_rows = ["| Semana | Actividad | Entregable | Criterio |", "|---|---|---|---|"]
    for w in weeks:
        cp_rows.append(f"| {w.get('week','')} | Estudio: {w.get('theme','')[:35]} | Analisis aplicado | Nivel {w.get('bloom_level','')} |")

    # Cases
    comp_ids = [c.get("competency_id", "") for c in competencies]
    ra_ids = [lo.get("ra_id", "") for lo in learning_outcomes]
    cases = [{"case_id": "CASE-001", "title": f"Caso: {subject_name}",
              "context": f"Organizacion financiera requiere {subject_name.lower()} para decisiones estrategicas.",
              "questions": [f"Como aplicaria {subject_name.lower()}?", "Que metricas usaria?", "Que riesgos identifica?"],
              "rubric": {"criteria": ["Analisis (25%)", "Metodologia (30%)", "Propuesta (25%)", "Comunicacion (20%)"], "competency_ids": comp_ids, "ra_ids": ra_ids}}]

    # Facilitator guide
    sessions = [{"week": w.get("week", 1), "duration_minutes": 90,
                 "objective": f"Semana {w.get('week','')}: {w.get('theme','')}",
                 "sequence": [{"time": "0-10min", "activity": "Apertura"}, {"time": "10-35min", "activity": f"Exposicion: {w.get('theme','')[:30]}"},
                              {"time": "35-65min", "activity": f"Caso practico"}, {"time": "65-80min", "activity": "Discusion"}, {"time": "80-90min", "activity": "Cierre"}],
                 "trigger_questions": [f"Como se relaciona {w.get('theme','').lower()[:30]} con su experiencia?"]} for w in weeks]

    return {
        "subject_name": subject_name, "language": language,
        "evidence_dashboard": {"html_content": "\n".join(rows), "papers_indexed": len(papers)},
        "critical_path_map": {"markdown_content": "\n".join(cp_rows)},
        "executive_cases_repository": {"cases": cases},
        "facilitator_guide": {"sessions": sessions},
    }


def _call_generate_masterclass(subject_name, weeks, objectives, papers, competencies):
    """Generate masterclass script (18-22 min) for the subject."""
    # Pick the most important theme (middle week — application level)
    mid_week = weeks[len(weeks) // 2] if weeks else {}
    theme = mid_week.get("theme", subject_name)
    bloom = mid_week.get("bloom_level", "APLICAR")

    # Pick top 3 papers for the case
    top_papers = [p for p in (papers or []) if isinstance(p, dict)][:3]
    paper_refs = "; ".join(f"{p.get('title','')[:40]} ({p.get('year','')})" for p in top_papers)

    obj_text = "; ".join(o.get("description", "")[:60] for o in (objectives or [])[:3] if isinstance(o, dict))
    comp_ids = ", ".join(c.get("competency_id", "") for c in (competencies or []) if isinstance(c, dict))

    script = {
        "title": f"Masterclass: {subject_name}",
        "duration_minutes": 20,
        "theme": theme,
        "structure": [
            {
                "section": "Gancho directivo",
                "time": "0:00 - 2:00",
                "duration_minutes": 2,
                "content": f"[SLIDE: Titulo] Bienvenidos a esta masterclass sobre {subject_name}. "
                           f"Hoy abordaremos {theme}, un tema critico para la toma de decisiones en el sector financiero mexicano. "
                           f"[DATO EN PANTALLA] Segun investigaciones recientes ({paper_refs[:80]}), "
                           f"este tema impacta directamente en la creacion de valor corporativo.",
                "notes": "Iniciar con una pregunta provocadora o dato impactante del sector financiero mexicano."
            },
            {
                "section": "Desarrollo conceptual con caso",
                "time": "2:00 - 16:00",
                "duration_minutes": 14,
                "content": f"[SLIDE: Marco conceptual] Los objetivos de esta sesion son: {obj_text}. "
                           f"[CASO VISUAL] Consideremos el caso de una institucion financiera mexicana regulada por la CNBV "
                           f"que enfrenta el reto de {theme.lower()}. "
                           f"[SLIDE: Evidencia] La investigacion academica Q1/Q2 nos muestra que {paper_refs}. "
                           f"[DATO EN PANTALLA] Competencias desarrolladas: {comp_ids}.",
                "notes": "Alternar entre teoria y caso practico. Usar datos reales del mercado mexicano."
            },
            {
                "section": "Sintesis y decision",
                "time": "16:00 - 20:00",
                "duration_minutes": 4,
                "content": f"[SLIDE: Sintesis] Los tres conceptos clave de hoy son: "
                           f"1) El marco teorico de {theme}, "
                           f"2) Su aplicacion en el contexto regulatorio mexicano (CNBV, Banxico), "
                           f"3) La evidencia academica que sustenta las decisiones. "
                           f"[SLIDE: Decision] Si usted fuera el director financiero, que decision tomaria?",
                "notes": "Cerrar con una pregunta que conecte con el reto de aprendizaje agentico."
            },
            {
                "section": "Llamada a la accion",
                "time": "20:00 - 22:00",
                "duration_minutes": 2,
                "content": f"[SLIDE: Siguiente paso] Para la proxima semana, complete el reto de aprendizaje agentico "
                           f"donde aplicara estos conceptos a un escenario real. "
                           f"Consulte las lecturas ejecutivas y los papers del dashboard de evidencia.",
                "notes": "Vincular con el reto agentico y las lecturas de la semana."
            }
        ],
        "total_slides": 8,
        "competencies_covered": comp_ids,
    }
    return script


def _call_generate_agentic_challenge(subject_name, learning_outcomes, competencies, weeks):
    """Generate agentic learning challenge (week 2) with Mexican financial sector scenario."""
    los = [lo for lo in (learning_outcomes or []) if isinstance(lo, dict)]
    ra_text = "; ".join(f"{lo.get('ra_id','')}: {lo.get('description','')[:60]}" for lo in los)
    comp_ids = [c.get("competency_id", "") for c in (competencies or []) if isinstance(c, dict)]
    week2_theme = weeks[1].get("theme", subject_name) if len(weeks) > 1 else subject_name

    challenge = {
        "title": f"Reto de Aprendizaje Agentico: {subject_name}",
        "week": 2,
        "scenario": (
            f"Usted es el director de planeacion financiera de una empresa mediana del sector financiero mexicano "
            f"que cotiza en la Bolsa Mexicana de Valores (BMV). La Comision Nacional Bancaria y de Valores (CNBV) "
            f"ha emitido nuevas disposiciones regulatorias que impactan directamente en {week2_theme.lower()}. "
            f"El consejo de administracion le solicita un analisis fundamentado que integre {subject_name.lower()} "
            f"para sustentar la estrategia financiera del proximo ejercicio fiscal. "
            f"Debe considerar el entorno macroeconomico actual de Mexico, las Normas de Informacion Financiera (NIF) "
            f"aplicables, y las mejores practicas internacionales documentadas en la literatura academica Q1/Q2."
        ),
        "central_question": (
            f"Con base en la evidencia academica y el marco regulatorio mexicano, "
            f"que estrategia financiera recomendaria al consejo de administracion "
            f"para optimizar {week2_theme.lower()} en el contexto actual?"
        ),
        "deliverable": (
            "Documento ejecutivo de 1-2 paginas que incluya: "
            "1) Diagnostico de la situacion con datos del contexto mexicano, "
            "2) Analisis fundamentado en al menos 3 papers del corpus academico, "
            "3) Recomendacion estrategica con justificacion, "
            "4) Consideraciones regulatorias (CNBV, Banxico, NIF segun aplique)."
        ),
        "learning_outcomes_assessed": ra_text,
        "rubric": {
            "criteria": [
                {
                    "criterion": "Fundamentacion en evidencia",
                    "weight": "25%",
                    "excelente": "Integra 3+ papers Q1/Q2 con analisis critico de hallazgos",
                    "bueno": "Referencia 2 papers con vinculacion al caso",
                    "regular": "Menciona papers sin analisis de relevancia",
                    "deficiente": "Sin referencias academicas o referencias no pertinentes"
                },
                {
                    "criterion": "Coherencia argumentativa",
                    "weight": "25%",
                    "excelente": "Argumento logico con premisas, evidencia y conclusion alineadas",
                    "bueno": "Estructura argumentativa clara con minor gaps",
                    "regular": "Ideas desconectadas o saltos logicos",
                    "deficiente": "Sin estructura argumentativa identificable"
                },
                {
                    "criterion": "Pertinencia del contexto regulatorio mexicano",
                    "weight": "25%",
                    "excelente": "Integra CNBV, Banxico, NIF con precision y relevancia al caso",
                    "bueno": "Menciona marco regulatorio con aplicacion parcial",
                    "regular": "Referencias regulatorias genericas sin especificidad",
                    "deficiente": "Ignora el contexto regulatorio mexicano"
                },
                {
                    "criterion": "Claridad directiva",
                    "weight": "25%",
                    "excelente": "Recomendacion ejecutiva clara, accionable y con metricas de seguimiento",
                    "bueno": "Recomendacion clara con implementacion parcialmente definida",
                    "regular": "Recomendacion vaga o sin plan de accion",
                    "deficiente": "Sin recomendacion o recomendacion incoherente"
                }
            ],
            "competency_ids": comp_ids,
        }
    }
    return challenge


def _direct_persist_content(subject_id: str, sj: dict, content_package: dict) -> None:
    """Persist content directly to S3 without agent loop."""
    from datetime import datetime, timezone

    bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
    table_name = os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")
    s3 = boto3.client("s3")
    ddb = boto3.resource("dynamodb")

    sj["content_package"] = content_package
    now = datetime.now(timezone.utc).isoformat()

    current = sj["pipeline_state"]["current_state"]
    advanced_states = {"PENDING_APPROVAL", "APPROVED", "REJECTED", "PUBLISHED"}
    if current not in advanced_states:
        sj["pipeline_state"]["current_state"] = "CONTENT_READY"
        sj["pipeline_state"]["state_history"].append({"state": "CONTENT_READY", "agent": "content-agent-direct", "timestamp": now, "llm_version": "deterministic", "result_hash": ""})
        ddb.Table(table_name).put_item(Item={"subject_id": subject_id, "SK": "STATE", "current_state": "CONTENT_READY",
                                              "subject_name": sj["metadata"]["subject_name"], "program_name": sj["metadata"]["program_name"],
                                              "updated_at": now, "s3_key": f"subjects/{subject_id}/subject.json"})
    sj["updated_at"] = now
    s3.put_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json",
                  Body=json.dumps(sj, ensure_ascii=False, indent=2).encode("utf-8"), ContentType="application/json")


def _self_persist_content(subject_id: str, result_text: str) -> None:

    from datetime import datetime, timezone

    bucket = os.environ.get("SUBJECTS_BUCKET_NAME", "academic-pipeline-subjects-254508868459-us-east-1-dev")
    table_name = os.environ.get("SUBJECTS_TABLE_NAME", "academic-pipeline-subjects-dev")
    s3 = boto3.client("s3")
    ddb = boto3.resource("dynamodb")

    obj = s3.get_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json")
    sj = json.loads(obj["Body"].read().decode("utf-8"))

    parsed = _extract_content_json(result_text)

    if not parsed:
        import logging
        logging.getLogger().warning(f"CONTENT_PERSIST: no parseable JSON found for {subject_id}")
        return

    now = datetime.now(timezone.utc).isoformat()
    sj.setdefault("content_package", {})
    if parsed.get("executive_readings"):
        sj["content_package"]["executive_readings"] = parsed["executive_readings"]
    if parsed.get("quizzes"):
        sj["content_package"]["quizzes"] = parsed["quizzes"]
    if parsed.get("maestria_artifacts"):
        sj["content_package"]["maestria_artifacts"] = parsed["maestria_artifacts"]
    if parsed.get("lab_cases"):
        sj["content_package"]["lab_cases"] = parsed["lab_cases"]
    if parsed.get("masterclass_script"):
        sj["content_package"]["masterclass_script"] = parsed["masterclass_script"]
    if parsed.get("agentic_challenge"):
        sj["content_package"]["agentic_challenge"] = parsed["agentic_challenge"]

    # Only advance state if not already past CONTENT_READY
    current = sj["pipeline_state"]["current_state"]
    advanced_states = {"PENDING_APPROVAL", "APPROVED", "REJECTED", "PUBLISHED"}
    if current not in advanced_states:
        sj["pipeline_state"]["current_state"] = "CONTENT_READY"
        sj["pipeline_state"]["state_history"].append({"state": "CONTENT_READY", "agent": "content-agent", "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": ""})
        ddb.Table(table_name).put_item(Item={"subject_id": subject_id, "SK": "STATE", "current_state": "CONTENT_READY", "subject_name": sj["metadata"]["subject_name"], "program_name": sj["metadata"]["program_name"], "updated_at": now, "s3_key": f"subjects/{subject_id}/subject.json"})
    sj["updated_at"] = now

    s3.put_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json", Body=json.dumps(sj, ensure_ascii=False, indent=2).encode("utf-8"), ContentType="application/json")


def _extract_content_json(text: str) -> dict:
    """Extract content JSON from agent response — handles multiple formats."""
    if not text:
        return {}

    # Strategy 1: Try ```json blocks (largest one with expected keys)
    matches = re.findall(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    best = {}
    for m in matches:
        try:
            p = json.loads(m.strip())
            if isinstance(p, dict) and len(p) > len(best):
                if any(k in p for k in ("executive_readings", "quizzes", "maestria_artifacts")):
                    best = p
        except json.JSONDecodeError:
            continue
    if best:
        return best

    # Strategy 2: Find the largest JSON object containing expected keys
    # Search for {"executive_readings" or {"quizzes" patterns
    for key in ("executive_readings", "quizzes", "maestria_artifacts"):
        pattern = f'"{key}"'
        idx = text.rfind(pattern)  # Last occurrence
        if idx < 0:
            continue
        # Walk backwards to find the opening brace
        brace_start = text.rfind('{', 0, idx)
        if brace_start < 0:
            continue
        # Walk forward to find matching closing brace
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        candidate = json.loads(text[brace_start:i+1])
                        if isinstance(candidate, dict) and any(k in candidate for k in ("executive_readings", "quizzes", "maestria_artifacts")):
                            return candidate
                    except json.JSONDecodeError:
                        pass
                    break

    # Strategy 3: Direct parse
    try:
        p = json.loads(text)
        if isinstance(p, dict):
            return p
    except (json.JSONDecodeError, TypeError):
        pass

    return {}


if __name__ == "__main__":
    app.run()
