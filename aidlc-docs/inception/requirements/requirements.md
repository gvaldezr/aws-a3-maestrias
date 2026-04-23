# Documento de Requerimientos
## Pipeline Académico → Canvas LMS con Agent Core Framework

---

## Resumen de Intención

| Campo | Valor |
|---|---|
| Solicitud del usuario | Pipeline automatizado y serverless que transforma insumos de planeación académica en cursos operativos en Canvas LMS, usando Agent Core Framework (Amazon Bedrock Agents) |
| Tipo de solicitud | Nuevo proyecto (Greenfield) |
| Estimación de alcance | Multi-sistema (Scopus API + Amazon Bedrock + Canvas LMS API + AWS serverless) |
| Estimación de complejidad | Alta — pipeline agéntico multi-agente con integraciones externas, orquestación event-driven y control de calidad automatizado |
| Profundidad de requerimientos | Comprensiva |

---

## Contexto del Sistema

El sistema procesa entre 6 y 20 asignaturas por ejecución (un programa académico completo). Los documentos de entrada (Perfil de Egreso, Matriz de Competencias, datos de asignatura) se proporcionan en combinación de formatos PDF, Word y Excel, cargados manualmente por el usuario a través de una interfaz web simple accesible para Staff de Tecnología Educativa.

El contenido generado es bilingüe (Español / Inglés) configurable por asignatura.

### Proceso de Investigación → Generación (5 Fases)

El pipeline implementa el siguiente proceso secuencial por asignatura. Cada fase produce un entregable que alimenta la siguiente y se persiste en el JSON de fuente única de verdad:

| Fase | Descripción | Entregable |
|---|---|---|
| **1. Ingesta y Búsqueda** | Definición de keywords a partir de los RA y competencias; búsqueda automatizada en Scopus con filtros de impacto (Q1/Q2) | Listado Top 20 de artículos y papers de vanguardia |
| **2. Elicitación Académica** | Extracción de conceptos, metodologías y casos de éxito con enfoque directivo y tecnológico | Matriz de Conocimiento Académico Validado |
| **3. Estructuración** | Organización del conocimiento según el tipo de materia (Fundamentos, Concentración o Proyecto); objetivos en nivel Analizar/Evaluar de Bloom | Mapa de Contenidos y Objetivos |
| **4. Generación de Recursos** | Creación de contenido ejecutivo, casos de laboratorio agéntico y guiones de masterclass | Carta Descriptiva y Paquete de Recursos Multimedia |
| **5. Curaduría y Montaje** | Selección bibliográfica en formato APA y exportación automática a plantillas HTML/Markdown para Canvas LMS | Aula Virtual lista para Validación Humana |

> **Nota**: La Fase 5 exporta a plantillas HTML/Markdown estructuradas para Canvas LMS. La integración con Canva está fuera del alcance de este proyecto.

---

## Requerimientos Funcionales

### RF-01 — Ingesta de Documentos de Entrada
- El sistema debe aceptar documentos en formatos PDF, Word (.docx) y Excel (.xlsx)
- El Staff de Tecnología Educativa carga los documentos a través de una interfaz web (S3 upload + trigger)
- El sistema debe parsear y extraer: Perfil de Egreso, Matriz de Competencias, nombre de asignatura, Resultados de Aprendizaje (RA) y temario oficial
- La carga de documentos dispara automáticamente el pipeline

### RF-02 — Construcción del JSON de Fuente Única de Verdad
- Por cada asignatura se genera un objeto JSON que actúa como fuente única de verdad
- El JSON se almacena en Amazon S3 (payload completo, versionado) y Amazon DynamoDB (estado e índice)
- El JSON se enriquece progresivamente en cada fase del pipeline (ingesta → investigación → diseño instruccional → contenido → validación → publicación)
- El esquema del JSON debe incluir: metadatos de asignatura, RA, competencias vinculadas, Top 20 Scopus, Matriz de Conocimiento Académico Validado, Mapa de Contenidos y Objetivos, Carta Descriptiva V1, paquete de contenido (incluyendo los 4 artefactos de Maestría), bibliografía APA, estado de aprobación y estado de publicación en Canvas

