# User Stories
## Pipeline Académico → Canvas LMS

**Organización**: Por épica de negocio
**Formato de criterios**: Gherkin (flujos principales) + Checklist (validaciones)
**Actor principal**: Staff de Tecnología Educativa + Agentes de IA (Scholar, DI, Content) + Administrador

---

## ÉPICA 1 — Ingesta de Insumos Académicos

### US-01 — Carga de Documentos de Entrada
**Como** Staff de Tecnología Educativa,
**quiero** cargar los documentos de planeación académica (Perfil de Egreso, Matriz de Competencias, temarios) en múltiples formatos desde la interfaz web,
**para** iniciar automáticamente el pipeline de generación de contenido sin intervención técnica.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Staff accede a la interfaz web autenticado
When carga uno o más documentos en formato PDF, Word (.docx) o Excel (.xlsx)
Then el sistema acepta los archivos y los almacena en S3
And el pipeline se dispara automáticamente para cada asignatura detectada
And el Staff recibe confirmación visual del inicio del proceso con el ID de ejecución
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] El sistema rechaza formatos no soportados con mensaje de error claro
- [ ] El sistema valida que el documento contiene al menos: nombre de asignatura y un RA
- [ ] Cada documento cargado genera un JSON inicial en S3 con estado `INGESTED`
- [ ] El sistema soporta carga simultánea de hasta 20 asignaturas
- [ ] Los archivos se almacenan cifrados en S3 (SSE-S3 o SSE-KMS)

---

### US-02 — Monitoreo del Estado del Pipeline
**Como** Staff de Tecnología Educativa,
**quiero** ver el estado en tiempo real de cada asignatura en proceso desde la interfaz web,
**para** saber en qué fase se encuentra cada una y detectar errores sin necesidad de acceder a AWS.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Staff tiene una o más asignaturas en proceso
When accede al dashboard de la interfaz web
Then ve una lista de asignaturas con su estado actual (INGESTED / RESEARCHING / DESIGNING / GENERATING / QA / PENDING_APPROVAL / PUBLISHING / PUBLISHED / FAILED)
And puede hacer clic en una asignatura para ver el detalle de la fase actual y el log de progreso
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] El estado se actualiza en tiempo real (polling o WebSocket, máx. 30 segundos de latencia)
- [ ] Los errores muestran descripción legible del problema y la fase donde ocurrió
- [ ] El historial de ejecuciones anteriores es accesible por asignatura
- [ ] El dashboard muestra métricas agregadas: total en proceso, completadas, con error

---

## ÉPICA 2 — Investigación Académica (Agente Scholar)

### US-03 — Búsqueda Automatizada en Scopus
**Como** Staff de Tecnología Educativa,
**quiero** que el sistema genere automáticamente el corpus de evidencia científica para cada asignatura consultando Scopus,
**para** garantizar que el contenido del curso esté fundamentado en investigación de vanguardia (Q1/Q2) sin que yo tenga que hacer búsquedas manuales.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que una asignatura tiene RA y competencias extraídos correctamente
When el Agente Scholar inicia la Fase 1
Then genera keywords de búsqueda a partir de los RA y competencias
And ejecuta la búsqueda en Scopus filtrando por Q1/Q2
And recupera el Top 20 de papers más relevantes
And almacena el listado en el JSON de la asignatura con estado `RESEARCHED`
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Las keywords generadas son específicas al dominio de la asignatura (no genéricas)
- [ ] Cada paper incluye: título, autores, año, revista, cuartil y hallazgo principal
- [ ] El sistema gestiona rate limiting de Scopus con backoff exponencial
- [ ] Si Scopus retorna menos de 5 papers relevantes, el agente escala para revisión humana

---

### US-09 — Agente Scholar: Generación de Matriz de Conocimiento
**Como** Agente Scholar,
**quiero** extraer conceptos clave, metodologías y casos de éxito de los papers recuperados,
**para** construir la Matriz de Conocimiento Académico Validado que alimentará al Agente DI.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Top 20 de papers está disponible en el JSON
When el Agente Scholar ejecuta la Fase 2 (Elicitación Académica)
Then extrae conceptos clave, metodologías y casos de éxito con enfoque directivo y tecnológico
And genera la Matriz de Conocimiento Académico Validado
And la almacena en el JSON con estado `KNOWLEDGE_MATRIX_READY`
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] La Matriz incluye al menos: concepto, fuente (paper), aplicación directiva y relevancia para el RA
- [ ] Los conceptos están organizados por afinidad temática
- [ ] La Matriz es legible por el Agente DI como entrada estructurada

