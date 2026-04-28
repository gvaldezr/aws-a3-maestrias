---
inclusion: fileMatch
fileMatchPattern: "**/agents/**,**/agent*,**/strands*,**/bedrock*"
---

# Desarrollo de Agentes — AgentCore + Strands SDK

## Arquitectura de agentes

El sistema tiene 3 agentes desplegados como AgentCore Runtimes:

| Agente | Directorio | Modelo | Temperatura | Max Tokens |
|--------|-----------|--------|-------------|-----------|
| Scholar | `src/agents/scholar/` | claude-sonnet-4.6 | 0.0 | 16384 |
| DI | `src/agents/di/` | claude-sonnet-4.6 | 0.0 | 16384 |
| Content | `src/agents/content/` | claude-sonnet-4.6 | 0.3 | 32768 |

## Patrón de entrypoint

Todos los agentes siguen este patrón exacto:

1. `BedrockAgentCoreApp()` a nivel de módulo
2. `_agent = None` como global lazy
3. `_get_agent()` con lazy init que importa `strands` internamente
4. Tools definidos con `@tool` dentro de `_get_agent()`
5. `@app.entrypoint` para `invoke(payload, context)`
6. `app.run()` en `__main__`

## Tools por agente

### Scholar (`src/agents/scholar/`)
- `search_scopus_papers(keywords, subject_id)` — Busca en Scopus API
- `enrich_papers_with_abstracts(papers)` — Enriquece con OpenAlex
- `build_knowledge_matrix(papers, learning_outcomes)` — Construye Knowledge Matrix
- Módulos auxiliares: `keyword_generator.py`, `openalex_client.py`, `relevance_scorer.py`, `corpus_validator.py`

### DI (`src/agents/di/`)
- `generate_learning_objectives(learning_outcomes, competencies, subject_type, knowledge_matrix)` — Objetivos Bloom
- `build_descriptive_card(objectives, subject_type, subject_name, graduation_profile, knowledge_matrix)` — Carta Descriptiva V1
- Módulos auxiliares: `bloom_mapper.py`, `card_builder.py`, `carta_descriptiva_prompt.py`, `traceability.py`

### Content (`src/agents/content/`)
- `generate_executive_readings(weekly_map, subject_name, language, papers, knowledge_matrix)` — Lecturas ejecutivas
- `generate_quizzes(learning_outcomes, subject_name, language, objectives, syllabus)` — Quizzes por RA
- `generate_maestria_artifacts(papers, subject_name, competencies, language, weekly_map, learning_outcomes)` — 4 artefactos Maestría
- Módulos auxiliares: `weekly_generator.py`, `llm_generator.py`, `coverage_checker.py`, `apa_formatter.py`
- **IMPORTANTE**: Content Agent llama tools directamente (no agent loop) para evitar MaxTokensReachedException

## Self-persist pattern

Cada agente implementa `_self_persist()` que:
1. Lee el Subject JSON actual de S3
2. Parsea el JSON del resultado del agente (busca bloques ```json)
3. Enriquece la sección correspondiente del Subject JSON
4. Verifica state regression guard (no retroceder estados)
5. Actualiza `pipeline_state.current_state` y `state_history`
6. Escribe a S3 y actualiza DynamoDB

## Prompt engineering

- System prompts cortos y directivos
- Instrucciones de output: "Return a single JSON block: ```json\n{...}\n```"
- Enforcement de IDs exactos: "Use EXACT competency IDs: C1, C2, C3, C4"
- Enforcement de semanas: "Generate EXACTLY N weeks"
- No text outside JSON block

## Despliegue de agentes

```bash
# Desplegar un agente
agentcore deploy --agent AcademicPipelineScholarDev

# Configuración en .bedrock_agentcore.yaml
# - runtime_type: PYTHON_3_11
# - deployment_type: direct_code_deploy
# - network_mode: PUBLIC
# - server_protocol: HTTP
```

## Testing de agentes

- Mockear `strands.Agent.__call__` para tests unitarios
- Mockear `boto3.client('s3')` y `boto3.resource('dynamodb')` con moto
- Mockear `httpx.Client` para Scopus API
- Verificar que `_self_persist()` escribe correctamente al Subject JSON
- Verificar state regression guard
