---
inclusion: manual
---

# Guía de Despliegue — Pipeline Académico

## Prerrequisitos
- AWS CLI configurado con cuenta `254508868459`, región `us-east-1`
- Node.js 18+ (para CDK)
- Python 3.11
- AgentCore CLI: `pip install bedrock-agentcore-starter-toolkit`
- CDK CLI: `npm install -g aws-cdk`

## 1. CDK Stacks (5 stacks)

```bash
# Desplegar todos los stacks
npx cdk deploy --all --require-approval never

# Desplegar stack individual
npx cdk deploy InfrastructureBaseStack
npx cdk deploy QACheckpointStack
npx cdk deploy CanvasPublisherStack
npx cdk deploy OrchestratorStack
npx cdk deploy WebInterfaceStack
```

### Orden de dependencias
1. InfrastructureBase (S3, DynamoDB, KMS, SNS, Secrets Manager)
2. QACheckpoint (Cognito, QA Gate, Checkpoint, API Gateway)
3. CanvasPublisher (Canvas Publisher Lambda)
4. Orchestrator (Step Functions, 9 Lambda handlers)
5. WebInterface (Upload/Ingestion/Dashboard, API Gateway, S3 trigger)

## 2. AgentCore Runtimes (3 agentes)

```bash
# Desplegar cada agente
agentcore deploy --agent AcademicPipelineScholarDev
agentcore deploy --agent AcademicPipelineDIDev
agentcore deploy --agent AcademicPipelineContentDev
```

### Configuración en `.bedrock_agentcore.yaml`
- Runtime: `PYTHON_3_11`
- Platform: `linux/arm64`
- Network: `PUBLIC`
- Protocol: `HTTP`
- Observability: `enabled: true`
- Deploy type: `direct_code_deploy`
- S3 source: `s3://bedrock-agentcore-codebuild-sources-254508868459-us-east-1`

## 3. Frontend

```bash
cd src/web_interface/frontend
npm install
npx vite build
aws s3 sync dist/ s3://<FRONTEND_BUCKET>/ --delete
```

## 4. Secretos (configurar una vez)

```bash
# Scopus API Key
aws secretsmanager create-secret \
  --name academic-pipeline/dev/scopus-api-key \
  --secret-string '{"api_key": "YOUR_SCOPUS_KEY"}'

# Canvas OAuth Token
aws secretsmanager create-secret \
  --name academic-pipeline/dev/canvas-oauth-token \
  --secret-string '{"oauth_token": "YOUR_CANVAS_TOKEN"}'
```

## 5. Canvas Publisher Mode

```bash
# Real mode (publica en Canvas LMS)
bash test-data/activate_canvas.sh

# Mock mode (simula sin Canvas real)
# Cambiar CANVAS_MOCK_MODE=true en la configuración del Lambda
```

## URLs post-despliegue
Las URLs se generan como outputs de cada CDK stack:
- Frontend: S3 Static Website (output de WebInterface)
- Web API: API Gateway REST (output de WebInterface)
- Checkpoint API: API Gateway REST (output de QACheckpoint)
- Cognito User Pool: Output de QACheckpoint

## Troubleshooting común
- **AgentCore timeout**: El Content agent tarda ~5 min. El timeout de sesión es 900s.
- **Scopus 401**: La API key puede no tener acceso a Abstract API. OpenAlex complementa.
- **CORS errors**: Verificar Gateway Responses para 4xx/5xx + usar IdToken (no AccessToken).
- **Schema validation bypass**: QA report y checkpoint escriben directo a S3 (bypass schema validator).