### RF-03 — Agente Investigador (Scholar) — Fases 1 y 2
- **Fase 1 — Ingesta y Búsqueda**: Genera keywords de alta precisión a partir de los RA y competencias de la asignatura; ejecuta búsqueda automatizada en la API de Scopus con filtros de impacto (Q1/Q2); recupera y rankea el Top 20 de artículos y papers de vanguardia
- **Fase 2 — Elicitación Académica**: Extrae conceptos clave, metodologías y casos de éxito de los papers recuperados, con enfoque directivo y tecnológico; genera la Matriz de Conocimiento Académico Validado
- Gestiona rate limiting de la API de Scopus (API Key institucional activa)
- Enriquece el JSON con: listado Top 20, Matriz de Conocimiento Académico Validado y metadatos de cada paper (título, autores, año, revista, cuartil, hallazgo principal)

### RF-04 — Agente de Diseño Instruccional (DI) — Fase 3
- **Fase 3 — Estructuración**: Organiza el conocimiento de la Matriz Académica según el tipo de materia (Fundamentos, Concentración o Proyecto); genera el Mapa de Contenidos y Objetivos con niveles de Bloom priorizados en Analizar/Evaluar
- Cruza el Mapa de Contenidos con el Perfil de Egreso para redactar la Carta Descriptiva V1
- Genera: mapa de 4 semanas (Ingesta → Síntesis) y diseño de casos de estudio vinculados a la realidad profesional del egresado
- Enriquece el JSON con: Mapa de Contenidos y Objetivos, Carta Descriptiva V1 y artefactos de diseño instruccional
- Utiliza Amazon Bedrock (Claude Sonnet / Haiku) como LLM

### RF-04a — Alineación Bloom–Competencias en la Carta Descriptiva V1
- Cada objetivo de aprendizaje de la Carta Descriptiva V1 debe redactarse usando verbos de la **Taxonomía de Bloom** (Recordar, Comprender, Aplicar, Analizar, Evaluar, Crear), especificando explícitamente el nivel cognitivo asignado
- Cada objetivo debe mapearse directamente a una o más competencias del programa (referenciadas por ID desde la Matriz de Competencias)
- El Agente DI debe verificar que el conjunto de objetivos cubre todos los niveles de Bloom requeridos por los Resultados de Aprendizaje de la asignatura
- El JSON debe almacenar la matriz de trazabilidad: `objetivo → nivel Bloom → competencia(s) del programa → RA asociado`
- El QA Gate (RF-06) debe validar que ningún RA queda sin al menos un objetivo de aprendizaje alineado a una competencia del programa
- Si un objetivo no puede mapearse a ninguna competencia del programa, el agente debe marcarlo como gap y escalar para revisión humana antes de continuar

### RF-05 — Agente de Contenido (Content) — Fase 4
- **Fase 4 — Generación de Recursos**: Desarrolla el paquete multimedia a partir de la Carta Descriptiva V1: lecturas ejecutivas, guiones de masterclass, casos de laboratorio agéntico y quizzes
- Genera el paquete en formato JSON/Markdown estructurado
- El contenido es bilingüe (Español / Inglés) según configuración por asignatura
- Para todos los programas de Maestría, genera obligatoriamente los cuatro artefactos definidos en RF-05a
- Enriquece el JSON con el paquete de contenido completo listo para la Fase 5
- Utiliza Amazon Bedrock (Claude Sonnet / Haiku) como LLM

### RF-05a — Estructura de Contenido para Maestría (todos los tipos)
El Agente de Contenido debe generar los siguientes cuatro artefactos por unidad/asignatura para todos los programas de Maestría, publicados como recursos independientes dentro del módulo de Canvas:

1. **Dashboard de Evidencia**: Infografía en formato Markdown/HTML que resume los papers clave (título, autores, año, revista, hallazgo principal) que sustentan la unidad. Generada a partir del corpus Scopus del Agente Scholar.

2. **Mapa de Ruta Crítica**: Visualización del ciclo de trabajo independiente (3 semanas) que muestra la secuencia de actividades, hitos de entrega y criterios de avance. Formato Markdown con tabla de progresión semanal.

3. **Repositorio de Casos Ejecutivos**: Fichas técnicas de casos de estudio diseñados por la IA, vinculados a la realidad profesional del egresado. Cada ficha incluye: contexto del caso, datos relevantes, preguntas de análisis y rúbrica de evaluación alineada a competencias del programa.

