# Arquitectura del Sistema

## Estructura en Canvas LMS

Cada asignatura se publica como un curso con la siguiente estructura de módulos:

```
📁 Información General
  📄 Carta Descriptiva (objetivos, mapa semanal)
  📄 Guión de Masterclass (18-22 min, indicaciones [SLIDE])
  📄 Guía del Facilitador (tabla tiempo/actividad por semana)

📁 Semana 1: [Tema]
  📄 Introducción (150-200 palabras)
  📄 Lectura 1: Fundamentos (400-500 palabras, LLM)
  📄 Lectura 2: Aplicación (400-500 palabras, LLM)
  📄 Lectura 3: Análisis crítico (400-500 palabras, LLM)
  ❓ Quiz (8 preguntas razonamiento crítico, LLM)
  📄 Foro (caso de negocio + 3 preguntas + rúbrica pares HTML)

📁 Semana 2-N: [Tema]
  ... (misma estructura)

📁 Reto de Aprendizaje Agéntico
  📄 Escenario financiero mexicano (BMV/CNBV)
  📄 Pregunta directiva central
  📄 Entregable (1-2 páginas)
  📄 Rúbrica analítica 4 niveles (tabla HTML con colores)
```

## Subject JSON — Fuente Única de Verdad

```json
{
  "subject_id": "uuid",
  "metadata": {
    "subject_name": "Ciencia de datos aplicada a las finanzas",
    "program_name": "Maestría en Dirección y Tecnología Financiera",
    "program_type": "MAESTRIA",
    "subject_type": "FUNDAMENTOS",
    "language": "ES"
  },
  "academic_inputs": {
    "graduation_profile": "...",
    "competencies": [{"competency_id": "C1", "description": "..."}],
    "learning_outcomes": [{"ra_id": "RA1", "description": "..."}],
    "syllabus": "Contenido temático: 1) ... Duración: 5 semanas."
  },
  "research": {
    "keywords": ["financial data analytics", ...],
    "top20_papers": [{"title": "...", "abstract": "...", "doi": "..."}],
    "knowledge_matrix": [{"ra_id": "RA1", "core_concepts": [...], "key_methodologies": [...]}]
  },
  "instructional_design": {
    "learning_objectives": [...],
    "descriptive_card": {...},
    "content_map": {"weeks": [...]}
  },
  "content_package": {
    "weekly_units": [{"week": 1, "introduction": {...}, "readings": [...], "quiz": {...}, "forum": {...}}],
    "executive_readings": {"readings": [...]},
    "quizzes": {"quizzes": [...]},
    "forums": [...],
    "maestria_artifacts": {...},
    "masterclass_script": {...},
    "agentic_challenge": {...}
  },
  "qa_report": {"status": "PASS", "ra_coverage": {...}, "bloom_alignment": {...}},
  "pipeline_state": {"current_state": "PUBLISHED", "state_history": [...]},
  "publication": {"canvas_course_id": "118", "canvas_course_url": "https://..."}
}
```

## Estados del Pipeline

```
INGESTED → KNOWLEDGE_MATRIX_READY → DI_READY → CONTENT_READY
→ PENDING_APPROVAL → APPROVED → PUBLISHED
                   → REJECTED (→ re-process)
```

## Decisiones de Diseño

1. **Llamadas LLM individuales**: El Content agent hace 1 llamada LLM por recurso (~2K tokens cada una) en vez de una llamada masiva. Elimina MaxTokensReachedException.

2. **Auto-persistencia con state guard**: Los agentes persisten directamente a S3/DynamoDB pero nunca regresan un estado más avanzado.

3. **OpenAlex para abstracts**: Scopus API key no tiene acceso a Abstract Retrieval. OpenAlex (gratuito) complementa con abstracts via DOI.

4. **HTML directo para Canvas**: Las rúbricas y tablas se generan como HTML (no markdown) para renderizado correcto en Canvas LMS.

5. **Template Anáhuac MADTFIN**: Carta descriptiva y contenido siguen las especificaciones exactas del equipo de Tecnología Educativa.

6. **Bypass schema validator**: QA Gate y Checkpoint escriben directo a S3 para evitar que el schema validator rechace campos dinámicos (qa_report, validation).
