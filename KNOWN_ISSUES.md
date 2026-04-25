# Known Issues — Pipeline Académico → Canvas LMS

## Issue 1: Agentes no reciben contexto académico del subject JSON

**Estado**: ✅ Resuelto (2026-04-24)
**Severidad**: Crítica — los agentes DI y Content generaban contenido genérico ignorando el syllabus real.

### Descripción
Cuando el orquestador invocaba los agentes con `subject_id`, los agentes construían un prompt mínimo sin incluir el syllabus, competencias, resultados de aprendizaje ni los papers de Scopus. Esto causaba que:
- El agente DI generara objetivos de "Inteligencia Artificial y Machine Learning" en vez de "Ciencia de datos aplicada a las finanzas"
- El agente Content generara lecturas de "Advanced Research Methods and Innovation" (8 semanas) en vez del contenido real (5 semanas)
- Los quizzes fueran plantillas vacías con opciones como "Opción B", "Opción C"
- Los artefactos Maestría usaran libros genéricos en vez de los 20 papers de Scopus
- Los IDs de competencias fueran genéricos (C-01, C-02) en vez de los reales (C1, C2, C3, C4)

### Causa raíz
Los agentes recibían solo `subject_id` y un prompt genérico. No leían el JSON de S3 para obtener el contexto académico completo.

### Solución aplicada
1. **Cada agente ahora carga el subject JSON de S3** via `_load_subject_context(subject_id)`
2. **Prompts enriquecidos**: `_build_scholar_prompt()`, `_build_di_prompt()`, `_build_content_prompt()` inyectan syllabus, competencias, RAs, papers
3. **System prompts reforzados**: instrucciones explícitas de usar IDs exactos (C1-C4, RA1-RA2) y temas del syllabus
4. **Tools mejorados**: `generate_executive_readings` ahora acepta `papers` y `subtopics`; `generate_quizzes` acepta `objectives` y `syllabus`; `generate_maestria_artifacts` acepta `weekly_map` y `learning_outcomes`
5. **Orquestador simplificado**: solo pasa `subject_id`, cada agente carga su propio contexto

### Archivos modificados
- `src/agents/scholar/agent.py` — `_load_subject_context()`, `_build_scholar_prompt()`
- `src/agents/di/agent.py` — `_load_subject_context()`, `_build_di_prompt()`
- `src/agents/content/agent.py` — `_load_subject_context()`, `_build_content_prompt()`, tools mejorados
- `src/orchestrator/invoke_agent.py` — prompts simplificados (agentes cargan contexto)

---

## Issue 2: Papers irrelevantes en resultados de Scopus

**Estado**: Pendiente (requiere re-ejecución del pipeline)
**Severidad**: Baja — 2 de 20 papers no son relevantes al dominio financiero.

### Descripción
Los papers #10 ("Solar Photovoltaic Modules' Performance Reliability") y #15 ("A Review of Degradation and Reliability Analysis of a Solar PV Module") no tienen relación con ciencia de datos financieros. Se colaron por coincidencia de keywords genéricos.

### Solución
El Scholar agent ahora genera keywords específicos del dominio basados en el syllabus. Al re-ejecutar el pipeline, estos papers no deberían aparecer.

---

## Issue 3: Frontend — Archivos subidos no siempre aparecen en el dashboard

**Estado**: Parcialmente resuelto
**Severidad**: Baja

### Descripción
Cuando se sube un archivo desde el frontend, el presigned URL funciona y el archivo llega a S3, pero el registro en DynamoDB puede tardar hasta 30 segundos en aparecer (polling interval del dashboard).

### Workaround
Esperar 30 segundos y el dashboard se actualiza automáticamente.

---

## Issue 4: Registros corruptos de pruebas anteriores

**Estado**: Resuelto
**Severidad**: Baja

### Descripción
Algunos registros en DynamoDB y S3 contienen datos corruptos de pruebas anteriores (ej: contenido XML de .docx parseado como texto plano antes del fix de python-docx).

### Solución
Limpiar manualmente los registros corruptos de DynamoDB y S3.
