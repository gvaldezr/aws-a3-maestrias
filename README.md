# Pipeline Académico → Canvas LMS

Sistema automatizado que transforma documentos de planeación académica (PDF/DOCX/XLSX) en cursos operativos para Canvas LMS, usando agentes de IA orquestados con Amazon Bedrock AgentCore Runtime + Strands SDK.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (S3 Static)                         │
│  Login (Cognito) → Upload DOCX → Dashboard → Revisar → Aprobar     │
└──────────┬──────────────────────────────────┬───────────────────────┘
           │ API Gateway (Web)                │ API Gateway (Checkpoint)
           ▼                                  ▼
┌──────────────────┐              ┌─────────────────────┐
│  Upload Handler  │              │ Checkpoint Handler   │
│  Ingestion       │              │ GET  /checkpoint     │
│  Dashboard       │              │ POST /decision       │
└────────┬─────────┘              └──────────┬──────────┘
         │ S3 Event                          │ Approve → Canvas Publisher
         ▼                                   ▼
┌──────────────────────────────────────────────────────┐
│              Step Functions Orchestrator              │
│  WarmUp → Scholar → DI → Content → QA Gate → STOP   │
└────┬──────────┬──────────┬──────────┬────────────────┘
     ▼          ▼          ▼          ▼
┌─────────┐ ┌──────┐ ┌─────────┐ ┌────────┐
│ Scholar │ │  DI  │ │ Content │ │QA Gate │
│AgentCore│ │Agent │ │ Agent   │ │Lambda  │
│ Runtime │ │Core  │ │  Core   │ │        │
└────┬────┘ └──┬───┘ └────┬────┘ └────┬───┘
     │         │          │           │
     ▼         ▼          ▼           ▼
