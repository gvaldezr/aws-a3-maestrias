# Estimación de Costos por Materia Procesada
## Pipeline Académico → Canvas LMS
### Fecha: 2026-04-27

---

## Resumen Ejecutivo

Cada materia (asignatura) procesada por el pipeline tiene un costo estimado de **~$0.98 USD**, donde el **88.5% corresponde a Amazon Bedrock** (Claude Sonnet 4.6). La arquitectura serverless garantiza **$0 cuando no hay ejecuciones**, con un costo fijo mensual de infraestructura de ~$5 USD.

---

## Flujo del Pipeline por Materia

```
Upload → Ingestion → Warmup → Scholar → DI → Content → QA Gate → Checkpoint → Canvas
  (S3)    (Lambda)   (AgentCore×3)  (AgentCore)  (AgentCore)  (Lambda)   (API GW)   (Lambda)
```

Orquestado por **AWS Step Functions** con ~12 transiciones de estado por materia.

---

## 1. Amazon Bedrock — Claude Sonnet 4.6

**Pricing on-demand**: $3.00 / 1M input tokens — $15.00 / 1M output tokens

### 1.1 Agente Scholar (1 invocación agéntica)

| Concepto | Input tokens | Output tokens |
|---|---|---|
| System prompt + prompt con syllabus completo | ~3,000 | — |
| Tool calls (search_scopus, enrich_abstracts, build_knowledge_matrix) | ~2,000 | ~4,000 |
| Respuesta final JSON (top20_papers + knowledge_matrix + keywords) | ~1,000 | ~6,000 |
| **Subtotal Scholar** | **~6,000** | **~10,000** |

### 1.2 Agente DI (1 invocación agéntica)

| Concepto | Input tokens | Output tokens |
|---|---|---|
| System prompt + prompt carta descriptiva (template Anáhuac) | ~4,000 | — |
| Tool calls (generate_learning_objectives, build_descriptive_card) | ~2,000 | ~3,000 |
| Respuesta final JSON (objectives + traceability + card + content_map) | ~1,000 | ~5,000 |
| **Subtotal DI** | **~7,000** | **~8,000** |

### 1.3 Agente Content — Llamadas LLM individuales

El Content agent ejecuta llamadas directas a Claude (no agénticas) para generar contenido semana por semana. Para una materia típica de **5 semanas**:

| Recurso generado | Llamadas LLM | Input/llamada | Output/llamada |
|---|---|---|---|
| Introducción semanal (150-200 palabras) | 5 | ~500 | ~800 |
| 3 Lecturas ejecutivas × 5 semanas (400-500 palabras c/u) | 15 | ~800 | ~1,500 |
| Quiz semanal — 8 preguntas de razonamiento crítico | 5 | ~600 | ~2,000 |
| Masterclass script (guión 18-22 min) | 1 | ~600 | ~2,000 |
| Reto agéntico (escenario + rúbrica) | 1 | ~500 | ~1,500 |
| **Subtotal Content** | **27 llamadas** | **~18,000** | **~35,000** |

### 1.4 Warmup (pre-calentamiento de microVMs)

| Concepto | Input tokens | Output tokens |
|---|---|---|
| 3 pings a agentes (Scholar, DI, Content) | ~300 | ~300 |

### 1.5 Totales Bedrock por Materia

| Agente | Input tokens | Output tokens | Costo input | Costo output | **Total** |
|---|---|---|---|---|---|
| Scholar | 6,000 | 10,000 | $0.018 | $0.150 | **$0.168** |
| DI | 7,000 | 8,000 | $0.021 | $0.120 | **$0.141** |
| Content (27 calls) | 18,000 | 35,000 | $0.054 | $0.525 | **$0.579** |
| Warmup | 300 | 300 | $0.001 | $0.005 | **$0.006** |
| **TOTAL BEDROCK** | **31,300** | **53,300** | **$0.094** | **$0.800** | **$0.894** |

---

## 2. AgentCore Runtime (Compute de microVMs)

Los 3 agentes corren en microVMs Firecracker de AgentCore Runtime. Se cobra por segundo de sesión activa.

