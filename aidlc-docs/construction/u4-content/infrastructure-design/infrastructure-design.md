# Diseño de Infraestructura — U4: Agente Content

## Patrón: AgentCore Runtime + Strands SDK

```bash
# Despliegue
agentcore configure --entrypoint src/agents/content/agent.py --non-interactive
agentcore deploy

# Variables de entorno requeridas
# SUBJECTS_BUCKET_NAME, SUBJECTS_TABLE_NAME
# STAFF_NOTIFICATIONS_TOPIC_ARN, AWS_REGION
```

## Estructura
```
src/agents/content/
├── agent.py          ← BedrockAgentCoreApp + @app.entrypoint + Strands Agent
├── models.py
├── content_generator.py   ← funciones puras de generación
├── apa_formatter.py       ← formateo bibliografía APA
└── coverage_checker.py    ← validación cobertura RA
```
