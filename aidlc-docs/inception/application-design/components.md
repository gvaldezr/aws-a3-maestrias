# Componentes del Sistema
## Pipeline Académico → Canvas LMS

---

## C1 — DocumentIngestionComponent

**Propósito**: Recibir, validar y parsear los documentos de entrada académicos, construyendo el JSON inicial de fuente única de verdad.

**Responsabilidades**:
- Aceptar documentos en formatos PDF, Word (.docx) y Excel (.xlsx) desde S3
- Extraer y estructurar: Perfil de Egreso, Matriz de Competencias, nombre de asignatura, Resultados de Aprendizaje (RA) y temario oficial
- Detectar el tipo de programa (Maestría / otro) y tipo de materia (Fundamentos / Concentración / Proyecto)
- Construir el JSON inicial de la asignatura con estado `INGESTED`
- Registrar el evento de ingesta en DynamoDB
- Disparar el evento que inicia el pipeline agéntico

**Interfaces**:
- Entrada: Objeto S3 (PDF / DOCX / XLSX)
- Salida: JSON de asignatura con estado `INGESTED` → S3 + DynamoDB

---

## C2 — ScholarAgentComponent

**Propósito**: Agente de investigación académica que ejecuta las Fases 1 y 2 del pipeline (Ingesta y Búsqueda + Elicitación Académica).

**Responsabilidades**:
- Generar keywords de búsqueda de alta precisión a partir de RA y competencias
- Ejecutar búsquedas en Scopus API con filtros Q1/Q2 y gestionar rate limiting
- Recuperar y rankear el Top 20 de papers relevantes
- Extraer conceptos, metodologías y casos de éxito (Matriz de Conocimiento Académico Validado)
- Detectar corpus insuficiente y escalar al Staff vía SNS
- Enriquecer el JSON con Top 20 y Matriz de Conocimiento; actualizar estado a `KNOWLEDGE_MATRIX_READY`

**Interfaces**:
- Entrada: JSON de asignatura con estado `INGESTED` (RA + competencias)
- Salida: JSON enriquecido con Top 20 Scopus + Matriz de Conocimiento → estado `KNOWLEDGE_MATRIX_READY`
- Integración externa: Scopus API (Elsevier) vía Action Group

---

## C3 — DIAgentComponent

**Propósito**: Agente de diseño instruccional que ejecuta la Fase 3 del pipeline (Estructuración), generando la Carta Descriptiva V1 con alineación Bloom–Competencias.

**Responsabilidades**:
- Organizar el conocimiento según el tipo de materia (Fundamentos / Concentración / Proyecto)
- Generar el Mapa de Contenidos y Objetivos con verbos Bloom en nivel Analizar/Evaluar
- Redactar la Carta Descriptiva V1 con objetivos mapeados a competencias por ID
- Construir la matriz de trazabilidad: `objetivo → nivel Bloom → competencia(s) → RA`
- Detectar gaps de alineación Bloom–Competencias y escalar al Staff
- Enriquecer el JSON con Mapa de Contenidos y Carta Descriptiva V1; actualizar estado a `DI_READY`

**Interfaces**:
- Entrada: JSON con estado `KNOWLEDGE_MATRIX_READY`
- Salida: JSON enriquecido con Carta Descriptiva V1 + matriz de trazabilidad → estado `DI_READY`

---

## C4 — ContentAgentComponent

**Propósito**: Agente de generación de contenido que ejecuta la Fase 4 del pipeline (Generación de Recursos), produciendo el paquete multimedia completo.

**Responsabilidades**:
- Generar lecturas ejecutivas, guiones de masterclass, quizzes y casos de laboratorio agéntico
- Para programas de Maestría: generar los cuatro artefactos obligatorios (Dashboard de Evidencia, Mapa de Ruta Crítica, Repositorio de Casos Ejecutivos, Guía del Facilitador)
- Generar contenido en el idioma configurado (Español / Inglés / Bilingüe)
- Detectar cobertura incompleta de RA y reintentar (máx. 3 intentos) antes de escalar
- Enriquecer el JSON con el paquete de contenido completo; actualizar estado a `CONTENT_READY`

**Interfaces**:
- Entrada: JSON con estado `DI_READY`
- Salida: JSON enriquecido con paquete multimedia completo → estado `CONTENT_READY`

---

## C5 — QAGateComponent

**Propósito**: Validar que el contenido generado cumple el 100% de los criterios de calidad antes de presentarlo al Staff para aprobación.

