# Guía de Operación

## Uso del Sistema

### 1. Subir una asignatura

1. Abrir el frontend: http://academic-pipeline-frontend-254508868459-dev.s3-website-us-east-1.amazonaws.com
2. Login: `staff-admin` / `Pipeline2026Edu!`
3. En "Cargar Documentos", seleccionar el archivo DOCX de la asignatura
4. Clic en "Cargar"
5. El pipeline se ejecuta automáticamente (~10-12 minutos)

### 2. Revisar contenido generado

1. En el Dashboard, buscar la asignatura con estado "⏳ Pendiente de aprobación"
2. Clic en "📋 Revisar"
3. Navegar las 6 tabs:
   - **Resumen**: QA Gate, conteos, carta descriptiva, mapa semanal
   - **Objetivos**: Bloom levels, competencias, RAs
   - **Lecturas**: Contenido expandible por semana
   - **Quizzes**: Preguntas con opciones y respuesta correcta
   - **Papers**: 20 papers de Scopus
   - **Maestría**: Dashboard, ruta crítica, casos, guía facilitador
4. Decidir: ✅ Aprobar / ❌ Rechazar con comentarios

### 3. Publicar en Canvas

- Al aprobar, el Canvas Publisher se ejecuta automáticamente
- En modo mock: genera URLs simuladas
- En modo real: crea el curso en Canvas LMS como borrador

## Administración

### Redesplegar agentes

```bash
# Los 3 agentes
for AGENT in AcademicPipelineScholarDev AcademicPipelineDIDev AcademicPipelineContentDev; do
  agentcore deploy --agent $AGENT
done
```

### Redesplegar Lambdas (sin CDK)

```bash
bash test-data/deploy_lambdas.sh      # QA Gate + Checkpoint
bash test-data/deploy_web_lambdas.sh   # Upload + Ingestion + Dashboard
bash test-data/deploy_canvas.sh        # Canvas Publisher
```

### Redesplegar frontend

```bash
cd src/web_interface/frontend
npm install && npx vite build
aws s3 sync dist/ s3://academic-pipeline-frontend-254508868459-dev/ --delete
```

### Redesplegar infraestructura (CDK)

```bash
npx cdk deploy --all --require-approval never
```

### Ejecutar pipeline manualmente

```bash
# Via Step Functions
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:254508868459:stateMachine:academic-pipeline-orchestrator-dev \
  --input '{"subject_id": "UUID_HERE"}'

# Via agentes individuales
agentcore invoke --agent AcademicPipelineScholarDev '{"subject_id": "UUID"}'
agentcore invoke --agent AcademicPipelineDIDev '{"subject_id": "UUID"}'
agentcore invoke --agent AcademicPipelineContentDev '{"subject_id": "UUID"}'
```

### Ejecutar QA Gate manualmente

```bash
aws lambda invoke --function-name academic-pipeline-qa-gate-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"subject_id": "UUID"}' \
  --region us-east-1 /tmp/qa.json
```

### Cambiar Canvas a modo real

```bash
aws lambda update-function-configuration \
  --function-name academic-pipeline-canvas-publisher-dev \
  --environment "Variables={CANVAS_MOCK_MODE=false,CANVAS_BASE_URL=https://anahuacmerida.instructure.com,CANVAS_SECRET_ARN=arn:aws:secretsmanager:us-east-1:254508868459:secret:academic-pipeline/dev/canvas-oauth-token,SUBJECTS_BUCKET_NAME=academic-pipeline-subjects-254508868459-us-east-1-dev,SUBJECTS_TABLE_NAME=academic-pipeline-subjects-dev}" \
  --region us-east-1
```

## Monitoreo

### CloudWatch Logs

```bash
# Agentes
aws logs tail /aws/bedrock-agentcore/runtimes/AcademicPipelineScholarDev-7S4W3RBBi0-DEFAULT --since 1h --follow
aws logs tail /aws/bedrock-agentcore/runtimes/AcademicPipelineDIDev-Rp1Oj57gGL-DEFAULT --since 1h --follow
aws logs tail /aws/bedrock-agentcore/runtimes/AcademicPipelineContentDev-fX2AEsCaMw-DEFAULT --since 1h --follow

# Step Functions
aws logs tail /aws/lambda/academic-pipeline-orch-scholarstep-dev --since 1h

# QA Gate
aws logs tail /aws/lambda/academic-pipeline-qa-gate-dev --since 1h
```

### Verificar estado de un subject

```bash
# DynamoDB
aws dynamodb get-item --table-name academic-pipeline-subjects-dev \
  --key '{"subject_id":{"S":"UUID"},"SK":{"S":"STATE"}}' \
  --query "Item.{state:current_state.S,name:subject_name.S}"

# S3 JSON completo
aws s3 cp s3://academic-pipeline-subjects-254508868459-us-east-1-dev/subjects/UUID/subject.json /tmp/subject.json
python test-data/check_subject.py /tmp/subject.json
```

## Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| "Asignatura sin nombre" | Parser no extrajo datos del DOCX | Verificar que el DOCX tiene tablas con "Denominación de la asignatura" |
| MaxTokensReachedException | Prompt muy largo para el agent loop | Verificar max_tokens=16384 en el agente |
| CORS error en frontend | Token expirado o API Gateway sin CORS en 4xx | Limpiar localStorage y re-login |
| QA Gate error 500 | Schema validator rechaza campos extra | QA Gate usa _save_json_direct (bypass validator) |
| Agente no persiste | Rol IAM sin permisos S3/DynamoDB | Verificar policy AcademicPipelineDataAccess en el rol |
| Estado regresa a CONTENT_READY | Race condition en auto-persist | Agentes verifican estado antes de escribir |
| Canvas Publisher import error | httpx/tenacity no en Lambda Layer | canvas_client usa import lazy de httpx |

## Recursos AWS Desplegados

| Recurso | Nombre/ARN |
|---------|-----------|
| S3 Bucket | academic-pipeline-subjects-254508868459-us-east-1-dev |
| S3 Frontend | academic-pipeline-frontend-254508868459-dev |
| DynamoDB | academic-pipeline-subjects-dev |
| Cognito Pool | us-east-1_29oR1qoVo (client: v8mnl80kg82gr2ejrvakdq6ju) |
| Step Functions | academic-pipeline-orchestrator-dev |
| Scholar Runtime | AcademicPipelineScholarDev-7S4W3RBBi0 |
| DI Runtime | AcademicPipelineDIDev-Rp1Oj57gGL |
| Content Runtime | AcademicPipelineContentDev-fX2AEsCaMw |
| Web API | https://z1px5977b8.execute-api.us-east-1.amazonaws.com/prod/ |
| Checkpoint API | https://zcf0tiic2e.execute-api.us-east-1.amazonaws.com/prod/ |
