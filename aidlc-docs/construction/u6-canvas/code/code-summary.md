# Resumen de Código — U6: Publicación Canvas LMS

## Archivos Creados

### Modelos
- `src/canvas-publisher/models.py` — CanvasCourse, CanvasModule, CanvasModuleItem, PublicationResult

### Lógica de Negocio (funciones puras)
- `src/canvas-publisher/formatters.py` — markdown_to_html, format_page_payload, format_quiz_payload, format_quiz_question_payload, format_rubric_payload, format_apa_page_payload

### Canvas API Client
- `src/canvas-publisher/canvas_client.py` — CanvasClient con retry/backoff (tenacity), OAuth Token desde Secrets Manager (BR-CV07), métodos: find_course_by_code, create_course, create_module, create_page, create_quiz, create_quiz_question, create_rubric

### Publisher (Lambda)
- `src/canvas-publisher/publisher.py` — publish_course (orquestador), _publish_maestria_artifacts (4 artefactos BR-CV03), lambda_handler con validación APPROVED (BR-CV01), notificación SNS con URL de Canvas

### Tests
- `tests/unit/canvas-publisher/test_formatters.py` — 16 unitarios + 3 PBT (PBT-02 round-trip APA, PBT-03 invariants)

## Cobertura de Stories
- US-08b (Publicación automática Canvas): publisher.py completo
- Fase 5 del pipeline: bibliografía APA, shell del curso, módulos, quizzes, rúbricas, artefactos Maestría

## Cumplimiento de Extensiones
- SECURITY-01: TLS 1.2+ en httpx (enforce por defecto) ✅
- SECURITY-03: logger sin OAuth Token ✅
- SECURITY-06: IAM least-privilege (solo secreto Canvas + S3/DynamoDB) ✅
- SECURITY-12: OAuth Token exclusivamente desde Secrets Manager ✅
- PBT-02: Round-trip APA (count referencias preservado) ✅
- PBT-03: Invariantes markdown_to_html retorna string, format_page_payload tiene wiki_page ✅
- PBT-09: Hypothesis como framework PBT ✅