---

### US-10 — Agente Scholar: Escalación por Corpus Insuficiente
**Como** Agente Scholar,
**quiero** detectar cuando el corpus recuperado de Scopus no es suficiente en cantidad o calidad,
**para** escalar al Staff de Tecnología Educativa antes de continuar con datos deficientes.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que la búsqueda en Scopus retorna menos de 5 papers Q1/Q2 relevantes
When el Agente Scholar evalúa la calidad del corpus
Then marca el JSON con estado `RESEARCH_ESCALATED`
And notifica al Staff vía SNS con el detalle del gap (keywords usadas, resultados obtenidos)
And detiene el pipeline para esa asignatura hasta recibir instrucción
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] La notificación incluye las keywords utilizadas y el número de resultados obtenidos
- [ ] El Staff puede proporcionar keywords alternativas desde la interfaz web para reintentar
- [ ] El reintento manual no cuenta como uno de los 3 reintentos automáticos del QA Gate

---

## ÉPICA 3 — Diseño Instruccional (Agente DI)

### US-04 — Generación de Carta Descriptiva con Alineación Bloom
**Como** Staff de Tecnología Educativa,
**quiero** que el sistema genere automáticamente la Carta Descriptiva V1 con objetivos de aprendizaje alineados a la Taxonomía de Bloom y mapeados a las competencias del programa,
**para** garantizar que el diseño instruccional sea profesionalizante y trazable al Perfil de Egreso.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que la Matriz de Conocimiento Académico está disponible en el JSON
When el Agente DI ejecuta la Fase 3 (Estructuración)
Then organiza el conocimiento según el tipo de materia (Fundamentos, Concentración o Proyecto)
And genera el Mapa de Contenidos con objetivos en nivel Analizar/Evaluar de Bloom
And redacta la Carta Descriptiva V1 con objetivos mapeados a competencias por ID
And almacena la matriz de trazabilidad objetivo→nivel Bloom→competencia→RA en el JSON
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Cada objetivo usa un verbo de Bloom con nivel cognitivo explícito
- [ ] Cada objetivo referencia al menos una competencia del programa por ID
- [ ] El conjunto de objetivos cubre el 100% de los RA de la asignatura
- [ ] El mapa de 4 semanas (Ingesta → Síntesis) está incluido en la Carta Descriptiva
- [ ] El JSON almacena la matriz de trazabilidad completa

---

### US-11 — Agente DI: Detección de Gaps de Alineación
**Como** Agente DI,
**quiero** detectar cuando un objetivo de aprendizaje no puede mapearse a ninguna competencia del programa,
**para** escalar el gap antes de continuar y evitar publicar contenido no alineado al Perfil de Egreso.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Agente DI ha generado los objetivos de aprendizaje
When evalúa la alineación de cada objetivo con la Matriz de Competencias
And encuentra un objetivo sin competencia asociada
Then marca el JSON con estado `DI_ALIGNMENT_GAP`
And notifica al Staff con el detalle del objetivo sin mapeo
And detiene el pipeline para esa asignatura hasta recibir instrucción
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] La notificación especifica el objetivo problemático y los RA que cubre
- [ ] El Staff puede asignar manualmente una competencia desde la interfaz web
- [ ] El pipeline se reanuda automáticamente tras la asignación manual

---

### US-18 — Agente DI: Estructuración por Tipo de Materia
**Como** Agente DI,
**quiero** organizar el conocimiento de forma diferenciada según el tipo de materia (Fundamentos, Concentración o Proyecto),
**para** que la estructura del curso sea coherente con el nivel y propósito académico de la asignatura.

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] El tipo de materia se detecta automáticamente desde los metadatos de la asignatura en el JSON
- [ ] Fundamentos: énfasis en conceptos y comprensión (Bloom: Recordar/Comprender/Aplicar)
- [ ] Concentración: énfasis en análisis y evaluación (Bloom: Analizar/Evaluar)
- [ ] Proyecto: énfasis en síntesis y creación (Bloom: Evaluar/Crear)
- [ ] Si el tipo de materia no está definido, el agente solicita aclaración al Staff