┌──────────────────────────────────────────┐
│     S3 (Subject JSON) + DynamoDB         │
│     Fuente única de verdad por asignatura│
└──────────────────────────────────────────┘
```

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Agentes IA | Amazon Bedrock AgentCore Runtime + Strands SDK |
| Modelo LLM | Claude Sonnet 4.6 (us.anthropic.claude-sonnet-4-6) |
| Orquestación | AWS Step Functions |
| Almacenamiento | Amazon S3 (JSON versionado) + DynamoDB (índice de estado) |
| APIs | Amazon API Gateway (REST) con Cognito JWT |
| Autenticación | Amazon Cognito User Pool |
| Investigación | Scopus API (Elsevier) |
| LMS destino | Canvas LMS (Instructure) — mock mode disponible |
| Frontend | React + TypeScript + Vite (S3 Static Website) |
| IaC | AWS CDK (Python) |
| Secretos | AWS Secrets Manager |

## Estructura del Proyecto

```
aws-a3-maestrias/
├── app.py                          # CDK App entry point
├── cdk.json                        # CDK configuration
├── .bedrock_agentcore.yaml         # AgentCore Runtime config (3 agents)
│
├── src/
│   ├── agents/
│   │   ├── scholar/agent.py        # Agente Investigador (Scopus + Knowledge Matrix)
│   │   ├── di/agent.py             # Agente Diseño Instruccional (Bloom + Carta Descriptiva)
│   │   └── content/agent.py        # Agente Contenido (Lecturas + Quizzes + Maestría)
│   │
│   ├── orchestrator/
│   │   ├── invoke_agent.py         # Step Functions Lambda handlers
│   │   └── persist_results.py      # Persistencia de resultados entre fases
│   │
│   ├── qa_checkpoint/
│   │   ├── qa_gate.py              # Validación QA (RA coverage, Bloom, Maestría)
│   │   ├── checkpoint.py           # Checkpoint humano (aprobar/rechazar/editar)
│   │   ├── models.py               # QAReport, ValidationDecision, etc.
│   │   └── timeout_checker.py      # Monitor de timeout 48h
│   │
│   ├── canvas_publisher/
│   │   ├── publisher.py            # Publicación en Canvas LMS
│   │   ├── canvas_client.py        # Cliente REST para Canvas API
│   │   ├── mock_client.py          # Mock para testing sin Canvas real
│   │   ├── formatters.py           # Markdown→HTML, payloads de Canvas API
│   │   └── models.py               # PublicationResult, CanvasCourse, etc.
│   │
│   ├── web_interface/
│   │   ├── backend/
│   │   │   ├── upload_handler.py   # Presigned URL para S3
│   │   │   ├── ingestion_handler.py # Parse DOCX/PDF → Subject JSON → Step Functions
│   │   │   ├── dashboard_handler.py # GET /api/subjects
│   │   │   └── document_parser.py  # Extracción de datos académicos de DOCX
│   │   └── frontend/
│   │       ├── src/App.tsx          # Login + Dashboard + Upload
│   │       ├── src/pages/CheckpointPage.tsx  # Revisión con 6 tabs
│   │       ├── src/components/SubjectTable.tsx # Tabla de estado
│   │       └── src/api/pipeline.ts  # API client
│   │
│   └── infrastructure/
│       ├── stacks/                  # CDK Stacks (5)
│       ├── state/                   # State manager (S3 + DynamoDB)
│       ├── schema/                  # JSON schema validator
│       └── observability/           # Logger + Metrics
│
├── tests/                           # 191 unit tests
├── lambda-layer/                    # Shared Lambda Layer
├── test-data/                       # Scripts de prueba y deploy
└── aidlc-docs/                      # Documentación AI-DLC
```

## Pipeline por Asignatura

Cada asignatura pasa por 7 fases secuenciales:

### Fase 1: Ingesta
- Staff sube DOCX/PDF desde el frontend
- `ingestion_handler` parsea tablas del DOCX (formato Anáhuac)
- Extrae: nombre, RAs, competencias, syllabus, tipo de materia
- Crea Subject JSON en S3 y dispara Step Functions

### Fase 2: Scholar (AgentCore Runtime)
- Genera keywords específicos del dominio a partir del syllabus
- Busca en Scopus API papers Q1/Q2 (Top 20)
- Construye Knowledge Matrix vinculando papers a RAs
- Auto-persiste resultados a S3 + DynamoDB

### Fase 3: DI — Diseño Instruccional (AgentCore Runtime)
- Carga contexto completo de S3 (syllabus, competencias, papers)
- Genera objetivos de aprendizaje con Taxonomía de Bloom
- Alinea objetivos → competencias del programa (C1-C4) → RAs
- Genera Carta Descriptiva V1 y Mapa de Contenidos semanal
- Auto-persiste resultados

### Fase 4: Content — Generación de Recursos (AgentCore Runtime)
- Carga todo el contexto previo (syllabus, objetivos, papers, mapa semanal)
- Genera lecturas ejecutivas por semana
- Genera quizzes con preguntas específicas del dominio
- Genera 4 artefactos Maestría (RF-05a):
  1. Dashboard de Evidencia (20 papers)
  2. Mapa de Ruta Crítica
  3. Repositorio de Casos Ejecutivos
  4. Guía del Facilitador (minuto a minuto)
- Auto-persiste resultados

### Fase 5: QA Gate
- Valida cobertura 100% de RAs
- Valida alineación Bloom–Competencias (sin gaps)
- Valida presencia de 4 artefactos Maestría
- Si PASS → estado PENDING_APPROVAL
- Si FAIL → reintento automático (máx 3)

### Fase 6: Checkpoint Humano (RF-07)
- Pipeline se pausa — Staff recibe notificación
- Frontend muestra 6 tabs de previsualización:
  - Resumen QA, Objetivos, Lecturas, Quizzes, Papers, Maestría
- Staff puede: Aprobar / Rechazar con comentarios / Editar
- Sin aprobación explícita, no se publica

### Fase 7: Canvas Publisher (RF-08)
- Crea curso en Canvas LMS (borrador)
- Publica módulos, páginas, quizzes, rúbricas
- Vincula competencias a rúbricas de evaluación
- Modo mock disponible (`CANVAS_MOCK_MODE=true`)

## Despliegue

### Prerrequisitos
- AWS CLI configurado (cuenta 254508868459, us-east-1)
- Node.js 18+ (para CDK)
- Python 3.11
- AgentCore CLI (`pip install bedrock-agentcore-starter-toolkit`)

### CloudFormation Stacks (5)
```bash
npx cdk deploy --all --require-approval never
```

| Stack | Recursos |
|-------|----------|
| Infrastructure | S3, DynamoDB, KMS, SNS, Secrets Manager |
| QACheckpoint | Cognito, QA Gate Lambda, Checkpoint Lambda, API Gateway |
| CanvasPublisher | Canvas Publisher Lambda |
| Orchestrator | Step Functions, 9 Lambda handlers |
| WebInterface | Upload/Ingestion/Dashboard Lambdas, API Gateway, S3 trigger |

### AgentCore Runtimes (3)
```bash
agentcore deploy --agent AcademicPipelineScholarDev
agentcore deploy --agent AcademicPipelineDIDev
agentcore deploy --agent AcademicPipelineContentDev
```

### Frontend
```bash
cd src/web_interface/frontend
npm install && npx vite build
aws s3 sync dist/ s3://academic-pipeline-frontend-254508868459-dev/ --delete
```

## URLs de Producción (dev)

| Recurso | URL |
|---------|-----|
| Frontend | http://academic-pipeline-frontend-254508868459-dev.s3-website-us-east-1.amazonaws.com |
| Web API | https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod/ |
| Checkpoint API | https://zcf0tiic2e.execute-api.us-east-1.amazonaws.com/prod/ |
| Cognito User Pool | us-east-1_29oR1qoVo |
| Staff User | staff-admin / Pipeline2026Edu! |

## Credenciales y Secretos

| Secreto | Ubicación |
|---------|-----------|
| Scopus API Key | Secrets Manager: `academic-pipeline/dev/scopus-api-key` |
| Canvas OAuth Token | Secrets Manager: `academic-pipeline/dev/canvas-oauth-token` |
| Canvas URL | https://anahuacmerida.instructure.com |

## Testing

```bash
# Unit tests (191 passing)
python -m pytest tests/ -q

# Test pipeline end-to-end
python test-data/check_subject.py /tmp/subject.json

# Review content quality
python test-data/review_content.py
```

## Configuración del Canvas Publisher

```bash
# Mock mode (default) — no hace llamadas reales a Canvas
aws lambda update-function-configuration \
  --function-name academic-pipeline-canvas-publisher-dev \
  --environment "Variables={CANVAS_MOCK_MODE=true,...}"

# Real mode — publica en Canvas LMS
aws lambda update-function-configuration \
  --function-name academic-pipeline-canvas-publisher-dev \
  --environment "Variables={CANVAS_MOCK_MODE=false,...}"
```
