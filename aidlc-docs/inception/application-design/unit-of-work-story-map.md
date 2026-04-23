# Mapa de User Stories por Unidad de Trabajo
## Pipeline Académico → Canvas LMS

---

## U1 — Infraestructura Base + JSON Schema

| Story | Título | Cobertura |
|---|---|---|
| US-16 | Auditoría de Acciones del Sistema | CloudWatch logs, retención 90 días, permisos de borrado |

**Notas**: U1 es la fundación técnica. La mayoría de las historias dependen indirectamente de U1 a través del JSON schema y la infraestructura de estado.

---

## U2 — Agente Scholar

| Story | Título | Cobertura |
|---|---|---|
| US-03 | Búsqueda Automatizada en Scopus | Fases 1 y 2 completas: keywords, búsqueda Q1/Q2, Top 20 |
| US-09 | Agente Scholar: Generación de Matriz de Conocimiento | Elicitación académica, Matriz de Conocimiento Validado |
| US-10 | Agente Scholar: Escalación por Corpus Insuficiente | Detección de corpus insuficiente, notificación SNS |

---

## U3 — Agente DI

| Story | Título | Cobertura |
|---|---|---|
| US-04 | Generación de Carta Descriptiva con Alineación Bloom | Estructuración, Mapa de Contenidos, Carta Descriptiva V1, trazabilidad |
| US-11 | Agente DI: Detección de Gaps de Alineación | Detección de objetivos sin competencia, escalación |
| US-18 | Agente DI: Estructuración por Tipo de Materia | Fundamentos / Concentración / Proyecto |

---

## U4 — Agente Content

| Story | Título | Cobertura |
|---|---|---|
| US-05 | Generación del Paquete Multimedia | Lecturas, masterclass, quizzes, casos de laboratorio |
| US-12 | Agente Content: Generación de los Cuatro Artefactos de Maestría | Dashboard, Mapa Ruta Crítica, Casos Ejecutivos, Guía Facilitador |
| US-13 | Agente Content: Generación Bilingüe | Español / Inglés / Bilingüe por asignatura |
| US-19 | Agente Content: Escalación por Cobertura Incompleta de RA | Reintentos automáticos, escalación tras 3 intentos |

---

## U5 — QA Gate + Checkpoint Humano

| Story | Título | Cobertura |
|---|---|---|
| US-06 | QA Gate: Validación de Cobertura Completa | Validación RA, Bloom-Competencias, 4 artefactos Maestría |
| US-07 | Checkpoint de Validación Humana: Aprobación | Notificación, previsualización, aprobación, registro |
| US-08 | Checkpoint de Validación Humana: Rechazo y Corrección | Rechazo con comentarios, corrección por agente, ciclos |

---

## U6 — Publicación Canvas LMS

| Story | Título | Cobertura |
|---|---|---|
| US-08b | Publicación Automática del Curso en Canvas | Fase 5 completa: bibliografía APA, shell, módulos, rúbricas, artefactos Maestría |

---

## U7 — Interfaz Web

| Story | Título | Cobertura |
|---|---|---|
| US-01 | Carga de Documentos de Entrada | Upload PDF/DOCX/XLSX, disparo del pipeline, confirmación |
| US-02 | Monitoreo del Estado del Pipeline | Dashboard en tiempo real, estados, historial |
| US-14 | Gestión Segura de Credenciales | Secrets Manager, sin credenciales en logs/código |
| US-15 | Autenticación del Staff en la Interfaz Web | Cognito, JWT, MFA Admin, bloqueo por intentos fallidos |

---

## Cobertura Total

| Unidad | Stories asignadas | Total |
|---|---|---|
| U1 | US-16 | 1 |
| U2 | US-03, US-09, US-10 | 3 |
| U3 | US-04, US-11, US-18 | 3 |
| U4 | US-05, US-12, US-13, US-19 | 4 |
| U5 | US-06, US-07, US-08 | 3 |
| U6 | US-08b | 1 |
| U7 | US-01, US-02, US-14, US-15 | 4 |
| **Total** | | **19 / 19** ✅ |

Todas las 19 user stories están asignadas a una unidad de trabajo.
