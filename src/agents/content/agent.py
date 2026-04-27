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
        max_tokens=16384,
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
    """Build a compact prompt with essential academic context for the Content agent."""
    meta = sj.get("metadata", {})
    inputs = sj.get("academic_inputs", {})
    research = sj.get("research", {})
    di = sj.get("instructional_design", {})

    subject_name = meta.get("subject_name", "Unknown")
    subject_type = meta.get("subject_type", "CONCENTRACION")
    program_type = meta.get("program_type", "MAESTRIA")
    language = meta.get("language", "ES")
    competencies = inputs.get("competencies", [])
    learning_outcomes = inputs.get("learning_outcomes", [])
    papers = research.get("top20_papers", [])
    objectives = di.get("learning_objectives", [])
    content_map = di.get("content_map", {})

    # Compact competencies
    comp_text = ", ".join(f"{c['competency_id']}" for c in competencies)

    # Compact learning outcomes
    lo_text = "\n".join(f"  {lo['ra_id']}: {lo['description'][:80]}" for lo in learning_outcomes)

    # Compact objectives
    obj_text = "\n".join(
        f"  {o.get('objective_id','')}: [{o.get('bloom_level','')}] {o.get('description','')[:80]}"
        for o in objectives
    )

    # Content map weeks — compact
    weeks = content_map.get("weeks", [])
    weeks_json = json.dumps([
        {"week": w.get("week"), "theme": w.get("theme","")[:50], "bloom_level": w.get("bloom_level",""),
         "subtopics": w.get("subtopics", [])[:3], "activities": w.get("activities", [])[:2]}
        for w in weeks
    ], ensure_ascii=False)

    # Papers — compact
    papers_compact = json.dumps([
        {"title": p.get("title","")[:60], "year": p.get("year",""), "journal": p.get("journal","")[:30],
         "key_finding": p.get("key_finding","")[:50], "syllabus_topic": p.get("syllabus_topic","")[:40]}
        for p in papers[:20]
    ], ensure_ascii=False)

    # Knowledge Matrix — pass to generate_executive_readings for substantive content
    knowledge_matrix = research.get("knowledge_matrix", [])
    km_compact = json.dumps(knowledge_matrix[:3], ensure_ascii=False)[:3000] if knowledge_matrix else "[]"

    num_weeks = len(weeks) if weeks else 5

    return f"""Generate content for subject "{subject_name}" (ID: {subject_id}).
Type: {subject_type} | Program: {program_type} | Language: {language} | Weeks: {num_weeks}

Competencies: {comp_text}

Learning Outcomes:
{lo_text}

Objectives:
{obj_text}

Weekly Map:
{weeks_json}

Papers:
{papers_compact}

Knowledge Matrix (IMPORTANT — pass this to generate_executive_readings):
{km_compact}

CALL THESE 3 TOOLS:
1. generate_executive_readings(weekly_map=<weekly_map>, subject_name="{subject_name}", language="{language}", papers=<papers>, knowledge_matrix=<knowledge_matrix>)
2. generate_quizzes(learning_outcomes=<learning_outcomes as list>, subject_name="{subject_name}", language="{language}", objectives=<objectives as list>)
3. generate_maestria_artifacts(papers=<papers>, subject_name="{subject_name}", competencies=<competencies as list>, language="{language}", weekly_map=<weekly_map>, learning_outcomes=<learning_outcomes>)

Return JSON with keys: executive_readings, quizzes, maestria_artifacts.
"""


@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint for Content Agent."""
    prompt = payload.get("prompt", "")
    subject_id = payload.get("subject_id", "")

    if not prompt and not subject_id:
        return {"result": "Content Agent ready. Send a prompt or subject_id to begin content generation."}

    agent = _get_agent()

    if subject_id:
        sj = _load_subject_context(subject_id)
        if sj:
            prompt = _build_content_prompt(subject_id, sj)
        else:
            prompt = json.dumps({
                "task": "Generate educational content for this subject",
                "subject_id": subject_id,
                "instructions": "Use all available tools to generate the complete content package",
            })

    result = agent(prompt)
    result_str = str(result)

    if subject_id:
        try:
            _self_persist_content(subject_id, result_str)
        except Exception:
            pass

    return {"result": result_str}


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
