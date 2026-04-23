# Diseño de Infraestructura — U2: Agente Scholar

## Patrón: AgentCore Runtime + Strands SDK

El agente Scholar se despliega como un **AgentCore Runtime** usando el CLI `agentcore deploy`.
No usa `CfnAgent` ni Action Groups de Bedrock Agents clásico.

## Estructura del agente

```
src/agents/scholar/
├── agent.py          ← BedrockAgentCoreApp + @app.entrypoint + Strands Agent
├── models.py
├── keyword_generator.py
├── relevance_scorer.py
└── corpus_validator.py
```

## Despliegue con AgentCore CLI

```bash
# 1. Instalar CLI
pip install bedrock-agentcore-starter-toolkit

# 2. Configurar entrypoint
agentcore configure --entrypoint src/agents/scholar/agent.py --non-interactive

# 3. Desplegar (crea Runtime en AgentCore automáticamente)
agentcore deploy

# 4. Invocar
agentcore invoke '{"subject_id": "uuid-de-la-asignatura"}'
```

## Variables de entorno requeridas

```
SUBJECTS_BUCKET_NAME      = academic-pipeline-subjects-{account}-{region}-{env}
SUBJECTS_TABLE_NAME       = academic-pipeline-subjects-{env}
SCOPUS_SECRET_ARN         = arn:aws:secretsmanager:...
STAFF_NOTIFICATIONS_TOPIC_ARN = arn:aws:sns:...
AWS_REGION                = us-east-1
```

## Outputs
El ARN del Runtime se obtiene tras `agentcore deploy` y se almacena en SSM Parameter Store
para que el orquestador del pipeline pueda invocarlo.
