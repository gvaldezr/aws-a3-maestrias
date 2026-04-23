# Dependencias y Flujo de Datos
## Pipeline Académico → Canvas LMS

---

## Matriz de Dependencias

| Componente | Depende de | Es consumido por |
|---|---|---|
| C1 DocumentIngestion | S3, C9 StateManagement, C10 Observability | S1 PipelineOrchestration |
| C2 ScholarAgent | C9 StateManagement, S3 ScopusIntegration, C10 Observability | S1 PipelineOrchestration |
| C3 DIAgent | C9 StateManagement, C10 Observability | S1 PipelineOrchestration |
| C4 ContentAgent | C9 StateManagement, C10 Observability | S1 PipelineOrchestration |
| C5 QAGate | C9 StateManagement, C10 Observability, S5 Notification | S1 PipelineOrchestration |
| C6 HumanValidation | C9 StateManagement, S5 Notification, C8 WebInterface | S1 PipelineOrchestration |
| C7 CanvasPublisher | C9 StateManagement, S4 CanvasIntegration, C10 Observability | S1 PipelineOrchestration |
| C8 WebInterface | S6 Authentication, API Gateway, C9 StateManagement | Staff de Tecnología Educativa |
| C9 StateManagement | S3 (bucket), DynamoDB | Todos los componentes |
| C10 Observability | CloudWatch, SNS | Todos los componentes |
| S1 PipelineOrchestration | C1–C7, C9, C10 | Evento S3 (trigger) |
| S2 DocumentProcessing | S3, Amazon Textract, C9 | C1 DocumentIngestion |
| S3 ScopusIntegration | Scopus API, Secrets Manager | C2 ScholarAgent |
| S4 CanvasIntegration | Canvas API, Secrets Manager | C7 CanvasPublisher |
| S5 Notification | SNS | C5, C6, C10 |
| S6 Authentication | Cognito, API Gateway | C8 WebInterface |
| S7 SecretsManagement | Secrets Manager | S3, S4, S6 |

---

## Flujo de Datos del Pipeline (por asignatura)

```
Staff carga documentos
        |
        v
[S3 PutObject Event]
        |
        v
[C1 DocumentIngestion + S2 DocumentProcessing]
  - Parsea PDF/DOCX/XLSX
  - Extrae datos académicos
  - Construye JSON inicial
  - Estado: INGESTED
        |
        v
[S1 PipelineOrchestration dispara C2]
        |
        v
[C2 ScholarAgent + S3 ScopusIntegration]
  - Genera keywords
  - Busca en Scopus (Top 20 Q1/Q2)
  - Construye Matriz de Conocimiento
  - Estado: KNOWLEDGE_MATRIX_READY
  - [Si corpus insuficiente] --> S5 Notification --> Staff
        |
        v
[C3 DIAgent]
  - Estructura por tipo de materia
  - Genera Mapa de Contenidos + Objetivos Bloom
  - Redacta Carta Descriptiva V1
  - Construye matriz trazabilidad
  - Estado: DI_READY
  - [Si gap Bloom-Competencias] --> S5 Notification --> Staff
        |
        v
[C4 ContentAgent]
  - Genera paquete multimedia
  - Genera 4 artefactos Maestría (si aplica)
  - Estado: CONTENT_READY
  - [Si cobertura RA incompleta] --> reintento (max 3) --> S5 Notification
        |
        v
[C5 QAGate]
  - Valida cobertura 100% RA
  - Valida alineación Bloom-Competencias
  - Valida 4 artefactos Maestría (si aplica)
  - Estado: PENDING_APPROVAL o QA_FAILED
        |
        v
[C6 HumanValidation]
  - Notifica Staff via SNS
  - Staff revisa en C8 WebInterface
  - Staff: Aprobar / Rechazar / Editar
  - [Timeout 48h] --> recordatorio SNS
  - Estado: APPROVED o REJECTED
  - [Si REJECTED] --> feedback --> C3/C4 para corrección
        |
        v (solo si APPROVED)
[C7 CanvasPublisher + S4 CanvasIntegration]
  - Genera bibliografía APA
  - Exporta a plantillas HTML/Markdown
  - Crea curso en Canvas
  - Publica módulos, recursos, tareas, quizzes
  - Vincula rúbricas a competencias
  - Estado: PUBLISHED
        |
        v
[C10 Observability]
  - Notifica Staff: curso publicado + URL Canvas
```

---

## Patrones de Comunicación

| Patrón | Componentes | Descripción |
|---|---|---|
| Event-driven (S3) | C1 → S1 | Documento cargado dispara el pipeline |
| Agente → Action Group | C2 → S3 ScopusIntegration | Bedrock Agent invoca Lambda via Action Group |
| Agente → Action Group | C7 → S4 CanvasIntegration | Bedrock Agent invoca Lambda via Action Group |
| State polling | C8 → C9 | Interfaz web consulta DynamoDB para dashboard |
| Async notification | C5, C6 → S5 → Staff | SNS para notificaciones asíncronas |
| Sync REST | C8 → API Gateway → C6 | Staff envía decisión de validación |
| Shared state | Todos → C9 | JSON en S3 + índice en DynamoDB como fuente única de verdad |

---

## Flujo de Seguridad

```
Staff accede a interfaz web
        |
        v
[S6 AuthenticationService - Cognito]
  - Valida credenciales
  - Emite JWT con expiración 8h
  - MFA para Administrador
        |
        v
[API Gateway - JWT Authorizer]
  - Valida JWT en cada request
  - Rechaza requests sin token válido
        |
        v
[Componentes del pipeline]
  - Credenciales externas desde S7 SecretsManagement
  - Logs sin secretos ni PII en C10 Observability
  - IAM least-privilege por componente
```
