"""
Prompt template para el Paquete de Contenido — MADTFIN Anáhuac Mayab.
Basado en las especificaciones del equipo de Tecnología Educativa.
"""

CONTENT_PACKAGE_TEMPLATE = """A partir de la Carta Descriptiva recibida, genera el paquete completo de recursos para una materia de {num_weeks} semanas.

CARTA DESCRIPTIVA DE ENTRADA:
- Nombre: {subject_name}
- Tipo: {subject_type}
- Programa: MADTFIN (Maestría en Dirección y Transformación Financiera)
- Objetivos de aprendizaje: {objectives_text}
- Mapa de contenidos semanal: {weekly_map_text}
- Competencias: {competencies_text}
- Resultados de aprendizaje: {learning_outcomes_text}
- Corpus académico (papers Q1/Q2 con abstracts): {corpus_text}
- Knowledge Matrix: {km_text}

GENERA LOS SIGUIENTES RECURSOS:

1. LECTURAS EJECUTIVAS (2 por semana, semanas 1 a {num_weeks_minus_1}):
- Extension: 400-500 palabras cada una.
- Tono: ejecutivo, sin jerga academica innecesaria.
- Estructura: contexto del problema / concepto clave / aplicacion directiva / pregunta de reflexion.
- IMPORTANTE: Usa los conceptos y definiciones de la Knowledge Matrix para escribir contenido sustantivo.
- Referencia los papers del corpus cuando sea pertinente.

2. GUION DE MASTERCLASS (1 por materia):
- Duracion objetivo: 18-22 minutos.
- Estructura: gancho directivo (2 min) / desarrollo conceptual con caso (14 min) / sintesis y decision (4 min) / llamada a la accion (2 min).
- Incluye indicaciones de pantalla: [SLIDE], [DATO EN PANTALLA], [CASO VISUAL].

3. QUIZ DE RAZONAMIENTO CRITICO (1 por materia, semana 3):
- 8 preguntas de opcion multiple con 4 distractores.
- Al menos 3 preguntas en nivel Analizar o Evaluar (Bloom).
- Cada pregunta incluye retroalimentacion de 2-3 lineas para la respuesta correcta.

4. RETO DE APRENDIZAJE AGENTICO (1 por materia, semana 2):
- Escenario ejecutivo real del sector financiero mexicano.
- Entregable: documento de 1-2 paginas con una decision justificada.
- Rubrica analitica de 4 niveles: Excelente / Bueno / Regular / Deficiente.
- Criterios: fundamentacion en evidencia, coherencia argumentativa, pertinencia del contexto regulatorio mexicano, claridad directiva.

RESTRICCIONES GENERALES:
- No uses bullets para explicar conceptos; usa prosa con conectores.
- Maximo 750 palabras por lectura ejecutiva.
- Los casos y escenarios deben referenciar empresas o regulaciones reales de Mexico cuando sea posible (CNBV, Banxico, BMV, LFPDPPP, NIF).
- No uses guiones largos.

CALL THESE TOOLS:
1. generate_executive_readings(weekly_map=<weekly_map>, subject_name="{subject_name}", language="{language}", papers=<papers>, knowledge_matrix=<knowledge_matrix>)
2. generate_quizzes(learning_outcomes=<learning_outcomes>, subject_name="{subject_name}", language="{language}", objectives=<objectives>)
3. generate_maestria_artifacts(papers=<papers>, subject_name="{subject_name}", competencies=<competencies>, language="{language}", weekly_map=<weekly_map>, learning_outcomes=<learning_outcomes>)

Return JSON with keys: executive_readings, quizzes, maestria_artifacts, masterclass_script, agentic_challenge.
"""


def build_content_package_prompt(
    subject_name: str,
    subject_type: str,
    language: str,
    num_weeks: int,
    objectives: list,
    weekly_map: list,
    competencies: list,
    learning_outcomes: list,
    papers: list,
    knowledge_matrix: list,
) -> str:
    """Build the content package prompt with actual data."""
    objectives_text = "; ".join(
        f"{o.get('objective_id','')}: [{o.get('bloom_level','')}] {o.get('description','')[:100]}"
        for o in objectives
    )

    weekly_map_text = "; ".join(
        f"Sem {w.get('week','')}: {w.get('theme','')[:50]} [{w.get('bloom_level','')}]"
        for w in weekly_map
    )

    competencies_text = "; ".join(
        f"{c['competency_id']}: {c['description'][:80]}"
        for c in competencies
    )

    lo_text = "; ".join(
        f"{lo['ra_id']}: {lo['description'][:80]}"
        for lo in learning_outcomes
    )

    # Papers (compact — save tokens)
    corpus_lines = []
    for p in papers[:10]:
        line = f"- {p.get('title','')[:50]} ({p.get('year','')}). {p.get('journal','')[:25]}."
        abstract = p.get("abstract", "")
        if abstract:
            line += f" {abstract[:80]}"
        corpus_lines.append(line)
    corpus_text = "\n".join(corpus_lines)

    # Knowledge matrix (very compact — concept names + short definitions)
    import json
    km_items = []
    km_list = knowledge_matrix if isinstance(knowledge_matrix, list) else []
    for km in km_list[:2]:
        if isinstance(km, dict):
            for c in km.get("core_concepts", [])[:3]:
                if isinstance(c, dict):
                    km_items.append(f"- {c.get('concept','')}: {c.get('definition','')[:80]}")
    km_text = "\n".join(km_items) if km_items else "No disponible"

    return CONTENT_PACKAGE_TEMPLATE.format(
        subject_name=subject_name,
        subject_type=subject_type,
        language=language,
        num_weeks=num_weeks,
        num_weeks_minus_1=num_weeks - 1,
        objectives_text=objectives_text,
        weekly_map_text=weekly_map_text,
        competencies_text=competencies_text,
        learning_outcomes_text=lo_text,
        corpus_text=corpus_text,
        km_text=km_text,
    )
