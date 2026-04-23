# Tech Stack — U2: Agente Scholar

| Componente | Tecnología | Justificación |
|---|---|---|
| Agente de IA | Amazon Bedrock Agent (Claude Sonnet 3.5) | Nativo AWS, soporte Action Groups, contexto largo para análisis de papers |
| Action Group Scopus | AWS Lambda (Python 3.11) | Serverless, integración nativa con Bedrock Agents |
| HTTP client Scopus | httpx (async) | Async nativo, mejor manejo de timeouts y retries |
| Credenciales | AWS Secrets Manager | Consistente con U1 |
| Retry logic | tenacity | Decoradores de retry con backoff exponencial, bien testeado |
| PBT | Hypothesis | Consistente con U1 (PBT-09) |
