# Diseño de Aplicación — Consolidado
## Pipeline Académico → Canvas LMS con Agent Core Framework

---

## Resumen Arquitectónico

Sistema serverless multi-agente orquestado con Amazon Bedrock Agents. El pipeline transforma documentos de planeación académica en cursos operativos en Canvas LMS a través de 5 fases secuenciales ejecutadas por 3 agentes especializados, con un QA Gate automatizado y un checkpoint de validación humana antes de la publicación.

**Patrón arquitectónico**: Event-driven + Agéntico (Agent Core)
**Modelo de datos**: JSON de fuente única de verdad enriquecido progresivamente (S3 + DynamoDB)
**Escala**: 6–20 asignaturas en paralelo por ejecución

---

## Componentes (resumen)

| ID | Componente | Fase del Pipeline | Tecnología base |
|---|---|---|---|
| C1 | DocumentIngestionComponent | Ingesta | Lambda + Textract |
| C2 | ScholarAgentComponent | Fases 1–2 (Investigación) | Bedrock Agent + Scopus Action Group |
| C3 | DIAgentComponent | Fase 3 (Estructuración) | Bedrock Agent (Claude Sonnet) |
| C4 | ContentAgentComponent | Fase 4 (Generación) | Bedrock Agent (Claude Sonnet/Haiku) |
| C5 | QAGateComponent | QA Gate | Lambda |
| C6 | HumanValidationComponent | Checkpoint Humano | Lambda + SNS |
| C7 | CanvasPublisherComponent | Fase 5 (Montaje) | Bedrock Agent + Canvas Action Group |
| C8 | WebInterfaceComponent | Interfaz Staff | Amplify / S3 Static + API Gateway |
| C9 | StateManagementComponent | Transversal | S3 + DynamoDB |
| C10 | ObservabilityComponent | Transversal | CloudWatch + SNS |

**Ver detalle completo**: `components.md`

---

## Servicios (resumen)

| ID | Servicio | Propósito | Tecnología |
|---|---|---|---|
| S1 | PipelineOrchestrationService | Orquesta el flujo agéntico completo | Bedrock Agents |
| S2 | DocumentProcessingService | Parsea PDF/DOCX/XLSX | Lambda + Textract |
| S3 | ScopusIntegrationService | Integración con Scopus API | Lambda + Secrets Manager |
| S4 | CanvasIntegrationService | Integración con Canvas API | Lambda + Secrets Manager |
| S5 | NotificationService | Notificaciones al Staff | SNS + Lambda |
| S6 | AuthenticationService | Autenticación del Staff | Cognito + API Gateway |
| S7 | SecretsManagementService | Gestión de credenciales | Secrets Manager |

**Ver detalle completo**: `services.md`

---

## Flujo del Pipeline (resumen)

```
Documentos (PDF/DOCX/XLSX)
    --> C1 DocumentIngestion  [JSON: INGESTED]
    --> C2 ScholarAgent       [JSON: KNOWLEDGE_MATRIX_READY]
    --> C3 DIAgent            [JSON: DI_READY]
    --> C4 ContentAgent       [JSON: CONTENT_READY]
    --> C5 QAGate             [JSON: PENDING_APPROVAL | QA_FAILED]
    --> C6 HumanValidation    [JSON: APPROVED | REJECTED]
    --> C7 CanvasPublisher    [JSON: PUBLISHED]
```

**Ver flujo completo con ramificaciones**: `component-dependency.md`

---

## Métodos Clave por Componente (resumen)

| Componente | Métodos principales |
|---|---|
| C1 | ingest_document, extract_academic_data, build_initial_json |
| C2 | generate_search_keywords, search_scopus, extract_knowledge_matrix |
| C3 | generate_learning_objectives, build_traceability_matrix, draft_descriptive_card |
| C4 | generate_executive_readings, generate_quizzes, generate_evidence_dashboard |
| C5 | run_full_qa, trigger_retry, escalate_qa_failure |
| C6 | process_approval, process_rejection, check_approval_timeout |
| C7 | generate_apa_bibliography, create_course_shell, publish_maestria_artifacts |
| C8 | authenticate_staff, upload_documents, submit_validation_decision |
| C9 | save_subject_json, update_subject_state, get_subject_json |
| C10 | log_event, record_metric, send_notification |

**Ver firmas completas**: `component-methods.md`

---

## Consideraciones de Seguridad (SECURITY-01 a SECURITY-15)

- Todas las credenciales externas gestionadas exclusivamente por S7 SecretsManagementService (SECURITY-12)
- Cifrado en reposo en S3 y DynamoDB; TLS 1.2+ en tránsito (SECURITY-01)
- IAM least-privilege por componente — ningún agente tiene permisos más allá de lo necesario (SECURITY-06)
- Logs estructurados sin secretos ni PII en C10 (SECURITY-03)
- Autenticación con Cognito + JWT + MFA para Administrador (SECURITY-12)
- Rate limiting en API Gateway para endpoints públicos (SECURITY-11)
- Retención de logs mínima 90 días; agentes sin permisos de borrado de logs (SECURITY-14)

---

## Unidades de Trabajo para Construcción

Las 7 unidades definidas en el plan de ejecución mapean directamente a los componentes:

| Unidad | Componentes incluidos |
|---|---|
| U1 — Infraestructura Base + JSON Schema | C9, C10, S7 |
| U2 — Agente Scholar | C2, S3 |
| U3 — Agente DI | C3 |
| U4 — Agente Content | C4 |
| U5 — QA Gate + Checkpoint Humano | C5, C6, S5 |
| U6 — Publicación Canvas | C7, S4 |
| U7 — Interfaz Web | C1, C8, S2, S6 |
