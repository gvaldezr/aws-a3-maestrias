"""
Prompt template para la Carta Descriptiva V1 — MADTFIN Anáhuac Mayab.
Basado en las especificaciones del equipo de Tecnología Educativa.
"""

CARTA_DESCRIPTIVA_TEMPLATE = """Tu tarea es generar una Carta Descriptiva V1 para la siguiente materia de la Maestría en Dirección y Transformación Financiera (MADTFIN) de la Universidad Anáhuac Mayab.

DATOS DE LA MATERIA:
- Nombre: {subject_name}
- Tipo: {subject_type}
- Resultado de Aprendizaje 1: {ra_1}
- Resultado de Aprendizaje 2: {ra_2}
- Contenido temático oficial: {syllabus}
- Competencias del programa: {competencies}
- Corpus académico validado (papers Q1/Q2): {corpus_papers}

AUDIENCIA: Directivos financieros con experiencia mínima de 5 años. Perfil ejecutivo. Sin tiempo para contenido redundante.

INSTRUCCIONES DE GENERACIÓN:

1. Objetivos de aprendizaje: Redacta objetivos en taxonomía de Bloom nivel Aplicar o superior (Aplicar, Analizar, Evaluar, Crear). Cada objetivo inicia con verbo de desempeño, incluye objeto de conocimiento y contexto organizacional mexicano. Genera un objetivo por cada tema del contenido temático oficial.

2. Mapa de contenidos: Organiza el temario en {num_weeks} semanas de trabajo independiente siguiendo el ciclo Ingesta / Aplicación / Consolidación / Síntesis. Cada semana debe tener un tema del contenido temático oficial con subtemas específicos.

3. Casos ejecutivos: Propón 2 casos de estudio con escenario real del sector financiero mexicano (puede ser CNBV, banca comercial, fintech, mercados bursátiles). Cada caso incluye: situación, pregunta directiva central y decisión esperada del estudiante.

4. Bibliografía: Selecciona los 5 papers más relevantes del corpus recibido. Formato APA 7.

RESTRICCIONES:
- Máximo 750 palabras por sección de contenido.
- No uses listas de bullets para explicar conceptos; usa prosa narrativa con conectores.
- Escribe los acrónimos completos en su primera aparición.
- No uses guiones largos; usa comas o paréntesis.
- El contexto regulatorio debe ser específico de México: CNBV, Banxico, LFPDPPP, NIF, según aplique a la materia.

Devuelve la Carta Descriptiva en formato JSON con las secciones: objetivos_aprendizaje, mapa_contenidos, casos_ejecutivos, bibliografia_apa.
Adicionalmente incluye: traceability_matrix (objetivo -> bloom_level -> competency_ids -> ra_ids) y alignment_gaps.
"""


def build_carta_descriptiva_prompt(
    subject_name: str,
    subject_type: str,
    learning_outcomes: list,
    syllabus: str,
    competencies: list,
    papers: list,
    num_weeks: int = 5,
) -> str:
    """Build the Carta Descriptiva prompt with actual data."""
    ra_1 = learning_outcomes[0]["description"] if learning_outcomes else ""
    ra_2 = learning_outcomes[1]["description"] if len(learning_outcomes) > 1 else ""

    comp_text = "; ".join(
        f"{c['competency_id']}: {c['description'][:100]}"
        for c in competencies
    )

    corpus = "\n".join(
        f"- {p.get('title','')} ({', '.join(p.get('authors',[])) if isinstance(p.get('authors'), list) else p.get('authors','')}, "
        f"{p.get('year','')}). {p.get('journal','')}. {p.get('key_finding','')}"
        for p in papers[:20]
    )

    return CARTA_DESCRIPTIVA_TEMPLATE.format(
        subject_name=subject_name,
        subject_type=subject_type,
        ra_1=ra_1,
        ra_2=ra_2,
        syllabus=syllabus,
        competencies=comp_text,
        corpus_papers=corpus,
        num_weeks=num_weeks,
    )
