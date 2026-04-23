# Build Instructions
## Pipeline Académico → Canvas LMS

---

## Prerrequisitos

| Requisito | Versión | Notas |
|---|---|---|
| Python | 3.11+ | Runtime de todos los agentes y Lambdas |
| Node.js | 18+ | Frontend React/TypeScript |
| AWS CDK CLI | 2.x | `npm install -g aws-cdk` |
| AWS CLI | 2.x | Configurado con credenciales de despliegue |
| AgentCore CLI | latest | `pip install bedrock-agentcore-starter-toolkit` |
| Docker | 20+ | Para builds locales de AgentCore |

---

## Variables de Entorno Requeridas

```bash
# AWS
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=<tu-account-id>
export CDK_ENV=dev   # dev | staging | prod

# Pipeline
export CANVAS_BASE_URL=https://<institution>.instructure.com
export CANVAS_ACCOUNT_ID=1
export SCHOLAR_AGENT_RUNTIME_ARN=<arn-tras-agentcore-deploy>
export ALLOWED_ORIGIN=https://<tu-dominio-amplify>.amplifyapp.com
```

---

## Pasos de Build

### 1. Instalar dependencias Python

```bash
# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependencias (pinadas en pyproject.toml)
pip install -e ".[dev]"

# Verificar instalación
python -c "import bedrock_agentcore; import strands; print('OK')"
```

### 2. Instalar dependencias Frontend

```bash
cd src/web-interface/frontend
npm install
npm run build   # genera build estático en dist/
cd ../../..
```

### 3. Sintetizar CDK (validación de infraestructura)

```bash
# Bootstrap (solo primera vez por cuenta/región)
cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_REGION}

# Sintetizar todos los stacks
cdk synth --context env=${CDK_ENV} --context account=${AWS_ACCOUNT_ID} --context region=${AWS_REGION}
```

**Salida esperada**: Archivos CloudFormation en `cdk.out/` sin errores.

### 4. Desplegar infraestructura base (U1)

```bash
cdk deploy AcademicPipeline-Infrastructure-Dev \
  --context env=dev \
  --context account=${AWS_ACCOUNT_ID} \
  --context region=${AWS_REGION} \
  --require-approval never
```

**Poblar secretos manualmente tras el despliegue:**
```bash
aws secretsmanager put-secret-value \
  --secret-id "academic-pipeline/dev/scopus-api-key" \
  --secret-string '{"api_key": "<tu-scopus-api-key>"}'

aws secretsmanager put-secret-value \
  --secret-id "academic-pipeline/dev/canvas-oauth-token" \
  --secret-string '{"oauth_token": "<tu-canvas-token>"}'
```

### 5. Desplegar agentes con AgentCore CLI (U2, U3, U4)

```bash
# Agente Scholar
agentcore configure --entrypoint src/agents/scholar/agent.py --non-interactive
agentcore deploy
export SCHOLAR_AGENT_RUNTIME_ARN=$(agentcore status --json | jq -r '.runtime_arn')

# Agente DI
agentcore configure --entrypoint src/agents/di/agent.py --non-interactive
agentcore deploy

# Agente Content
agentcore configure --entrypoint src/agents/content/agent.py --non-interactive
agentcore deploy
```

### 6. Desplegar Lambdas restantes (U5, U6, U7)

```bash
cdk deploy AcademicPipeline-QACheckpoint-Dev \
  AcademicPipeline-CanvasPublisher-Dev \
  AcademicPipeline-WebInterface-Dev \
  --context env=dev --require-approval never
```

### 7. Verificar despliegue

```bash
# Verificar Lambdas activas
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'academic-pipeline')].[FunctionName,LastModified]" --output table

# Verificar AgentCore Runtimes
agentcore list

# Verificar API Gateway
aws apigateway get-rest-apis --query "items[?name=='academic-pipeline-api-dev']"
```

---

## Artefactos Generados

| Artefacto | Ubicación |
|---|---|
| CloudFormation templates | `cdk.out/` |
| Frontend build | `src/web-interface/frontend/dist/` |
| AgentCore configs | `.agentcore/` |
| Lambda packages | Generados por CDK en `cdk.out/` |

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'bedrock_agentcore'`
```bash
pip install bedrock-agentcore-starter-toolkit
```

### Error: `CDK bootstrap required`
```bash
cdk bootstrap aws://${AWS_ACCOUNT_ID}/${AWS_REGION}
```

### Error: `Canvas API 401 Unauthorized`
Verificar que el OAuth Token en Secrets Manager es válido y no ha expirado.
