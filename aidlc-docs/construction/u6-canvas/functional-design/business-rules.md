# Reglas de Negocio — U6: Publicación Canvas LMS

## BR-CV01 — Solo se publica contenido APPROVED
El publisher solo puede ejecutarse si el estado del JSON es APPROVED. Cualquier otro estado es un error.

## BR-CV02 — Curso publicado en estado borrador
El curso se crea en Canvas con workflow_state="unpublished". La activación para estudiantes es manual por el docente.

## BR-CV03 — Artefactos Maestría como páginas independientes
Para Maestría, los 4 artefactos (Dashboard de Evidencia, Mapa de Ruta Crítica, Repositorio de Casos, Guía del Facilitador) se publican como páginas Canvas independientes dentro del módulo correspondiente.

## BR-CV04 — Rúbricas vinculadas a competencias por ID
Las rúbricas de evaluación deben referenciar los competency_ids del programa. La vinculación es trazable al Perfil de Egreso original.

## BR-CV05 — Bibliografía APA como recurso del módulo
La bibliografía en formato APA se publica como una página Canvas independiente en el módulo de la asignatura.

## BR-CV06 — Reintentos con backoff ante fallos de Canvas API
Ante errores de Canvas API (5xx, timeout), se reintenta con backoff exponencial (1s, 2s, 4s), máximo 3 intentos.

## BR-CV07 — Credenciales desde Secrets Manager
El OAuth Token de Canvas se obtiene exclusivamente desde AWS Secrets Manager. Nunca se hardcodea.

## BR-CV08 — URLs de Canvas almacenadas en JSON
Tras la publicación exitosa, el JSON se actualiza con: canvas_course_id, canvas_course_url, module_urls y published_at.

## BR-CV09 — Idempotencia por subject_id
Si el pipeline se re-ejecuta para la misma asignatura, el publisher verifica si ya existe un curso en Canvas con el mismo course_code antes de crear uno nuevo.
