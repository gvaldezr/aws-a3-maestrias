# Known Issues — Pipeline Académico → Canvas LMS

## Resueltos

1. **Agentes sin contexto académico** → Cada agente carga subject JSON de S3
2. **MaxTokensReachedException** → Content agent usa llamadas LLM individuales (no agent loop)
3. **Auto-persistencia fallaba** → IAM permissions + direct persist + state regression guard
4. **DOCX parser no leía tablas** → Extrae tablas Anáhuac (nombre, RAs, syllabus, semanas)
5. **CORS en API Gateway** → Gateway Responses para 4xx/5xx + IdToken
6. **QA Report no persistía** → Direct S3 write (bypass schema validator)
7. **Semanas incorrectas** → Parser extrae "Duración del ciclo: N semanas"
8. **TypeError en tools** → `_ensure_dicts()` para strings JSON
9. **Contenido genérico** → Templates Anáhuac MADTFIN + LLM individual calls
10. **Scopus sin abstracts** → OpenAlex como complemento (auto-enrich en Scholar persist)
11. **Quiz formato incorrecto** → QA Gate acepta ra_ids (plural)
12. **Checkpoint 500 error** → Direct S3 write para approve/reject (bypass schema validator)
13. **Canvas un solo módulo** → 1 módulo por semana + módulos globales
14. **Rúbricas sin formato** → HTML tables con colores (4 niveles)
15. **Guía facilitador como JSON** → Renderizada como tabla HTML
16. **Reto en módulo incorrecto** → Módulo propio al final
17. **Nombre del curso genérico** → Usa nombre de la asignatura + prefijo MADTFIN

## Pendientes

| Problema | Severidad | Detalle |
|----------|-----------|---------|
| Content agent ~5 min con LLM | Baja | Dentro del timeout de 900s |
| Scopus Abstract API 401 | Baja | API key sin acceso. OpenAlex como complemento |
| Test coverage 26% | Baja | 191 tests pasan |
| RF-09 Paralelo | Media | 1 asignatura a la vez. Falta Map state en Step Functions |
| RF-11 Alarmas SNS | Baja | Topics existen pero sin suscriptores |

## Evolución Arquitectónica — Futura Iteración

### Migración de orquestación: Step Functions → Strands Agents Graph + AgentCore Memory

**Estado**: Análisis completado, pendiente de implementación.

**Contexto**: La orquestación actual usa Step Functions con 9 Lambdas (warmup, 3 invoke, 3 persist, qa, canvas). Cada agente implementa `_self_persist()` manualmente (~150 líneas por agente). Los 3 AgentCore Runtimes ya tienen memory IDs creados (STM_ONLY) pero no se usan.

**Propuesta**: Reemplazar Step Functions por un Strands `GraphBuilder` corriendo en un 4to AgentCore Runtime (orquestador), y activar AgentCore Memory para contexto conversacional entre agentes.

#### Plan de migración en 3 fases

| Fase | Cambio | Esfuerzo | Valor |
|------|--------|----------|-------|
| **1 — Activar Memory** | Agregar `AgentCoreMemorySessionManager` (STM) a los 3 agentes existentes. `session_id=subject_id`, `actor_id=agent_name`. No cambiar orquestación. | Bajo (1-2 días) | Agentes recuerdan contexto entre reintentos. Simplifica `_self_persist()`. |
| **2 — Strands Graph** | Crear AgentCore Runtime "Orchestrator" con Strands Graph. Los 3 agentes se invocan como agents-as-tools (HTTP). Reemplaza Step Functions + 9 Lambdas. | Medio (3-5 días) | Elimina 9 Lambdas + Step Functions. Paralelismo nativo. Conditional edges para QA retry. |
| **3 — Long-Term Memory** | Habilitar LTM con estrategia `semantic`. El orquestador aprende patrones entre asignaturas. | Bajo (1 día) | Personalización progresiva del pipeline. |

#### Qué se gana

- **Elimina 9 Lambdas + 1 Step Functions state machine** → 1 AgentCore Runtime orquestador
- **Paralelismo nativo**: `GraphBuilder` ejecuta nodos sin dependencias en paralelo (resuelve RF-09)
- **QA retry con conditional edges**: Reemplaza lógica manual de reintentos
- **Menos código**: Elimina `src/orchestrator/` (~400 líneas), simplifica `_self_persist()` en 3 agentes (~450 líneas)
- **Memoria entre sesiones**: LTM permite que el pipeline aprenda de ejecuciones anteriores

#### Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Pérdida de visibilidad de Step Functions (consola visual) | OpenTelemetry de Strands + CloudWatch Logs |
| Timeout de AgentCore (15 min request) — pipeline tarda ~10-12 min | Sesiones persistentes de AgentCore o async task management |
| Subject JSON en S3 sigue siendo necesario (frontend, checkpoint, Canvas) | Memory complementa, no reemplaza. Dos sistemas de estado coexisten. |
| Content Agent no usa agent loop (MaxTokensReachedException) | Mantener patrón de llamadas directas a tools dentro del nodo del Graph |
| Complejidad de migración de entrypoints | Fase 2 usa agents-as-tools (invocación HTTP) para mínimo cambio |

#### Recursos de memoria existentes (no usados)

| Agente | Memory ID | ARN |
|--------|-----------|-----|
| Scholar | `AcademicPipelineScholarDev_mem-FYZKJbF5He` | `arn:aws:bedrock-agentcore:us-east-1:254508868459:memory/AcademicPipelineScholarDev_mem-FYZKJbF5He` |
| DI | `AcademicPipelineDIDev_mem-4QE2yM6pPf` | `arn:aws:bedrock-agentcore:us-east-1:254508868459:memory/AcademicPipelineDIDev_mem-4QE2yM6pPf` |
| Content | `AcademicPipelineContentDev_mem-Gjqbhj7KMz` | `arn:aws:bedrock-agentcore:us-east-1:254508868459:memory/AcademicPipelineContentDev_mem-Gjqbhj7KMz` |

#### Referencias

- [Strands Agents Graph](https://strandsagents.com/docs/user-guide/concepts/multi-agent/graph/index.md)
- [Strands Agents Workflow](https://strandsagents.com/docs/user-guide/concepts/multi-agent/workflow/index.md)
- [AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [AgentCore Memory + Strands integration](https://strandsagents.com/docs/community/session-managers/agentcore-memory/index.md)
- [Long-running tasks con AgentCore + Strands](https://aws.amazon.com/blogs/machine-learning/build-long-running-mcp-servers-on-amazon-bedrock-agentcore-with-strands-agents-integration/)
