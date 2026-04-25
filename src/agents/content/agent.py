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
        max_tokens=8192,
    )

    @tool
    def generate_executive_readings(weekly_map: list, subject_name: str, language: str, papers: list = None) -> dict:
        """Generate executive readings for each week of the course map.

        Args:
            weekly_map: List of week dicts with week, theme, bloom_level, activities, subtopics
            subject_name: Name of the subject
            language: Content language: ES, EN, or BILINGUAL
            papers: Optional list of research papers to reference in readings
        """
        readings = []
        papers = papers or []
        for week in weekly_map:
            w = week.get("week", 1)
            theme = week.get("theme", "")
            bloom = week.get("bloom_level", "")
            subtopics = week.get("subtopics", [])
            activities = week.get("activities", [])

            # Build subtopics section
            subtopics_md = "\n".join(f"- {st}" for st in subtopics) if subtopics else f"- Tema principal: {theme}"

            # Find relevant papers for this week's theme
            theme_lower = theme.lower()
            relevant_papers = [
                p for p in papers
                if any(word in p.get("title", "").lower() for word in theme_lower.split() if len(word) > 4)
            ][:3]
            papers_md = ""
            if relevant_papers:
                papers_md = "\n## Referencias Académicas\n\n" + "\n".join(
                    f"- {p.get('title','')} ({p.get('year','')}, {p.get('journal','')[:40]})"
                    for p in relevant_papers
                )

            # Build activities section
            activities_md = ""
            if activities:
                activities_md = "\n## Actividades de Aprendizaje\n\n" + "\n".join(f"- {a}" for a in activities)

            content = (
                f"# Lectura Ejecutiva — Semana {w}: {theme}\n\n"
                f"**Nivel Bloom**: {bloom}\n"
                f"**Asignatura**: {subject_name}\n\n"
                f"## Contenido Temático\n\n{subtopics_md}\n"
                f"{activities_md}\n"
                f"{papers_md}\n\n"
                f"## Aplicación Profesional\n\n"
                f"Caso de aplicación de {theme} en el contexto de {subject_name}.\n"
            )
            if language == "BILINGUAL":
                content += f"\n---\n# Executive Reading — Week {w}: {theme}\n\n[English version]"

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
        objectives = objectives or []
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
            "You are Content, a content generation agent for university programs. "
            "You receive the COMPLETE academic context: syllabus, competencies, learning outcomes, objectives, content map, and research papers. "
            "CRITICAL RULES: "
            "1. ALL content MUST be specific to the actual subject — NEVER generate generic 'Research Methods' or placeholder content. "
            "2. Use the EXACT learning outcome IDs from the input (RA1, RA2) — NEVER generate generic IDs. "
            "3. The subject_name in all outputs MUST match the input subject name EXACTLY. "
            "4. Readings MUST match the content map weeks (NOT 8 generic weeks). "
            "5. Quiz questions MUST be substantive and specific to the subject domain. "
            "6. The Evidence Dashboard MUST use the actual Scopus papers provided. "
            "7. Pass the papers list to generate_maestria_artifacts and generate_executive_readings. "
            "8. Pass the weekly_map from the content map to generate_executive_readings and generate_maestria_artifacts. "
            "Use generate_executive_readings, generate_quizzes, and generate_maestria_artifacts (if Maestría). "
            "CRITICAL: Your final response MUST be ONLY a single JSON code block with NO text before or after. "
            "Format: ```json\n{...}\n``` "
            "The JSON MUST have keys: executive_readings, quizzes, maestria_artifacts, lab_cases. "
            "Do NOT include markdown tables, explanations, summaries, or commentary outside the JSON block."
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
    """Build a rich prompt with all academic context for the Content agent."""
    meta = sj.get("metadata", {})
    inputs = sj.get("academic_inputs", {})
    research = sj.get("research", {})
    di = sj.get("instructional_design", {})

    subject_name = meta.get("subject_name", "Unknown")
    subject_type = meta.get("subject_type", "CONCENTRACION")
    program_name = meta.get("program_name", "")
    program_type = meta.get("program_type", "MAESTRIA")
    language = meta.get("language", "ES")
    competencies = inputs.get("competencies", [])
    learning_outcomes = inputs.get("learning_outcomes", [])
    syllabus = inputs.get("syllabus", "")
    papers = research.get("top20_papers", [])
    objectives = di.get("learning_objectives", [])
    content_map = di.get("content_map", {})
    descriptive_card = di.get("descriptive_card", {})

    # Format competencies
    comp_text = "\n".join(f"  - {c['competency_id']}: {c['description']}" for c in competencies)

    # Format learning outcomes
    lo_text = "\n".join(f"  - {lo['ra_id']}: {lo['description']}" for lo in learning_outcomes)

    # Format objectives from DI
    obj_text = "\n".join(
        f"  - {o.get('objective_id','')}: [{o.get('bloom_level','')}] {o.get('description','')}"
        for o in objectives
    )

    # Format content map weeks
    weeks = content_map.get("weeks", [])
    weeks_text = "\n".join(
        f"  Sem {w.get('week','')}: {w.get('theme','')} [{w.get('bloom_level','')}]"
        for w in weeks
    )

    # Format top papers
    papers_text = "\n".join(
        f"  {i}. {p.get('title','')} ({p.get('year','')}, {p.get('journal','')[:40]}) — {p.get('key_finding','')}"
        for i, p in enumerate(papers[:20], 1)
    )

    # Determine number of weeks from content map or syllabus
    num_weeks = len(weeks) if weeks else 5

    return f"""Generate the complete content package for the following subject. Use generate_executive_readings, generate_quizzes, and generate_maestria_artifacts tools.

SUBJECT: {subject_name}
SUBJECT_ID: {subject_id}
SUBJECT_TYPE: {subject_type}
PROGRAM: {program_name}
PROGRAM_TYPE: {program_type}
LANGUAGE: {language}
TOTAL_WEEKS: {num_weeks}

SYLLABUS:
{syllabus}

PROGRAM COMPETENCIES:
{comp_text}

LEARNING OUTCOMES (use these for quizzes — EXACT IDs):
{lo_text}

LEARNING OBJECTIVES (from DI agent — use for readings alignment):
{obj_text}

CONTENT MAP (from DI agent — use for weekly readings):
{weeks_text}

TOP 20 RESEARCH PAPERS (use for Evidence Dashboard and readings):
{papers_text}

CRITICAL INSTRUCTIONS:
1. Executive readings MUST match the content map weeks above ({num_weeks} weeks), NOT 8 generic weeks
2. Each reading MUST be about the ACTUAL topic from the syllabus, NOT generic "Research Methods"
3. Quizzes MUST use the EXACT learning outcome IDs: {', '.join(lo['ra_id'] for lo in learning_outcomes)}
4. Quiz questions MUST be specific to "{subject_name}" content, NOT template placeholders
5. The Evidence Dashboard MUST use the actual 20 Scopus papers listed above
6. The subject_name in all outputs must be "{subject_name}" (NOT a generic name)
7. Language is {language} — generate content in Spanish
8. This is a {program_type} program — generate ALL 4 Maestría artifacts
9. Executive cases must relate to {subject_name} in a financial/business context
10. The Facilitator Guide sessions must match the {num_weeks} weeks of the content map
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

    parsed = {}
    matches = re.findall(r'```(?:json)?\s*\n(.*?)\n```', result_text, re.DOTALL)
    for m in matches:
        try:
            p = json.loads(m.strip())
            if isinstance(p, dict) and len(p) > len(parsed):
                parsed = p
        except json.JSONDecodeError:
            continue

    sj.setdefault("content_package", {})
    if parsed.get("executive_readings"):
        sj["content_package"]["executive_readings"] = parsed["executive_readings"]
    if parsed.get("quizzes"):
        sj["content_package"]["quizzes"] = parsed["quizzes"]
    if parsed.get("maestria_artifacts"):
        sj["content_package"]["maestria_artifacts"] = parsed["maestria_artifacts"]
    if parsed.get("lab_cases"):
        sj["content_package"]["lab_cases"] = parsed["lab_cases"]

    now = datetime.now(timezone.utc).isoformat()
    sj["pipeline_state"]["current_state"] = "CONTENT_READY"
    sj["pipeline_state"]["state_history"].append({"state": "CONTENT_READY", "agent": "content-agent", "timestamp": now, "llm_version": "claude-sonnet-4.6", "result_hash": ""})
    sj["updated_at"] = now

    s3.put_object(Bucket=bucket, Key=f"subjects/{subject_id}/subject.json", Body=json.dumps(sj, ensure_ascii=False, indent=2).encode("utf-8"), ContentType="application/json")
    ddb.Table(table_name).put_item(Item={"subject_id": subject_id, "SK": "STATE", "current_state": "CONTENT_READY", "subject_name": sj["metadata"]["subject_name"], "program_name": sj["metadata"]["program_name"], "updated_at": now, "s3_key": f"subjects/{subject_id}/subject.json"})


if __name__ == "__main__":
    app.run()
