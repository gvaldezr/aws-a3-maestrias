# Preguntas de Verificación de Requerimientos
## Pipeline Académico → Canvas LMS (Agent Core Framework)

Por favor responde cada pregunta llenando la letra de tu elección después de la etiqueta `[Answer]:`.
Si ninguna opción se ajusta, elige la última opción (Other/Otro) y describe tu preferencia.

---

## Pregunta 1 — Alcance de Asignaturas
¿Cuántas asignaturas se procesarán en paralelo en una ejecución típica del pipeline?

A) 1–5 asignaturas (piloto / prueba de concepto)
B) 6–20 asignaturas (un programa académico completo)
C) 21–100 asignaturas (múltiples programas simultáneos)
D) Más de 100 asignaturas (escala institucional)
E) Otro (describe después de [Answer]:)

[Answer]: B

---

## Pregunta 2 — Documentos de Entrada
¿En qué formato se proporcionarán el Perfil de Egreso y la Matriz de Competencias?

A) Archivos PDF cargados manualmente por el usuario
B) Archivos Word/Excel cargados manualmente
C) Documentos almacenados en un bucket S3 (carga previa)
D) Combinación de formatos (PDF, Word, Excel)
E) Otro (describe después de [Answer]:)

[Answer]: E combinacion de formatos cargados manualmente

---

## Pregunta 3 — Integración con Scopus API
¿Cuentas con credenciales activas de la API de Scopus (Elsevier)?

A) Sí, tenemos API Key institucional activa
B) No, necesitamos contemplar una alternativa (ej. Semantic Scholar, OpenAlex)
C) Sí, pero con cuota limitada — necesitamos gestión de rate limiting
D) Otro (describe después de [Answer]:)

[Answer]: A

---

## Pregunta 4 — Integración con Canvas LMS
¿Cuál es el tipo de instancia de Canvas LMS que se usará?

A) Canvas Cloud (Instructure-hosted) con acceso a API REST
B) Canvas auto-hospedado (on-premise) con acceso a API REST
C) Canvas en AWS (auto-hospedado en infraestructura propia)
D) Aún no tenemos Canvas — necesitamos contemplar el aprovisionamiento
E) Otro (describe después de [Answer]:)

[Answer]: A

---

## Pregunta 6 — Modelo de Lenguaje (LLM) para los Agentes
¿Qué modelo de lenguaje se usará para los agentes de IA (DI, Content, Scholar)?

A) Amazon Bedrock (Claude Sonnet / Haiku) — preferencia AWS nativa
B) OpenAI GPT-4o / GPT-4 Turbo
C) Anthropic Claude directamente (sin Bedrock)
D) Múltiples modelos según el agente (ej. Claude para DI, GPT para Content)
E) Otro (describe después de [Answer]:)

[Answer]: A

---

## Pregunta 7 — Orquestación del Pipeline Serverless
¿Cuál es la preferencia para orquestar el flujo entre agentes?

A) AWS Step Functions (orquestación visual, nativa AWS)
B) AWS EventBridge + Lambda (event-driven puro)
C) Amazon Bedrock Agents con Action Groups (Agent Core nativo)
D) Combinación: Bedrock Agents para lógica agéntica + Step Functions para orquestación macro
E) Otro (describe después de [Answer]:)

[Answer]: C

---

## Pregunta 8 — Almacenamiento del JSON de "Fuente Única de Verdad"
¿Dónde se almacenará el JSON enriquecido que fluye entre fases?

A) Amazon S3 (un objeto JSON por asignatura, versionado)
B) Amazon DynamoDB (registro por asignatura con atributos enriquecidos)
C) Amazon S3 + DynamoDB (S3 para payload completo, DynamoDB para estado/índice)
D) Otro (describe después de [Answer]:)

[Answer]: C

---

## Pregunta 9 — Control de Calidad (QA Gate)
¿Cómo debe comportarse el sistema cuando un recurso generado NO cubre el 100% de los Resultados de Aprendizaje?

A) Detener el pipeline y notificar al usuario para revisión manual
B) Reintentar automáticamente con el agente (máx. 3 intentos) antes de escalar
C) Publicar en Canvas con una bandera de advertencia visible para el docente
D) Registrar el gap en un reporte de QA y continuar con los RA cubiertos
E) Otro (describe después de [Answer]:)

[Answer]: B

---

## Pregunta 10 — Notificaciones y Monitoreo
¿Qué mecanismo de notificación se requiere cuando el pipeline completa o falla?

A) Email vía Amazon SES
B) Notificación en Slack / Teams (webhook)
C) Dashboard en AWS CloudWatch + alarmas SNS
D) Combinación de email + dashboard
E) Otro (describe después de [Answer]:)

[Answer]: C

---

## Pregunta 11 — Autenticación y Acceso al Sistema
¿Quién tendrá acceso para disparar el pipeline?

A) Solo administradores técnicos (acceso directo a AWS Console / CLI)
B) Coordinadores académicos a través de una interfaz web simple (S3 upload + trigger)
C) Integración con sistema institucional existente (SSO / LDAP)
D) API pública con autenticación por API Key
E) Otro (describe después de [Answer]:)

[Answer]: B

---

## Pregunta 12 — Idioma del Contenido Generado
¿En qué idioma deben generarse los contenidos del curso (lecturas, quizzes, guiones)?

A) Español únicamente
B) Inglés únicamente
C) Bilingüe (Español + Inglés) según configuración por asignatura
D) Otro (describe después de [Answer]:)

[Answer]: C

---

## Pregunta 13 — Extensión de Seguridad
¿Deben aplicarse reglas de seguridad como restricciones bloqueantes en este proyecto?

A) Sí — aplicar todas las reglas de SEGURIDAD como restricciones bloqueantes (recomendado para aplicaciones de producción)
B) No — omitir reglas de seguridad (adecuado para PoC, prototipos y proyectos experimentales)
C) Otro (describe después de [Answer]:)

[Answer]: A

---

## Pregunta 14 — Extensión de Testing Basado en Propiedades
¿Deben aplicarse reglas de Property-Based Testing (PBT) en este proyecto?

A) Sí — aplicar todas las reglas PBT como restricciones bloqueantes (recomendado para proyectos con lógica de negocio, transformaciones de datos o componentes con estado)
B) Parcial — aplicar PBT solo para funciones puras y round-trips de serialización
C) No — omitir reglas PBT (adecuado para aplicaciones CRUD simples o capas de integración delgadas)
D) Otro (describe después de [Answer]:)

[Answer]: A

---
