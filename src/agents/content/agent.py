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
    def generate_executive_readings(weekly_map: list, subject_name: str, language: str) -> dict:
        """Generate executive readings for each week of the course map.

        Args:
            weekly_map: List of week dicts with week, theme, bloom_level, activities
            subject_name: Name of the subject
            language: Content language: ES, EN, or BILINGUAL
        """
        readings = []
        for week in weekly_map:
            w = week.get("week", 1)
            theme = week.get("theme", "")
            content = (
                f"# Lectura Ejecutiva — Semana {w}: {theme}\n\n"
                f"## Conceptos Clave\n\n- Concepto 1 de {theme}\n- Concepto 2 con aplicación directiva\n\n"
                f"## Aplicación Profesional\n\nCaso de aplicación en contexto de {subject_name}.\n"
            )
            if language == "BILINGUAL":
                content += f"\n---\n# Executive Reading — Week {w}: {theme}\n\n[English version]"
            readings.append({"week": w, "title": f"Semana {w}: {theme}", "content_md": content, "language": language})
        return {"readings": readings}

    @tool
    def generate_quizzes(learning_outcomes: list, subject_name: str, language: str) -> dict:
        """Generate quizzes with minimum 3 questions per learning outcome.

        Args:
            learning_outcomes: List of dicts with ra_id and description
            subject_name: Name of the subject
            language: Content language
        """
        quizzes = []
        for lo in learning_outcomes:
            questions = [
                {"question": f"¿Cuál es el concepto central de '{lo['description']}'?",
                 "options": [f"Opción correcta sobre {lo['description'][:30]}", "Opción B", "Opción C", "Opción D"],
                 "correct_answer": 0, "feedback": f"Correcto — concepto fundamental de {subject_name}."},
                {"question": f"¿Cómo se aplica '{lo['description']}' en contexto directivo?",
                 "options": ["Aplicación estratégica", "Sin aplicación", "Solo teórica", "Irrelevante"],
                 "correct_answer": 0, "feedback": "La aplicación directiva implica decisiones estratégicas."},
                {"question": f"¿Qué evidencia respalda '{lo['description']}'?",
                 "options": ["Investigación Q1/Q2", "Solo opinión", "Sin evidencia", "Datos obsoletos"],
                 "correct_answer": 0, "feedback": "Evidencia de investigación académica de alto impacto."},
            ]
            quizzes.append({"ra_id": lo["ra_id"], "questions": questions})
        return {"quizzes": quizzes}

    @tool
    def generate_maestria_artifacts(papers: list, subject_name: str, competencies: list, language: str) -> dict:
        """Generate the 4 mandatory Maestría artifacts.

        Args:
            papers: Top 20 papers from Scholar agent
            subject_name: Name of the subject
            competencies: Program competencies
            language: Content language
        """
        # Dashboard de Evidencia
        rows = ["| # | Título | Año | Revista | Hallazgo |", "|---|--------|-----|---------|----------|"]
        for i, p in enumerate(papers[:10], 1):
            rows.append(f"| {i} | {p.get('title','')[:50]} | {p.get('year','')} | {p.get('journal','')[:30]} | {p.get('key_finding','')[:50]} |")

        # Mapa de Ruta Crítica
        critical_path = (
            "| Semana | Actividad | Entregable | Criterio |\n|---|---|---|---|\n"
            f"| 1 | Lectura de papers clave | Resumen ejecutivo | 3 conceptos clave |\n"
            f"| 2 | Aplicación a caso real | Análisis de caso | 2 competencias vinculadas |\n"
            f"| 3 | Síntesis e integración | Propuesta ejecutiva | Todos los RA cubiertos |"
        )

        # Casos Ejecutivos
        comp_ids = [c["competency_id"] for c in competencies[:2]]
        cases = [{"title": f"Caso: {subject_name}", "context": f"Organización implementa {subject_name}",
                  "data": "Datos del caso", "questions": ["¿Cómo aplicar?", "¿Qué métricas?", "¿Qué riesgos?"],
                  "rubric": {"criteria": ["Análisis (30%)", "Aplicación (40%)", "Propuesta (30%)"], "competency_ids": comp_ids}}]

        # Guía del Facilitador
        sessions = [{"week": w, "duration_minutes": 90,
                     "objective": f"Semana {w} de {subject_name}",
                     "sequence": [{"time": "0-10min", "activity": "Apertura"}, {"time": "10-40min", "activity": "Exposición"},
                                  {"time": "40-70min", "activity": "Caso práctico"}, {"time": "70-90min", "activity": "Cierre"}],
                     "trigger_questions": [f"¿Cómo conecta con su experiencia?"],
                     "formative_criteria": "Participación y vinculación con competencias"} for w in range(1, 5)]

        return {
            "evidence_dashboard": {"html_content": "\n".join(rows)},
            "critical_path_map": {"markdown_content": critical_path},
            "executive_cases_repository": {"cases": cases},
            "facilitator_guide": {"sessions": sessions},
        }

    _content_agent = Agent(
        model=model,
        tools=[generate_executive_readings, generate_quizzes, generate_maestria_artifacts],
        system_prompt=(
            "You are Content, a content generation agent for professional Master's programs. "
            "Use generate_executive_readings, generate_quizzes, and generate_maestria_artifacts (if Maestría). "
            "Return JSON with: executive_readings, quizzes, maestria_artifacts, lab_cases"
        ),
    )
    return _content_agent


@app.entrypoint
def invoke(payload: dict, context: RequestContext = None) -> dict:
    """AgentCore Runtime entrypoint for Content Agent."""
    prompt = payload.get("prompt", "")
    subject_id = payload.get("subject_id", "")

    if not prompt and not subject_id:
        return {"result": "Content Agent ready. Send a prompt or subject_id to begin content generation."}

    agent = _get_agent()

    if subject_id:
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
