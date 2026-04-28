---
inclusion: auto
---

# Pipeline Académico → Canvas LMS — Visión General del Proyecto

## Qué es este sistema
Sistema automatizado que transforma documentos de planeación académica (PDF/DOCX/XLSX) en cursos operativos para Canvas LMS, usando agentes de IA orquestados con Amazon Bedrock AgentCore Runtime + Strands SDK.

## Dominio de negocio
- **Cliente**: Universidad Anáhuac — Maestría en Dirección y Tecnología Financiera (MADTFIN)
- **Usuarios**: Staff de Tecnología Educativa que carga documentos y aprueba contenido
- **Flujo**: Documento académico → 3 agentes IA secuenciales → QA automático → Checkpoint humano → Publicación en Canvas LMS
- **Idioma del dominio**: Español (contenido académico, UI, documentación). Código y comentarios técnicos en inglés.

## Pipeline por asignatura (7 fases)
1. **Ingesta** — Staff sube DOCX, parser extrae tablas Anáhuac (nombre, RAs, competencias, syllabus, semanas)
2. **Scholar** (AgentCore, ~3 min) — Keywords → Scopus Q1/Q2 → OpenAlex abstracts → Knowledge Matrix
3. **DI** (AgentCore, ~2 min) — Carta Descriptiva V1 + Bloom–Competencias + Trazabilidad
4. **Content** (AgentCore, ~5 min) — Lecturas, quizzes, foros, masterclass, reto agéntico, 4 artefactos Maestría
5. **QA Gate** — Cobertura 100% RAs, alineación Bloom, artefactos Maestría
6. **Checkpoint Humano** — Staff revisa en frontend (10 tabs), aprueba/rechaza
7. **Canvas Publisher** — Crea curso con módulos semanales + globales en Canvas LMS

## Fuente única de verdad
Cada asignatura tiene un **Subject JSON** en S3 que se enriquece progresivamente por cada agente. DynamoDB sirve como índice de estado para consultas rápidas.

### Estados del pipeline
`INGESTED → KNOWLEDGE_MATRIX_READY → DI_READY → CONTENT_READY → PENDING_APPROVAL → APPROVED → PUBLISHED`

Estados de error: `RESEARCH_ESCALATED`, `DI_ALIGNMENT_GAP`, `QA_FAILED`, `CONTENT_QA_FAILED`, `REJECTED`, `FAILED`

## Stack tecnológico
| Componente | Tecnología |
|-----------|-----------|
| Agentes IA | Amazon Bedrock AgentCore Runtime + Strands SDK |
| Modelo LLM | Claude Sonnet 4.6 (`us.anthropic.claude-sonnet-4-6`) |
| Orquestación | AWS Step Functions |
| Almacenamiento | S3 (JSON versionado, SSE-KMS) + DynamoDB (índice de estado) |
| APIs | API Gateway REST + Cognito JWT |
| Investigación | Scopus API (Elsevier) + OpenAlex (abstracts gratuitos) |
| LMS destino | Canvas LMS (Instructure) REST API |
| Frontend | React 18 + TypeScript + Vite (S3 Static Website) |
| IaC | AWS CDK (Python) |
| Backend | Python 3.11 (Lambda + AgentCore) |
| Secretos | AWS Secrets Manager |
| Observabilidad | CloudWatch Logs (JSON estructurado) + SNS |

## Estructura del monorepo
```
src/
├── infrastructure/          # U1: CDK stacks, JSON schema, state manager, logger
├── agents/
│   ├── scholar/             # U2: Scopus + OpenAlex + Knowledge Matrix
│   ├── di/                  # U3: Carta Descriptiva + Bloom mapper
│   └── content/             # U4: Lecturas, quizzes, foros, masterclass, reto
├── qa_checkpoint/           # U5: QA Gate + Checkpoint humano
├── canvas_publisher/        # U6: Canvas LMS publisher
├── web_interface/           # U7: Frontend React + Backend Lambda
│   ├── backend/
│   └── frontend/
└── orchestrator/            # Step Functions handlers
tests/
├── unit/                    # Tests unitarios por unidad
├── integration/             # Tests de integración
└── e2e_test.py              # Test end-to-end
```

## CDK Stacks (5)
| Stack | Recursos principales |
|-------|---------------------|
| InfrastructureBase | S3, DynamoDB, KMS, SNS, Secrets Manager |
| QACheckpoint | Cognito, QA Gate Lambda, Checkpoint Lambda, API Gateway |
| CanvasPublisher | Canvas Publisher Lambda |
| Orchestrator | Step Functions, 9 Lambda handlers |
| WebInterface | Upload/Ingestion/Dashboard Lambdas, API Gateway, S3 trigger |

## AgentCore Runtimes (3)
| Runtime | Agente | Entrypoint |
|---------|--------|-----------|
| AcademicPipelineScholarDev | Scholar | `src/agents/scholar/agent.py` |
| AcademicPipelineDIDev | DI | `src/agents/di/agent.py` |
| AcademicPipelineContentDev | Content | `src/agents/content/agent.py` |

## Región AWS
`us-east-1` — Cuenta `254508868459`