| Agente | Lambda timeout | Duración estimada | Sesiones |
|---|---|---|---|
| Warmup (3 pings) | 120s | ~45s | 3 |
| Scholar | 600s | ~120s | 1 |
| DI | 480s | ~90s | 1 |
| Content | 600s | ~180s (27 LLM calls) | 1 |

**Costo estimado AgentCore compute**: **~$0.075** por materia

---

## 3. AWS Lambda

| Función | Memory | Timeout | Duración est. | Invocaciones/materia |
|---|---|---|---|---|
| Orchestrator Lambdas (9 steps) | 512 MB | 30–600s | ~5s promedio | 9 |
| QA Gate | 256 MB | 30s | ~5s | 1 |
| Checkpoint handler | 256 MB | 30s | ~2s | 1 |
| Canvas Publisher | 512 MB | 300s | ~15s | 1 |
| Ingestion handler | 256 MB | 30s | ~5s | 1 |
| Upload handler | 256 MB | 30s | ~2s | 1 |
| Dashboard handler | 256 MB | 30s | ~2s | ~5 (polling) |

**Cálculo**: ~14 invocaciones × 512MB × 5s promedio = 35,840 MB-s = 35.84 GB-s

Lambda pricing: $0.0000166667/GB-s → **~$0.001** por materia

---

## 4. APIs Externas

| API | Llamadas/materia | Costo |
|---|---|---|
| Scopus (Elsevier) — búsqueda papers Q1/Q2 | 1–3 queries | **$0.00** (API Key institucional, 20K/semana) |
| OpenAlex — enriquecimiento de abstracts | 1 batch (20 papers) | **$0.00** (API gratuita, sin límite) |
| Canvas LMS — publicación de curso | 1 sesión (~5 API calls) | **$0.00** (incluido en licencia institucional) |

---

## 5. Almacenamiento y Base de Datos

### Amazon S3

| Operación | Cantidad/materia | Costo |
|---|---|---|
| PutObject (JSON ~500KB, múltiples escrituras entre fases) | ~8 | $0.000040 |
| GetObject (lecturas entre fases) | ~15 | $0.000006 |
| Storage mensual (500KB × 1 mes, Standard) | 0.0005 GB | $0.000012 |
| **Total S3** | | **~$0.0001** |

### Amazon DynamoDB (On-Demand)

| Operación | Cantidad/materia | Costo |
|---|---|---|
| Write — PutItem (state updates, GSI propagation) | ~10 WCU | $0.0000125 |
| Read — GetItem (state checks, dashboard queries) | ~20 RCU | $0.0000050 |
| **Total DynamoDB** | | **~$0.00002** |

---

## 6. Step Functions

| Concepto | Cantidad | Costo |
|---|---|---|
| Standard workflow — transiciones de estado | ~12 | **$0.0003** |

---

## 7. Servicios de Soporte (por materia)

| Servicio | Uso por materia | Costo |
|---|---|---|
| Secrets Manager (lectura de Scopus key + Canvas token) | 3 API calls | $0.0000012 |
| SNS (notificación al Staff para checkpoint) | 2 publishes | $0.000001 |
| CloudWatch Logs (ingesta de logs de todos los componentes) | ~5 MB | $0.0025 |
| KMS (encrypt/decrypt S3 + DynamoDB) | ~20 operaciones | $0.00006 |
| API Gateway (checkpoint + dashboard requests) | ~10 requests | $0.000035 |
| **Total servicios de soporte** | | **~$0.003** |

---

## 8. Costos Fijos Mensuales (independientes del volumen)

| Servicio | Concepto | Costo/mes |
|---|---|---|
| KMS | 1 CMK (academic-pipeline) | $1.00 |
| Secrets Manager | 3 secretos (Scopus, Canvas, CDK) | $1.20 |
| CloudWatch | Retención 90 días (7 log groups) | $2.00 |
| EventBridge Scheduler | Timeout checker cada hora | $0.50 |
| Cognito | User Pool (<50K MAU) | $0.00 (free tier) |
| S3 (frontend) | Static site hosting | $0.30 |
| **Total fijo mensual** | | **~$5.00** |

---

## Resumen: Costo Total por Materia

