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
| Investigación | Scopus API (Elsevier) + OpenAlex (abstracts) |
| LMS destino | Canvas LMS (Instructure) |
| Frontend | React + TypeScript + Vite (S3 Static Website) |
| IaC | AWS CDK (Python) |
| Secretos | AWS Secrets Manager |

## Pipeline por Asignatura

Cada asignatura pasa por 7 fases secuenciales:

### Fase 1: Ingesta
- Staff sube DOCX desde el frontend
- Parser extrae tablas Anáhuac: nombre, RAs, competencias, syllabus, duración (semanas)
- Crea Subject JSON en S3 y dispara Step Functions

### Fase 2: Scholar (AgentCore Runtime, ~3 min)
- Genera keywords específicos del dominio a partir del syllabus
- Busca en Scopus API papers Q1/Q2 (Top 20)
- Enriquece papers con abstracts de OpenAlex (API gratuita)
- Construye Knowledge Matrix con conceptos, definiciones y metodologías
- Auto-persiste a S3 + DynamoDB

### Fase 3: DI — Diseño Instruccional (AgentCore Runtime, ~2 min)
- Usa template Anáhuac MADTFIN para Carta Descriptiva
- Genera objetivos con Taxonomía de Bloom (Aplicar o superior)
- Audiencia: directivos financieros 5+ años experiencia
- Contexto regulatorio México (CNBV, Banxico, NIF)
- Genera mapa de contenidos semanal y casos ejecutivos

### Fase 4: Content — Generación de Recursos (AgentCore Runtime, ~5 min)
Genera contenido por semana usando llamadas LLM individuales:

**Por semana (= 1 Módulo en Canvas):**
- 1 Introducción (150-200 palabras)
- 3 Lecturas ejecutivas (400-500 palabras cada una, prosa narrativa)
- 1 Quiz de razonamiento crítico (8 preguntas, ≥3 en Analizar/Evaluar)
- 1 Foro de aprendizaje (caso de negocio + 3 preguntas + rúbrica evaluación pares)

**Recursos globales:**
- 1 Guión de Masterclass (18-22 min, con indicaciones [SLIDE]/[CASO VISUAL])
- 1 Reto de Aprendizaje Agéntico (escenario financiero mexicano, rúbrica 4 niveles)
- 4 Artefactos Maestría (dashboard, ruta crítica, casos, guía facilitador)

Para 5 semanas: 5 intros + 15 lecturas + 5 quizzes + 5 foros + masterclass + reto.

### Fase 5: QA Gate
- Valida cobertura 100% de RAs
- Valida alineación Bloom–Competencias
- Valida presencia de artefactos Maestría
- Si PASS → PENDING_APPROVAL

### Fase 6: Checkpoint Humano
- Pipeline se pausa — Staff revisa en frontend (10 tabs)
- Tabs: Resumen, Objetivos, Lecturas, Quizzes, Foros, Papers, Maestría, Masterclass, Reto, Preview Canvas
- Staff puede: Aprobar / Rechazar con comentarios
- Cursos publicados muestran banner verde + link a Canvas

### Fase 7: Canvas Publisher
- Crea curso con nombre de la asignatura (código MADTFIN)
- Estructura en Canvas:
  - Módulo "Información General": Carta Descriptiva, Masterclass, Guía Facilitador
  - Módulos semanales: Introducción, 3 Lecturas, Quiz, Foro (con rúbrica HTML)
  - Módulo "Reto de Aprendizaje Agéntico" (al final)
- Rúbricas renderizadas como tablas HTML con colores (4 niveles)

## Despliegue

### Prerrequisitos
- AWS CLI configurado
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
aws s3 sync dist/ s3://<FRONTEND_BUCKET>/ --delete
```

## URLs y Credenciales

Las URLs se generan durante el despliegue con CDK. Consultar los outputs de cada stack.

| Recurso | Descripción |
|---------|-------------|
| Frontend | S3 Static Website (output de WebInterface stack) |
| Web API | API Gateway REST (output de WebInterface stack) |
| Checkpoint API | API Gateway REST (output de QACheckpoint stack) |
| Cognito User Pool | Output de QACheckpoint stack |
| Staff User | Crear via Cognito console o CLI |

| Secreto | Ubicación |
|---------|-----------|
| Scopus API Key | Secrets Manager: `academic-pipeline/<env>/scopus-api-key` |
| Canvas OAuth Token | Secrets Manager: `academic-pipeline/<env>/canvas-oauth-token` |

## Testing

```bash
# Unit tests (191 passing)
python -m pytest tests/ -q

# Check subject state
python test-data/check_subject.py /tmp/subject.json

# Check content quality
python test-data/check_new_content.py /tmp/subject.json

# Show reading sizes
python test-data/show_readings.py /tmp/subject.json
```

## Configuración del Canvas Publisher

```bash
# Real mode (publica en Canvas LMS)
bash test-data/activate_canvas.sh

# Mock mode (simula sin Canvas real)
# Cambiar CANVAS_MOCK_MODE=true en la configuración del Lambda
```
