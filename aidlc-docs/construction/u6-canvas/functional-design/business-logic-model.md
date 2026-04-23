# Modelo de Lógica de Negocio — U6: Publicación Canvas LMS

## publish_course(subject_json) → PublicationResult

### Fase 5 — Curaduría y Montaje

1. **Verificar estado APPROVED** (BR-CV01)
2. **Obtener OAuth Token** desde Secrets Manager (BR-CV07)
3. **Verificar idempotencia**: buscar curso existente por course_code (BR-CV09)
4. **Crear shell del curso** en Canvas (BR-CV02): nombre, código, workflow_state="unpublished"
5. **Crear módulo principal** con el nombre de la asignatura
6. **Publicar recursos por tipo**:
   - Lecturas ejecutivas → Canvas Pages (una por semana)
   - Guiones de masterclass → Canvas Pages
   - Quizzes → Canvas Quizzes con preguntas y respuestas
   - Casos de laboratorio → Canvas Assignments con rúbrica
   - Bibliografía APA → Canvas Page independiente (BR-CV05)
7. **Para Maestría**: publicar 4 artefactos como Pages independientes (BR-CV03)
8. **Crear y vincular rúbricas** a competencias del programa (BR-CV04)
9. **Actualizar JSON** con URLs de Canvas (BR-CV08)
10. **Actualizar estado** a PUBLISHED

## format_canvas_page(title, content_md) → dict
- Convierte Markdown a HTML básico compatible con Canvas
- Retorna payload para Canvas Pages API

## format_canvas_quiz(quiz) → dict
- Construye payload para Canvas Quizzes API
- Incluye preguntas, opciones, respuesta correcta y retroalimentación

## format_apa_page(bibliography) → dict
- Genera página Canvas con la bibliografía APA formateada
- Título: "Referencias Bibliográficas"