---

## ÉPICA 4 — Generación de Contenido (Agente Content)

### US-05 — Generación del Paquete Multimedia
**Como** Staff de Tecnología Educativa,
**quiero** que el sistema genere automáticamente el paquete completo de recursos educativos a partir de la Carta Descriptiva V1,
**para** tener todo el material listo para publicar en Canvas sin producción manual de contenido.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que la Carta Descriptiva V1 está disponible en el JSON
When el Agente Content ejecuta la Fase 4 (Generación de Recursos)
Then genera lecturas ejecutivas, guiones de masterclass, quizzes y casos de laboratorio agéntico
And para programas de Maestría genera los cuatro artefactos obligatorios (RF-05a)
And almacena el paquete completo en el JSON con estado `CONTENT_READY`
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] El contenido generado está en el idioma configurado para la asignatura (ES / EN / Bilingüe)
- [ ] Cada recurso está en formato JSON/Markdown estructurado listo para Canvas API
- [ ] Los quizzes incluyen al menos 3 preguntas por RA con respuestas y retroalimentación
- [ ] Los casos de laboratorio agéntico incluyen contexto, datos, preguntas y rúbrica

---

### US-12 — Agente Content: Generación de los Cuatro Artefactos de Maestría
**Como** Agente Content,
**quiero** generar los cuatro artefactos obligatorios para programas de Maestría (Dashboard de Evidencia, Mapa de Ruta Crítica, Repositorio de Casos Ejecutivos, Guía del Facilitador),
**para** que el aula virtual cumpla con la estructura requerida por todos los programas de Maestría.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que la asignatura pertenece a un programa de Maestría
When el Agente Content genera el paquete de contenido
Then produce el Dashboard de Evidencia con los papers clave del corpus Scopus
And produce el Mapa de Ruta Crítica con el ciclo de 3 semanas de trabajo independiente
And produce el Repositorio de Casos Ejecutivos con fichas técnicas y rúbricas
And produce la Guía del Facilitador con el minuto a minuto por sesión
And almacena los cuatro artefactos en el JSON como recursos independientes
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Dashboard de Evidencia: incluye título, autores, año, revista, cuartil y hallazgo de cada paper
- [ ] Mapa de Ruta Crítica: tabla de 3 semanas con actividades, hitos y criterios de avance
- [ ] Repositorio de Casos: cada ficha incluye contexto, datos, preguntas y rúbrica alineada a competencias
- [ ] Guía del Facilitador: incluye objetivos por sesión, tiempos, preguntas detonadoras y criterios formativos
- [ ] Todos los artefactos están en el idioma configurado para la asignatura

---

### US-13 — Agente Content: Generación Bilingüe
**Como** Agente Content,
**quiero** generar el contenido en el idioma configurado para cada asignatura (Español, Inglés o Bilingüe),
**para** que el aula virtual sea accesible en el idioma requerido por el programa.

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] La configuración de idioma se lee del JSON de la asignatura
- [ ] Modo Bilingüe: cada recurso se genera en ambos idiomas como secciones paralelas
- [ ] Los términos técnicos en modo Bilingüe mantienen consistencia terminológica entre idiomas
- [ ] El idioma de los metadatos de Canvas (nombre del módulo, descripción) sigue la misma configuración

---

### US-19 — Agente Content: Escalación por Cobertura Incompleta de RA
**Como** Agente Content,
**quiero** detectar cuando el contenido generado no cubre el 100% de los RA de la asignatura,
**para** reintentar automáticamente antes de escalar al Staff.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Agente Content ha generado el paquete de contenido
When el QA Gate evalúa la cobertura de RA
And detecta que uno o más RA no están cubiertos
Then el agente reintenta la generación del recurso faltante (máx. 3 intentos)
And si tras 3 intentos persiste el gap, marca el JSON con estado `CONTENT_QA_FAILED`
And notifica al Staff con el detalle del RA no cubierto
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Cada reintento usa un prompt diferente para evitar el mismo resultado
- [ ] El log de cada intento se almacena en el JSON para auditoría
- [ ] La notificación al Staff incluye el RA problemático y los 3 intentos fallidos