**Responsabilidades**:
- Verificar cobertura del 100% de los RA de la asignatura
- Verificar que cada objetivo tiene nivel Bloom asignado y competencia mapeada
- Para Maestría: verificar presencia y completitud de los cuatro artefactos de RF-05a
- Activar reintentos automáticos en el agente responsable (máx. 3 intentos por gap)
- Escalar al Staff vía SNS si persisten gaps tras 3 intentos
- Actualizar el JSON con el reporte de QA y estado `PENDING_APPROVAL` o `QA_FAILED`

**Interfaces**:
- Entrada: JSON con estado `CONTENT_READY`
- Salida: JSON con reporte QA → estado `PENDING_APPROVAL` o `QA_FAILED`

---

## C6 — HumanValidationComponent

**Propósito**: Gestionar el checkpoint de validación humana, bloqueando la publicación hasta recibir aprobación explícita del Staff.

**Responsabilidades**:
- Notificar al Staff vía SNS cuando el contenido está listo para revisión
- Exponer el resumen del contenido y resultado del QA Gate a la interfaz web
- Procesar la decisión del Staff: Aprobar / Rechazar con comentarios / Editar manualmente
- En caso de rechazo: enrutar el feedback al agente responsable para corrección
- Gestionar el timeout de 48 horas con recordatorio automático
- Registrar la decisión en el JSON y DynamoDB con timestamp y usuario; actualizar estado a `APPROVED` o `REJECTED`

**Interfaces**:
- Entrada: JSON con estado `PENDING_APPROVAL` + acción del Staff desde la interfaz web
- Salida: JSON con estado `APPROVED` o `REJECTED` + feedback de corrección

---

## C7 — CanvasPublisherComponent

**Propósito**: Ejecutar la Fase 5 del pipeline (Curaduría y Montaje), publicando el curso aprobado en Canvas LMS.

**Responsabilidades**:
- Generar la bibliografía en formato APA a partir del Top 20 de Scopus
- Exportar el paquete de contenido a plantillas HTML/Markdown para Canvas
- Crear la shell del curso en Canvas Cloud vía API REST
- Publicar módulos, recursos, tareas y quizzes
- Vincular rúbricas a competencias del programa por ID
- Publicar los cuatro artefactos de Maestría como páginas independientes en el módulo
- Gestionar reintentos con backoff exponencial ante fallos de la Canvas API
- Actualizar el JSON con estado `PUBLISHED` y URLs de Canvas

**Interfaces**:
- Entrada: JSON con estado `APPROVED`
- Salida: JSON con estado `PUBLISHED` + URLs de Canvas
- Integración externa: Canvas LMS Cloud API REST vía Action Group

---

## C8 — WebInterfaceComponent

**Propósito**: Interfaz web para el Staff de Tecnología Educativa que permite cargar documentos, monitorear el pipeline y gestionar el checkpoint de validación humana.

**Responsabilidades**:
- Autenticar al Staff con credenciales propias
- Permitir carga de documentos (PDF, DOCX, XLSX) que disparan el pipeline
- Mostrar dashboard de estado en tiempo real por asignatura
- Presentar el checkpoint de validación humana con previsualización del contenido
- Procesar decisiones de aprobación, rechazo con comentarios y edición manual
- Mostrar notificaciones y alertas del sistema

**Interfaces**:
- Entrada: Acciones del Staff (carga, aprobación, rechazo, edición)
- Salida: Eventos hacia S3 (documentos) y API Gateway (decisiones de validación)

---

## C9 — StateManagementComponent

**Propósito**: Gestionar el estado persistente del pipeline por asignatura, sirviendo como fuente de verdad para el progreso y el índice de consulta.

**Responsabilidades**:
- Mantener el JSON de fuente única de verdad en S3 (payload completo, versionado)
- Mantener el índice de estado en DynamoDB (estado actual, timestamps, metadatos)
- Registrar cada transición de estado con: agente responsable, timestamp, versión LLM y hash del resultado
- Proveer el estado actual a la interfaz web y a los agentes

**Interfaces**:
- Entrada: Eventos de actualización de estado desde cualquier componente
- Salida: JSON de asignatura (S3) + registro de estado (DynamoDB)

---

## C10 — ObservabilityComponent

**Propósito**: Centralizar el logging estructurado, métricas, alarmas y notificaciones del sistema.

**Responsabilidades**:
- Recibir y enrutar logs estructurados de todos los componentes a CloudWatch
- Configurar métricas de pipeline (asignaturas procesadas, errores, tiempos, aprobaciones pendientes)
- Gestionar alarmas SNS para fallos, escalaciones de QA y timeouts de validación humana
- Garantizar retención de logs mínima de 90 días
- Prevenir que los agentes puedan eliminar o modificar sus propios logs

**Interfaces**:
- Entrada: Eventos de log y métricas desde todos los componentes
- Salida: CloudWatch Logs + CloudWatch Metrics + SNS notifications
