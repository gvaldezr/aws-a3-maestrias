# Diseño de Infraestructura — U3: Agente DI

## CDK Stack: DIAgentStack

El agente DI se despliega como **AgentCore Runtime** usando el CLI `agentcore deploy`.

```bash
# Configurar y desplegar
agentcore configure --entrypoint src/agents/di/agent.py --non-interactive
agentcore deploy

# Variables de entorno requeridas
# SUBJECTS_BUCKET_NAME, SUBJECTS_TABLE_NAME, STAFF_NOTIFICATIONS_TOPIC_ARN, AWS_REGION
```