---

## ÉPICA 5 — Control de Calidad y Validación Humana

### US-06 — QA Gate: Validación de Cobertura Completa
**Como** Staff de Tecnología Educativa,
**quiero** que el sistema valide automáticamente que el contenido generado cubre el 100% de los RA y la alineación Bloom–Competencias antes de presentármelo para revisión,
**para** no tener que revisar manualmente la completitud del contenido.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el paquete de contenido está generado
When el QA Gate ejecuta la validación
Then verifica que cada RA tiene al menos un recurso de contenido asociado
And verifica que cada objetivo tiene nivel Bloom asignado y competencia mapeada
And para Maestría verifica que los cuatro artefactos de RF-05a están presentes
And si todo es válido, avanza al checkpoint de validación humana con estado `PENDING_APPROVAL`
And si hay gaps, activa el mecanismo de reintentos del agente responsable
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] El reporte del QA Gate se almacena en el JSON con detalle por RA
- [ ] El reporte es visible para el Staff en la interfaz web
- [ ] El QA Gate no puede ser omitido — es un paso obligatorio antes del checkpoint humano

---

### US-07 — Checkpoint de Validación Humana: Aprobación de Contenido
**Como** Staff de Tecnología Educativa,
**quiero** revisar el contenido generado y aprobarlo, rechazarlo con comentarios o editarlo antes de que se publique en Canvas,
**para** tener control editorial sobre lo que llega a los docentes y estudiantes.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el QA Gate ha validado el contenido exitosamente
When el Staff accede al checkpoint de validación en la interfaz web
Then ve un resumen del contenido: carta descriptiva, mapa de semanas, artefactos y resultado del QA
And puede previsualizar cada recurso antes de decidir
When el Staff hace clic en "Aprobar"
Then el pipeline continúa automáticamente a la publicación en Canvas
And el JSON registra la aprobación con timestamp y usuario
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] El Staff puede aprobar, rechazar con comentarios o editar campos específicos
- [ ] El rechazo con comentarios regresa el contenido al agente responsable con el feedback
- [ ] La edición manual se registra en el JSON como modificación humana (auditoría)
- [ ] Si no hay respuesta en 48 horas, el sistema envía recordatorio vía SNS
- [ ] El pipeline no avanza sin aprobación explícita

---

### US-08 — Checkpoint de Validación Humana: Rechazo y Corrección
**Como** Staff de Tecnología Educativa,
**quiero** rechazar el contenido generado con comentarios específicos y que el agente correspondiente lo corrija automáticamente,
**para** iterar sobre el contenido sin tener que reiniciar el pipeline completo.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Staff está en el checkpoint de validación
When hace clic en "Rechazar" e ingresa comentarios específicos
Then el pipeline regresa al agente responsable del recurso rechazado
And el agente recibe los comentarios como contexto para la corrección
And genera una versión corregida del recurso
And el Staff recibe notificación para revisar la corrección
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Los comentarios de rechazo son obligatorios (campo no puede estar vacío)
- [ ] El agente identifica automáticamente qué fase debe corregir según el recurso rechazado
- [ ] El ciclo rechazo→corrección puede repetirse hasta 3 veces antes de escalar a soporte técnico
- [ ] Cada ciclo de corrección se registra en el JSON para auditoría

---

## ÉPICA 6 — Publicación en Canvas LMS

### US-08b — Publicación Automática del Curso en Canvas
**Como** Staff de Tecnología Educativa,
**quiero** que el sistema publique automáticamente el curso aprobado en Canvas LMS con todos sus recursos estructurados,
**para** que el aula virtual esté lista para los docentes sin intervención manual en Canvas.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el Staff ha aprobado el contenido en el checkpoint de validación
When el pipeline ejecuta la Fase 5 (Curaduría y Montaje)
Then crea la shell del curso en Canvas vía API REST
And publica los módulos con todos los recursos del paquete de contenido
And configura tareas y quizzes con sus rúbricas
And vincula las rúbricas a las competencias del programa
And actualiza el JSON con estado `PUBLISHED` y las URLs de Canvas
And notifica al Staff con el enlace al curso publicado
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Los cuatro artefactos de Maestría se publican como páginas independientes en el módulo
- [ ] La bibliografía APA se incluye como recurso del módulo
- [ ] Las rúbricas están vinculadas a competencias por ID (trazabilidad completa)
- [ ] El curso se publica en estado "borrador" en Canvas (no visible para estudiantes hasta activación manual)
- [ ] Si la publicación en Canvas falla, el sistema reintenta con backoff exponencial (máx. 3 intentos)

