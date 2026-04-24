# Known Issues — Pipeline Académico → Canvas LMS

## Issue 1: Step Functions → AgentCore Runtime — Persistencia de datos

**Estado**: Pendiente
**Severidad**: Media — el pipeline ejecuta pero los datos generados por los agentes no se persisten en el JSON de S3.

### Descripción
Cuando Step Functions invoca los agentes AgentCore (Scholar, DI, Content) via `invoke_agent_runtime`, el agente retorna error 500 porque el runtime del agente no tiene acceso a AWS Secrets Manager para obtener la API Key de Scopus.

Los agentes funcionan correctamente cuando se invocan directamente con `agentcore invoke` (usa credenciales locales del usuario), pero fallan cuando se invocan desde Lambda (usa el rol IAM del Lambda, no el del AgentCore Runtime).

### Impacto
- El Step Functions completa (SUCCEEDED) pero las secciones `research`, `instructional_design` y `content_package` del JSON quedan vacías
- El historial de estados se actualiza correctamente (3 transiciones)
- El DynamoDB muestra el estado correcto (CONTENT_READY)

### Causa raíz
El AgentCore Runtime ejecuta el agente en un microVM aislado con su propio rol IAM. Cuando el agente intenta acceder a Secrets Manager para obtener la API Key de Scopus, el rol del runtime no tiene permisos para `secretsmanager:GetSecretValue`.

### Soluciones propuestas

**Opción A (recomendada)**: Agregar permisos de Secrets Manager al rol IAM del AgentCore Runtime
```bash
aws iam put-role-policy \
  --role-name AmazonBedrockAgentCoreSDKRuntime-us-east-1-4058655f4d \
  --policy-name SecretsManagerAccess \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":"arn:aws:secretsmanager:us-east-1:254508868459:secret:academic-pipeline/*"}]}'
```

**Opción B**: Pasar la API Key como variable de entorno del AgentCore Runtime via `agentcore configure --env`

**Opción C**: Que el orquestador (Lambda) obtenga la API Key de Secrets Manager y la pase como parámetro al agente en el payload de invocación

### Workaround actual
Los agentes se pueden invocar manualmente con `agentcore invoke` y producen resultados correctos (probado con Scopus real — 20 papers Q1).

---

## Issue 2: Frontend — Archivos subidos no siempre aparecen en el dashboard

**Estado**: Parcialmente resuelto
**Severidad**: Baja

### Descripción
Cuando se sube un archivo desde el frontend, el presigned URL funciona y el archivo llega a S3, pero el registro en DynamoDB puede tardar hasta 30 segundos en aparecer (polling interval del dashboard).

### Workaround
Esperar 30 segundos y el dashboard se actualiza automáticamente.

---

## Issue 3: Registros corruptos de pruebas anteriores

**Estado**: Resuelto
**Severidad**: Baja

### Descripción
Algunos registros en DynamoDB y S3 contienen datos corruptos de pruebas anteriores (ej: contenido XML de .docx parseado como texto plano antes del fix de python-docx).

### Solución
Limpiar manualmente los registros corruptos de DynamoDB y S3.
