"""
LLM Content Generator — individual small calls to Claude for each resource.
Each call uses ~2K tokens prompt + ~2K response, never hitting token limits.
"""
from __future__ import annotations

import json
import os
import logging

log = logging.getLogger(__name__)


def _get_model():
    """Lazy-init Bedrock model for individual calls."""
    from strands.models import BedrockModel
    return BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-6",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
        temperature=0.4,
        max_tokens=4096,
    )


def _call_llm(prompt: str) -> str:
    """Make a single LLM call with a short prompt. Returns text response."""
    from strands import Agent
    model = _get_model()
    agent = Agent(model=model, tools=[], system_prompt="Responde en espanol. Solo devuelve el contenido solicitado, sin preambulos.")
    result = agent(prompt)
    return str(result)


def generate_reading_llm(week_num: int, total_weeks: int, theme: str, subject_name: str,
                         bloom_level: str, subtopics: list, concepts: list,
                         papers: list, methodologies: list) -> str:
    """Generate one executive reading using LLM. ~400-500 words, narrative prose."""
    concepts_text = "\n".join(
        f"- {c.get('concept','')}: {c.get('definition','')[:150]}"
        for c in concepts[:4]
    ) if concepts else "No disponible"

    papers_text = "\n".join(
        f"- {p.get('title','')[:50]} ({p.get('year','')}, {p.get('journal','')[:25]})"
        for p in papers[:3]
    ) if papers else "No disponible"

    methods_text = ", ".join(methodologies[:5]) if methodologies else "No disponible"
    subtopics_text = ", ".join(subtopics[:4]) if subtopics else theme

    prompt = f"""Genera una lectura ejecutiva de 400-500 palabras para la Semana {week_num} de {total_weeks} de la asignatura "{subject_name}".

Tema: {theme}
Nivel Bloom: {bloom_level}
Subtemas: {subtopics_text}

Conceptos clave (de la Knowledge Matrix):
{concepts_text}

Metodologias: {methods_text}

Papers de referencia:
{papers_text}

FORMATO: Prosa narrativa ejecutiva (sin bullets para explicar conceptos). Estructura:
1. Contexto del problema (1 parrafo)
2. Concepto clave con definicion academica (2 parrafos)
3. Aplicacion directiva en el sector financiero mexicano (1 parrafo)
4. Pregunta de reflexion (1 linea)

RESTRICCIONES: Max 500 palabras. Tono ejecutivo. Contexto regulatorio Mexico (CNBV, Banxico, NIF). Sin guiones largos. Acronimos completos en primera aparicion."""

    try:
        return _call_llm(prompt)
    except Exception as e:
        log.warning(f"LLM reading generation failed for week {week_num}: {e}")
        return f"# Lectura Ejecutiva, Semana {week_num}: {theme}\n\n[Contenido pendiente de generacion LLM]\n"


def generate_quiz_llm(subject_name: str, ra_descriptions: list, objectives: list) -> list:
    """Generate 8 critical reasoning questions using LLM."""
    ra_text = "\n".join(f"- {r[:80]}" for r in ra_descriptions[:3])
    obj_text = "\n".join(f"- {o[:80]}" for o in objectives[:5])

    prompt = f"""Genera 8 preguntas de razonamiento critico para la asignatura "{subject_name}" de la Maestria MADTFIN (Anahuac Mayab).

Resultados de aprendizaje:
{ra_text}

Objetivos:
{obj_text}

FORMATO JSON (array de 8 objetos):
[{{"question_id":"Q1","bloom_level":"ANALIZAR","question":"...","options":["correcta","distractor1","distractor2","distractor3"],"correct_answer":0,"feedback":"retroalimentacion de 2-3 lineas"}}]

REGLAS:
- 8 preguntas total
- Al menos 3 en nivel ANALIZAR o EVALUAR (Bloom)
- 4 opciones por pregunta (1 correcta + 3 distractores plausibles)
- Retroalimentacion de 2-3 lineas para la respuesta correcta
- Contexto del sector financiero mexicano (CNBV, Banxico, BMV)
- Tono ejecutivo, sin jerga innecesaria

Devuelve SOLO el array JSON, sin texto adicional."""

    try:
        result = _call_llm(prompt)
        # Extract JSON array from response
        import re
        # Try direct parse
        try:
            questions = json.loads(result)
            if isinstance(questions, list) and len(questions) >= 6:
                return questions
        except json.JSONDecodeError:
            pass
        # Try extracting from markdown
        matches = re.findall(r'\[.*\]', result, re.DOTALL)
        for m in matches:
            try:
                questions = json.loads(m)
                if isinstance(questions, list) and len(questions) >= 6:
                    return questions
            except json.JSONDecodeError:
                continue
        log.warning("LLM quiz: could not parse JSON response")
        return []
    except Exception as e:
        log.warning(f"LLM quiz generation failed: {e}")
        return []


