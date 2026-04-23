# Servicios del Sistema
## Pipeline Académico → Canvas LMS

---

## S1 — PipelineOrchestrationService

**Propósito**: Orquestar el flujo completo del pipeline por asignatura, coordinando la secuencia de agentes y gestionando transiciones de estado.

**Tecnología**: Amazon Bedrock Agents (Agent Core) con Action Groups

**Responsabilidades**:
- Recibir el evento de ingesta desde S3 y disparar la cadena agéntica
- Coordinar la secuencia: Scholar → DI → Content → QA Gate → Checkpoint Humano → Canvas Publisher
- Gestionar el estado de cada asignatura en DynamoDB
- Enrutar reintentos y escalaciones al componente correcto
- Garantizar que cada agente recibe el JSON enriquecido de la fase anterior

**Interacciones**:
- Consume: DocumentIngestionComponent (evento de inicio)
- Orquesta: ScholarAgentComponent → DIAgentComponent → ContentAgentComponent → QAGateComponent → HumanValidationComponent → CanvasPublisherComponent
- Persiste estado en: StateManagementComponent
- Reporta a: ObservabilityComponent

**Patrón de orquestación**: Event-driven secuencial — cada agente publica su resultado en S3/DynamoDB y dispara el siguiente paso vía evento de Bedrock Agent

---

## S2 — DocumentProcessingService

**Propósito**: Gestionar la ingesta, parsing y extracción de datos académicos desde documentos heterogéneos.

**Tecnología**: AWS Lambda + Amazon Textract (PDF) + python-docx (DOCX) + openpyxl (XLSX)

**Responsabilidades**:
- Detectar el formato del documento y seleccionar el parser adecuado
- Extraer texto estructurado y tablas de PDF, Word y Excel
- Normalizar los datos extraídos al esquema del JSON de fuente única de verdad
- Validar que el documento contiene los campos mínimos requeridos

**Interacciones**:
- Consume: Evento S3 PutObject (documento cargado por el Staff)
- Produce: JSON inicial → StateManagementComponent
- Notifica: ObservabilityComponent (éxito / error de parsing)

---

## S3 — ScopusIntegrationService

**Propósito**: Encapsular toda la comunicación con la API de Scopus, gestionando autenticación, rate limiting y transformación de respuestas.

**Tecnología**: AWS Lambda + Scopus API REST + AWS Secrets Manager (API Key)

**Responsabilidades**:
- Recuperar la API Key de Scopus desde Secrets Manager en tiempo de ejecución
- Construir y ejecutar queries Scopus con filtros de impacto (Q1/Q2)
- Gestionar rate limiting con backoff exponencial
- Transformar la respuesta de Scopus al modelo interno `Paper`
- Cachear resultados en S3 para evitar re-consultas innecesarias

**Interacciones**:
- Invocado por: ScholarAgentComponent (Action Group)
- Consume: Scopus API externa
- Recupera credenciales de: AWS Secrets Manager

---

## S4 — CanvasIntegrationService

**Propósito**: Encapsular toda la comunicación con la Canvas LMS API REST, gestionando autenticación OAuth2, paginación y transformación de payloads.

**Tecnología**: AWS Lambda + Canvas API REST + AWS Secrets Manager (OAuth Token)

**Responsabilidades**:
- Recuperar el OAuth Token de Canvas desde Secrets Manager en tiempo de ejecución
- Crear cursos, módulos, páginas, tareas, quizzes y rúbricas vía Canvas API
- Gestionar reintentos con backoff exponencial ante fallos de la API
- Transformar el paquete de contenido interno al formato esperado por Canvas API
- Publicar los cuatro artefactos de Maestría como páginas Canvas independientes

**Interacciones**:
- Invocado por: CanvasPublisherComponent (Action Group)
- Consume: Canvas LMS Cloud API externa
- Recupera credenciales de: AWS Secrets Manager

---

## S5 — NotificationService

**Propósito**: Centralizar el envío de notificaciones al Staff y al Administrador para eventos críticos del pipeline.

**Tecnología**: Amazon SNS + AWS Lambda

**Responsabilidades**:
- Notificar al Staff cuando el contenido está listo para revisión (checkpoint humano)
- Enviar recordatorios de validación pendiente tras 48 horas sin respuesta
- Alertar sobre fallos del pipeline, escalaciones de QA y gaps de alineación
- Enviar alertas de seguridad (intentos de login fallidos, accesos no autorizados)

**Interacciones**:
- Invocado por: QAGateComponent, HumanValidationComponent, ObservabilityComponent, ScholarAgentComponent, DIAgentComponent
- Produce: Mensajes SNS → email / webhook configurado

---

## S6 — AuthenticationService

**Propósito**: Gestionar la autenticación y autorización del Staff de Tecnología Educativa en la interfaz web.

**Tecnología**: Amazon Cognito User Pools + API Gateway Authorizer

**Responsabilidades**:
- Autenticar al Staff con usuario y contraseña
- Gestionar sesiones con expiración de 8 horas
- Aplicar bloqueo progresivo tras 5 intentos fallidos de login
- Proveer tokens JWT para autorización en API Gateway
- Gestionar MFA para cuentas de Administrador

**Interacciones**:
- Invocado por: WebInterfaceComponent
- Protege: API Gateway (todos los endpoints del pipeline)
- Registra eventos de seguridad en: ObservabilityComponent

---

## S7 — SecretsManagementService

**Propósito**: Proveer acceso seguro a credenciales y secretos del sistema en tiempo de ejecución.

**Tecnología**: AWS Secrets Manager

**Responsabilidades**:
- Almacenar y rotar: Scopus API Key, Canvas OAuth Token, credenciales de base de datos
- Proveer acceso a secretos solo a los componentes con permisos IAM explícitos
- Garantizar que ningún secreto aparezca en logs, variables de entorno o código

**Interacciones**:
- Invocado por: ScopusIntegrationService, CanvasIntegrationService, AuthenticationService
- Acceso controlado por: IAM least-privilege policies por componente
