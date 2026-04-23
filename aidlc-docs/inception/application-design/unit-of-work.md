# Unidades de Trabajo
## Pipeline Académico → Canvas LMS

**Modelo de despliegue**: Serverless — cada unidad es desplegable de forma independiente
**Organización de código**: Monorepo con estructura `src/{unit-name}/`
**Total de unidades**: 7

---

## U1 — Infraestructura Base + JSON Schema

**Descripción**: Fundación del sistema. Define el esquema del JSON de fuente única de verdad, provisiona los recursos de almacenamiento y estado, y establece las políticas IAM base que todas las demás unidades heredan.

**Componentes incluidos**: C9 StateManagementComponent, C10 ObservabilityComponent, S7 SecretsManagementService

**Responsabilidades**:
- Definir y versionar el esquema JSON completo de la asignatura (todos los campos de las 5 fases)
- Provisionar bucket S3 con versionado y cifrado (SSE-KMS)
- Provisionar tabla DynamoDB con índices para consultas por estado y por programa
- Configurar AWS Secrets Manager con los secretos del sistema (Scopus API Key, Canvas Token)
- Configurar CloudWatch Log Groups con retención de 90 días
- Configurar alarmas SNS base (fallos de pipeline, escalaciones)
- Definir roles IAM base con least-privilege para cada unidad

**Directorio de código**: `src/infrastructure/`
**IaC**: AWS CDK (Python)
**Dependencias**: Ninguna — es la unidad fundacional

---

## U2 — Agente Scholar

**Descripción**: Implementa las Fases 1 y 2 del pipeline (Ingesta y Búsqueda + Elicitación Académica). Agente de investigación académica que transforma RA y competencias en corpus científico validado.

**Componentes incluidos**: C2 ScholarAgentComponent, S3 ScopusIntegrationService

**Responsabilidades**:
- Implementar el Bedrock Agent "Scholar" con su system prompt y configuración
- Implementar el Action Group de Scopus (Lambda que invoca Scopus API)
- Lógica de generación de keywords, búsqueda Q1/Q2, ranking Top 20
- Construcción de la Matriz de Conocimiento Académico Validado
- Gestión de rate limiting de Scopus con backoff exponencial
- Detección de corpus insuficiente y escalación vía SNS
- Enriquecimiento del JSON con Top 20 + Matriz de Conocimiento

**Directorio de código**: `src/agents/scholar/`
**Tecnología**: Amazon Bedrock Agent + Lambda (Python) + Scopus API
**Dependencias**: U1 (JSON schema, S3, DynamoDB, Secrets Manager, SNS)

---

## U3 — Agente DI

**Descripción**: Implementa la Fase 3 del pipeline (Estructuración). Agente de diseño instruccional que genera la Carta Descriptiva V1 con alineación Bloom–Competencias.

**Componentes incluidos**: C3 DIAgentComponent

**Responsabilidades**:
- Implementar el Bedrock Agent "DI" con su system prompt y configuración
- Lógica de estructuración por tipo de materia (Fundamentos / Concentración / Proyecto)
- Generación del Mapa de Contenidos con verbos Bloom en nivel Analizar/Evaluar
- Redacción de la Carta Descriptiva V1 con mapa de 4 semanas
- Construcción de la matriz de trazabilidad objetivo→Bloom→competencia→RA
- Detección de gaps de alineación y escalación vía SNS
- Enriquecimiento del JSON con Carta Descriptiva V1 y matriz de trazabilidad

**Directorio de código**: `src/agents/di/`
**Tecnología**: Amazon Bedrock Agent (Claude Sonnet)
**Dependencias**: U1, U2 (JSON con Matriz de Conocimiento)

---

## U4 — Agente Content

**Descripción**: Implementa la Fase 4 del pipeline (Generación de Recursos). Agente de contenido que produce el paquete multimedia completo incluyendo los cuatro artefactos obligatorios para Maestría.

**Componentes incluidos**: C4 ContentAgentComponent

**Responsabilidades**:
- Implementar el Bedrock Agent "Content" con su system prompt y configuración
- Generación de lecturas ejecutivas, guiones de masterclass, quizzes y casos de laboratorio
- Generación de los cuatro artefactos de Maestría: Dashboard de Evidencia, Mapa de Ruta Crítica, Repositorio de Casos Ejecutivos, Guía del Facilitador
- Soporte bilingüe (Español / Inglés / Bilingüe) por configuración de asignatura
- Detección de cobertura incompleta de RA con reintentos automáticos (máx. 3)
- Enriquecimiento del JSON con el paquete de contenido completo