def generate_masterclass_llm(subject_name: str, theme: str, objectives: list,
                              papers: list, competencies: list) -> dict:
    """Generate masterclass script using LLM."""
    obj_text = "; ".join(objectives[:3])
    papers_text = "; ".join(f"{p.get('title','')[:40]} ({p.get('year','')})" for p in papers[:3])
    comp_text = ", ".join(competencies[:4])

    prompt = f"""Genera un guion de masterclass de 18-22 minutos para "{subject_name}" (MADTFIN, Anahuac Mayab).

Tema central: {theme}
Objetivos: {obj_text}
Papers de referencia: {papers_text}
Competencias: {comp_text}

ESTRUCTURA (devuelve JSON):
{{"title":"...","duration_minutes":20,"structure":[
  {{"section":"Gancho directivo","time":"0:00-2:00","content":"[SLIDE: ...] texto narrativo...","notes":"..."}},
  {{"section":"Desarrollo conceptual con caso","time":"2:00-16:00","content":"[CASO VISUAL] ... [DATO EN PANTALLA] ...","notes":"..."}},
  {{"section":"Sintesis y decision","time":"16:00-20:00","content":"...","notes":"..."}},
  {{"section":"Llamada a la accion","time":"20:00-22:00","content":"...","notes":"..."}}
]}}

REGLAS: Incluir [SLIDE], [DATO EN PANTALLA], [CASO VISUAL]. Caso del sector financiero mexicano. Sin bullets, prosa narrativa. Devuelve SOLO JSON."""

    try:
        result = _call_llm(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            import re
            matches = re.findall(r'\{.*\}', result, re.DOTALL)
            for m in matches:
                try:
                    parsed = json.loads(m)
                    if "structure" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
        return {}
    except Exception as e:
        log.warning(f"LLM masterclass generation failed: {e}")
        return {}


def generate_challenge_llm(subject_name: str, ra_descriptions: list,
                            competencies: list, week_theme: str) -> dict:
    """Generate agentic learning challenge using LLM."""
    ra_text = "; ".join(ra_descriptions[:2])
    comp_text = ", ".join(competencies[:4])

    prompt = f"""Genera un reto de aprendizaje agentico para "{subject_name}" (MADTFIN, Anahuac Mayab).

Tema de semana 2: {week_theme}
Resultados de aprendizaje: {ra_text}
Competencias: {comp_text}

FORMATO JSON:
{{"title":"...","week":2,"scenario":"escenario ejecutivo real del sector financiero mexicano (BMV, CNBV, Banxico)...","central_question":"pregunta directiva central...","deliverable":"documento 1-2 paginas con decision justificada...","rubric":{{"criteria":[
  {{"criterion":"Fundamentacion en evidencia","weight":"25%","excelente":"...","bueno":"...","regular":"...","deficiente":"..."}},
  {{"criterion":"Coherencia argumentativa","weight":"25%","excelente":"...","bueno":"...","regular":"...","deficiente":"..."}},
  {{"criterion":"Pertinencia regulatoria mexicana","weight":"25%","excelente":"...","bueno":"...","regular":"...","deficiente":"..."}},
  {{"criterion":"Claridad directiva","weight":"25%","excelente":"...","bueno":"...","regular":"...","deficiente":"..."}}
]}}}}

REGLAS: Escenario real Mexico. Rubrica 4 niveles. Sin bullets, prosa. Devuelve SOLO JSON."""

    try:
        result = _call_llm(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            import re
            matches = re.findall(r'\{.*\}', result, re.DOTALL)
            for m in matches:
                try:
                    parsed = json.loads(m)
                    if "scenario" in parsed or "rubric" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue
        return {}
    except Exception as e:
        log.warning(f"LLM challenge generation failed: {e}")
        return {}