| Componente | Costo/materia | % del total |
|---|---|---|
| **Amazon Bedrock (Claude Sonnet 4.6)** | **$0.894** | **88.5%** |
| **AgentCore Runtime (compute microVM)** | **$0.075** | **7.4%** |
| **CloudWatch Logs** | $0.003 | 0.3% |
| **AWS Lambda** | $0.001 | 0.1% |
| **S3 + DynamoDB + Step Functions** | $0.001 | 0.1% |
| **Servicios de soporte (SNS, KMS, API GW, Secrets)** | $0.003 | 0.3% |
| **APIs externas (Scopus, OpenAlex, Canvas)** | $0.000 | 0.0% |
| | | |
| **TOTAL POR MATERIA** | **~$0.98 USD** | **100%** |

---

## Proyecciones por Volumen Mensual

| Escenario | Materias/mes | Costo variable | Costo fijo | **Total mensual** |
|---|---|---|---|---|
| Mínimo (1 programa) | 6 | $5.85 | $5.00 | **$10.85** |
| Típico (2 programas) | 15 | $14.63 | $5.00 | **$19.63** |
| Máximo (4 programas) | 40 | $39.00 | $5.00 | **$44.00** |
| Escala (10 programas) | 100 | $97.50 | $5.00 | **$102.50** |

---

## Proyección Anual

| Escenario | Materias/año | **Costo anual estimado** |
|---|---|---|
| Mínimo — 6 materias × 2 ciclos | 12 | **~$72** |
| Típico — 15 materias × 3 ciclos | 45 | **~$104** |
| Máximo — 40 materias × 3 ciclos | 120 | **~$178** |
| Escala — 100 materias × 3 ciclos | 300 | **~$354** |

---

## Oportunidades de Optimización

### Opción A: Claude Haiku para contenido templado
Usar **Claude Haiku** ($0.25/$1.25 per 1M tokens) para lecturas ejecutivas y quizzes (27 llamadas del Content agent), reservando Sonnet solo para Scholar y DI:

| Componente | Costo actual | Costo optimizado | Ahorro |
|---|---|---|---|
| Content agent (27 calls) | $0.579 | $0.068 | **-88%** |
| **Total por materia** | $0.98 | **$0.39** | **-60%** |

### Opción B: Bedrock Batch API (50% descuento)
Si las materias se procesan en lote (no requieren resultado inmediato):

| Componente | Costo actual | Costo batch | Ahorro |
|---|---|---|---|
| Todo Bedrock | $0.894 | $0.447 | **-50%** |
| **Total por materia** | $0.98 | **$0.53** | **-46%** |

### Opción C: Combinación Haiku + Batch
Haiku para Content + Batch para todo:

| **Total por materia optimizado** | **~$0.24 USD** | **Ahorro: -76%** |
|---|---|---|

---

## Comparativa con Alternativas

| Enfoque | Costo/materia | Tiempo | Calidad |
|---|---|---|---|
| **Pipeline actual (Sonnet 4.6)** | $0.98 | ~8 min | Alta (Q1/Q2 papers, Bloom, trazabilidad) |
| Pipeline optimizado (Haiku + Batch) | $0.24 | ~15 min | Media-Alta |
| Diseño instruccional manual (1 persona) | ~$500–1,500 | 40–80 hrs | Variable |
| Consultoría externa | ~$2,000–5,000 | 2–4 semanas | Alta |

**ROI**: El pipeline automatizado reduce el costo de diseño instruccional en **99.9%** comparado con el proceso manual, manteniendo trazabilidad académica completa (Bloom → Competencias → Perfil de Egreso).

---

## Notas Técnicas

1. **Modelo utilizado**: `us.anthropic.claude-sonnet-4-6` (cross-region inference, us-east-1)
2. **Tokens estimados con base en**: análisis del código fuente de los 3 agentes y sus prompts
3. **Materia típica**: 5 semanas, 2 resultados de aprendizaje, 3-4 competencias, 20 papers Q1/Q2
4. **$0 idle**: toda la arquitectura es serverless pay-per-use; sin costos cuando no hay ejecuciones
5. **Precios**: región us-east-1, on-demand, a fecha abril 2026