4. **Guía del Facilitador**: Documento "minuto a minuto" automatizado para el docente que detalla: objetivos por sesión, secuencia de actividades, tiempos sugeridos, preguntas detonadoras y criterios de evaluación formativa.

Todos los artefactos se generan en el idioma configurado para la asignatura (Español / Inglés / Bilingüe) y se almacenan en el JSON de fuente única de verdad antes de pasar al QA Gate.

### RF-06 — Control de Calidad (QA Gate)
- Antes del checkpoint de validación humana, el sistema valida que los recursos generados cubren el 100% de los RA de la asignatura
- Valida que cada RA tiene al menos un objetivo de aprendizaje con nivel Bloom asignado y mapeado a una competencia del programa (RF-04a)
- Valida que no existen objetivos de aprendizaje sin competencia asociada (gaps de alineación)
- Para Maestría (todos los tipos), valida adicionalmente que los cuatro artefactos de RF-05a están presentes y completos
- Si la cobertura es incompleta: reintenta automáticamente con el agente responsable (máximo 3 intentos)
- Si tras 3 intentos persiste el gap: escala notificando al usuario para revisión manual
- Registra el resultado del QA Gate en el JSON y en DynamoDB, incluyendo la matriz de trazabilidad Bloom–Competencias

### RF-07 — Checkpoint de Validación Humana (Pre-Publicación)
- Antes de publicar en Canvas, el pipeline se detiene y notifica al Staff de Tecnología Educativa para revisión
- La notificación incluye un resumen del contenido generado por asignatura: carta descriptiva, mapa de semanas, los cuatro artefactos de RF-05a y resultado del QA Gate
- El Staff de Tecnología Educativa accede a una vista de previsualización del curso desde la interfaz web
- El Staff de Tecnología Educativa puede: **Aprobar** (dispara la publicación en Canvas), **Rechazar con comentarios** (regresa al agente correspondiente para corrección) o **Editar manualmente** campos específicos antes de aprobar
- El pipeline no avanza a publicación sin aprobación explícita del Staff de Tecnología Educativa
- El estado de aprobación (aprobado / rechazado / pendiente) se registra en el JSON y en DynamoDB con timestamp y usuario responsable
- Si no hay respuesta en un plazo configurable (default: 48 horas), el sistema envía un recordatorio vía CloudWatch alarm + SNS

### RF-08 — Publicación en Canvas LMS — Fase 5
- **Fase 5 — Curaduría y Montaje**: Genera la selección bibliográfica en formato APA a partir del Top 20 de Scopus; exporta el paquete de contenido a plantillas HTML/Markdown estructuradas para Canvas LMS
- Crea la shell del curso en Canvas Cloud (Instructure-hosted) vía API REST
- Publica módulos y carga todos los recursos del paquete de contenido, incluyendo los cuatro artefactos de RF-05a como páginas/archivos independientes dentro del módulo correspondiente
- Configura tareas y quizzes
- Vincula rúbricas de evaluación con las competencias originales del programa
- Actualiza el JSON con el estado de publicación y URLs de Canvas

### RF-09 — Procesamiento Paralelo de Asignaturas
- El pipeline debe procesar múltiples asignaturas en paralelo (hasta 20 simultáneas)
- Cada asignatura es una ejecución independiente con su propio JSON de estado
- El sistema debe gestionar la concurrencia sin degradación de calidad

### RF-10 — Interfaz de Carga para Staff de Tecnología Educativa
- Interfaz web simple (S3 upload + trigger) accesible para Staff de Tecnología Educativa sin conocimientos técnicos de AWS
- Permite cargar documentos de entrada, monitorear el estado del pipeline por asignatura y gestionar el checkpoint de validación humana (RF-07)
- Autenticación mediante credenciales propias (no SSO institucional)

### RF-11 — Notificaciones y Monitoreo
- Dashboard en AWS CloudWatch con métricas clave del pipeline (asignaturas procesadas, errores, tiempo de ejecución, aprobaciones pendientes)
- Alarmas SNS configuradas para fallos del pipeline, escalaciones de QA y recordatorios de validación humana pendiente
- Logs estructurados de cada ejecución accesibles desde CloudWatch

---

## Requerimientos No Funcionales