---

## ÉPICA 7 — Seguridad y Gestión de Acceso

### US-14 — Gestión Segura de Credenciales
**Como** Administrador del Sistema,
**quiero** que todas las credenciales (Scopus API Key, Canvas OAuth Token) se gestionen exclusivamente a través de AWS Secrets Manager,
**para** garantizar que nunca estén expuestas en código, logs o variables de entorno.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que el sistema necesita autenticarse con Scopus o Canvas
When un agente o Action Group realiza una llamada a la API externa
Then obtiene las credenciales en tiempo de ejecución desde AWS Secrets Manager
And nunca almacena las credenciales en el JSON, logs o variables de entorno
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] No existen credenciales hardcodeadas en ningún artefacto de código o configuración
- [ ] Los logs de CloudWatch no contienen API Keys, tokens ni valores de secretos
- [ ] La rotación de credenciales en Secrets Manager no requiere redespliegue del sistema
- [ ] Los agentes tienen permisos de IAM de mínimo privilegio para acceder solo a sus secretos

---

### US-15 — Autenticación del Staff en la Interfaz Web
**Como** Administrador del Sistema,
**quiero** que la interfaz web requiera autenticación con credenciales propias antes de permitir cualquier acción,
**para** garantizar que solo el Staff de Tecnología Educativa autorizado pueda disparar el pipeline o aprobar publicaciones.

**Criterios de Aceptación — Flujo Principal (Gherkin)**
```gherkin
Given que un usuario intenta acceder a la interfaz web
When no tiene sesión activa
Then es redirigido a la pantalla de login
And debe autenticarse con usuario y contraseña
And tras autenticación exitosa accede solo a las asignaturas de su programa asignado
```

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Las sesiones expiran tras 8 horas de inactividad
- [ ] Los intentos fallidos de login se registran en CloudWatch con alerta SNS tras 5 intentos
- [ ] Las contraseñas se almacenan con hashing adaptativo (bcrypt o Argon2)
- [ ] MFA habilitado para cuentas con rol de Administrador
- [ ] CORS restringido a los dominios autorizados de la interfaz web

---

### US-16 — Auditoría de Acciones del Sistema
**Como** Administrador del Sistema,
**quiero** que todas las acciones relevantes del pipeline (inicio, aprobaciones, rechazos, publicaciones, errores) queden registradas en logs estructurados con actor, timestamp y detalle,
**para** tener trazabilidad completa de quién hizo qué y cuándo en el sistema.

**Criterios de Aceptación — Validaciones (Checklist)**
- [ ] Cada log incluye: timestamp ISO 8601, actor (usuario o agente), acción, asignatura ID y resultado
- [ ] Los logs se almacenan en CloudWatch con retención mínima de 90 días
- [ ] Los agentes no tienen permisos para eliminar o modificar sus propios logs
- [ ] Las aprobaciones y rechazos del checkpoint humano se registran con el usuario responsable
- [ ] Las modificaciones manuales del Staff en el checkpoint se registran como eventos de auditoría

---

## Resumen de Historias por Épica

| Épica | Historias | Actor principal |
|---|---|---|
| 1. Ingesta de Insumos | US-01, US-02 | Staff de Tecnología Educativa |
| 2. Investigación Académica | US-03, US-09, US-10 | Staff / Agente Scholar |
| 3. Diseño Instruccional | US-04, US-11, US-18 | Staff / Agente DI |
| 4. Generación de Contenido | US-05, US-12, US-13, US-19 | Staff / Agente Content |
| 5. Control de Calidad y Validación | US-06, US-07, US-08 | Staff de Tecnología Educativa |
| 6. Publicación en Canvas | US-08b | Staff de Tecnología Educativa |
| 7. Seguridad y Acceso | US-14, US-15, US-16 | Administrador del Sistema |

**Total: 19 historias** — dentro del rango estándar (15–25) aprobado en el plan.