**Directorio de código**: `src/agents/content/`
**Tecnología**: Amazon Bedrock Agent (Claude Sonnet / Haiku)
**Dependencias**: U1, U3 (JSON con Carta Descriptiva V1)

---

## U5 — QA Gate + Checkpoint Humano

**Descripción**: Implementa el control de calidad automatizado y el flujo de validación humana antes de la publicación en Canvas.

**Componentes incluidos**: C5 QAGateComponent, C6 HumanValidationComponent, S5 NotificationService

**Responsabilidades**:
- Validación de cobertura del 100% de RA
- Validación de alineación Bloom–Competencias (sin objetivos sin competencia)
- Validación de presencia de los cuatro artefactos de Maestría (si aplica)
- Reintentos automáticos en el agente responsable (máx. 3 por gap)
- Notificación al Staff cuando el contenido está listo para revisión
- Procesamiento de decisiones: Aprobar / Rechazar con comentarios / Editar manualmente
- Gestión del timeout de 48 horas con recordatorio SNS
- Enrutamiento de feedback de rechazo al agente responsable
- Registro de decisiones en JSON y DynamoDB con auditoría completa

**Directorio de código**: `src/qa-checkpoint/`
**Tecnología**: Lambda (Python) + SNS + DynamoDB
**Dependencias**: U1, U4 (JSON con paquete de contenido)

---

## U6 — Publicación Canvas LMS

**Descripción**: Implementa la Fase 5 del pipeline (Curaduría y Montaje). Publica el curso aprobado en Canvas LMS con todos sus recursos estructurados.

**Componentes incluidos**: C7 CanvasPublisherComponent, S4 CanvasIntegrationService

**Responsabilidades**:
- Generación de bibliografía APA a partir del Top 20 de Scopus
- Exportación del paquete de contenido a plantillas HTML/Markdown para Canvas
- Creación de la shell del curso en Canvas Cloud vía API REST
- Publicación de módulos, recursos, tareas y quizzes
- Vinculación de rúbricas a competencias del programa por ID
- Publicación de los cuatro artefactos de Maestría como páginas independientes
- Gestión de reintentos con backoff exponencial ante fallos de Canvas API
- Actualización del JSON con estado PUBLISHED y URLs de Canvas

**Directorio de código**: `src/canvas-publisher/`
**Tecnología**: Lambda (Python) + Canvas API REST + Secrets Manager
**Dependencias**: U1, U5 (JSON con estado APPROVED)

---

## U7 — Interfaz Web

**Descripción**: Interfaz web para el Staff de Tecnología Educativa. Permite cargar documentos, monitorear el pipeline y gestionar el checkpoint de validación humana.

**Componentes incluidos**: C1 DocumentIngestionComponent, C8 WebInterfaceComponent, S2 DocumentProcessingService, S6 AuthenticationService

**Responsabilidades**:
- Frontend web (React / Next.js) desplegado en AWS Amplify
- Autenticación con Amazon Cognito (usuario/contraseña + MFA para Admin)
- Carga de documentos (PDF/DOCX/XLSX) a S3 con disparo automático del pipeline
- Dashboard de estado en tiempo real por asignatura (polling DynamoDB)
- Vista de checkpoint de validación humana con previsualización de contenido
- Procesamiento de decisiones de aprobación, rechazo y edición manual
- Parsing de documentos de entrada (Lambda + Textract + python-docx + openpyxl)
- API Gateway como backend para todas las operaciones del Staff

**Directorio de código**: `src/web-interface/` (frontend) + `src/document-ingestion/` (backend)
**Tecnología**: React/Next.js + AWS Amplify + API Gateway + Lambda + Cognito + Textract
**Dependencias**: U1, U5 (checkpoint), U6 (URLs de Canvas para confirmación)

---

## Estructura de Código del Monorepo

```
/                                   <- Workspace root
├── src/
│   ├── infrastructure/             <- U1: CDK stacks, JSON schema
│   ├── agents/
│   │   ├── scholar/                <- U2: Bedrock Agent Scholar
│   │   ├── di/                     <- U3: Bedrock Agent DI
│   │   └── content/                <- U4: Bedrock Agent Content
│   ├── qa-checkpoint/              <- U5: QA Gate + Human Validation
│   ├── canvas-publisher/           <- U6: Canvas LMS publisher
│   └── web-interface/              <- U7: Frontend + Document Ingestion
├── tests/
│   ├── unit/                       <- Tests unitarios por unidad
│   ├── integration/                <- Tests de integración entre unidades
│   └── contract/                   <- Tests de contrato (Scopus API, Canvas API)
├── aidlc-docs/                     <- Documentación AI-DLC (NO código)
└── README.md
```