### RNF-01 — Arquitectura Serverless y Event-Driven
- Toda la orquestación se implementa con Amazon Bedrock Agents y Action Groups (Agent Core nativo)
- No hay servidores persistentes — cada etapa se activa por eventos
- Escalabilidad automática para procesar hasta 20 asignaturas en paralelo

### RNF-02 — Consistencia de Datos
- El JSON de fuente única de verdad es la única fuente de verdad para todo el pipeline
- Cada agente lee y escribe exclusivamente sobre el JSON de su asignatura
- DynamoDB actúa como índice de estado para consultas rápidas de progreso

### RNF-03 — Trazabilidad
- Cada transformación del JSON debe registrar: agente responsable, timestamp, versión del modelo LLM utilizado y hash del resultado
- El historial completo de enriquecimiento del JSON debe ser auditable

### RNF-04 — Idioma del Contenido
- El sistema soporta generación bilingüe (Español / Inglés) configurable por asignatura
- La configuración de idioma se almacena en el JSON de la asignatura

### RNF-05 — Disponibilidad y Resiliencia
- El pipeline debe tolerar fallos parciales (un agente falla sin detener otras asignaturas en paralelo)
- Reintentos automáticos con backoff exponencial para llamadas a APIs externas (Scopus, Canvas)

### RNF-06 — Costo de Infraestructura
- Arquitectura pay-per-use: sin costos fijos de infraestructura cuando no hay ejecuciones activas
- Uso de modelos Bedrock Haiku para tareas de menor complejidad y Sonnet para diseño instruccional

---

## Stack Tecnológico Definido

| Componente | Tecnología |
|---|---|
| Orquestación agéntica | Amazon Bedrock Agents con Action Groups |
| LLM | Amazon Bedrock — Claude Sonnet / Haiku |
| Almacenamiento de estado | Amazon S3 (JSON payload) + Amazon DynamoDB (índice) |
| Investigación académica | Scopus API (Elsevier) — API Key institucional |
| LMS destino | Canvas Cloud (Instructure-hosted) — API REST |
| Interfaz de carga | AWS Amplify / S3 Static Site + API Gateway |
| Monitoreo | AWS CloudWatch + SNS |
| Gestión de secretos | AWS Secrets Manager (API Keys de Scopus y Canvas) |
| Producción visual | Markdown / HTML (sin integración Canva) |

---

## Integraciones Externas

| Sistema | Tipo | Credenciales |
|---|---|---|
| Scopus API (Elsevier) | API REST — búsqueda académica | API Key institucional (AWS Secrets Manager) |
| Canvas LMS Cloud | API REST — gestión de cursos | OAuth2 / API Token (AWS Secrets Manager) |

---

## Restricciones y Supuestos

- La API Key de Scopus es institucional y activa; se debe implementar gestión de rate limiting
- Canvas LMS es la instancia Cloud de Instructure con acceso completo a la API REST
- El Staff de Tecnología Educativa tiene acceso a internet y un navegador moderno
- Los documentos de entrada (PDF, Word, Excel) contienen información estructurada y legible por máquina
- El sistema no gestiona el aprovisionamiento de Canvas — la instancia ya existe
- Los cuatro artefactos de RF-05a aplican a todos los programas de Maestría; para otros niveles educativos el Agente de Contenido genera el paquete estándar

---

## Criterios de Éxito

1. El pipeline procesa una asignatura de extremo a extremo (ingesta → validación humana → Canvas) sin intervención técnica
2. El QA Gate valida cobertura del 100% de RA y presencia de los cuatro artefactos de RF-05a antes de presentar al Staff de Tecnología Educativa
3. El checkpoint de validación humana bloquea efectivamente la publicación hasta recibir aprobación explícita
4. El sistema procesa 6–20 asignaturas en paralelo sin errores de concurrencia
5. El Staff de Tecnología Educativa puede disparar el pipeline, revisar contenido y aprobar publicación sin conocimientos técnicos de AWS
6. Todos los recursos generados en Canvas están vinculados trazablemente al Perfil de Egreso original

---

## Configuración de Extensiones

| Extensión | Estado | Decidido en |
|---|---|---|
| Security Baseline | Habilitada (bloqueante) | Requirements Analysis |
| Property-Based Testing | Habilitada (bloqueante — Full) | Requirements Analysis |
