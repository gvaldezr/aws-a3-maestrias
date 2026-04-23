# Security Test Instructions
## Pipeline Académico → Canvas LMS

Basado en extensión Security Baseline (SECURITY-01 a SECURITY-15) habilitada como restricción bloqueante.

---

## 1. Escaneo de Vulnerabilidades en Dependencias (SECURITY-10)

```bash
# Instalar pip-audit
pip install pip-audit

# Escanear dependencias Python
pip-audit --requirement requirements.txt --output json > security-results/dependency-audit.json

# Verificar que no hay vulnerabilidades críticas o altas
pip-audit --requirement requirements.txt --fail-on-severity high
```

**Criterio de aceptación**: 0 vulnerabilidades críticas o altas.

---

## 2. Verificación de Secretos en Código (SECURITY-12)

```bash
# Instalar detect-secrets
pip install detect-secrets

# Escanear el repositorio
detect-secrets scan --all-files > security-results/secrets-scan.json

# Verificar que no hay secretos hardcodeados
detect-secrets audit security-results/secrets-scan.json
```

**Criterio de aceptación**: 0 secretos detectados en código fuente.

---

## 3. Verificación de Headers HTTP (SECURITY-04)

```bash
# Invocar Lambda de upload y verificar headers de respuesta
aws lambda invoke \
  --function-name academic-pipeline-upload-handler-dev \
  --payload '{"body": "{\"file_name\": \"test.pdf\", \"file_size_bytes\": 1024, \"content_type\": \"application/pdf\"}"}' \
  /tmp/response.json

# Verificar headers requeridos
cat /tmp/response.json | jq '.headers'
```

**Headers requeridos**:
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self'`

---

## 4. Verificación de Cifrado (SECURITY-01)

```bash
# Verificar cifrado en S3
aws s3api get-bucket-encryption \
  --bucket academic-pipeline-subjects-${AWS_ACCOUNT_ID}-${AWS_REGION}-dev

# Verificar cifrado en DynamoDB
aws dynamodb describe-table \
  --table-name academic-pipeline-subjects-dev \
  --query "Table.SSEDescription"

# Verificar que S3 rechaza requests sin TLS
aws s3api get-bucket-policy \
  --bucket academic-pipeline-subjects-${AWS_ACCOUNT_ID}-${AWS_REGION}-dev \
  | jq '.Policy' | python3 -c "import sys,json; p=json.loads(json.load(sys.stdin)); print([s for s in p['Statement'] if 'SecureTransport' in str(s)])"
```

**Criterio de aceptación**: SSE-KMS habilitado, política de TLS obligatorio presente.

---

## 5. Verificación de IAM Least-Privilege (SECURITY-06)

```bash
# Verificar que los roles no tienen wildcards
aws iam get-role-policy \
  --role-name academic-pipeline-lambda-dev \
  --policy-name inline-policy 2>/dev/null || \
aws iam list-attached-role-policies \
  --role-name academic-pipeline-lambda-dev

# Usar IAM Access Analyzer para detectar permisos excesivos
aws accessanalyzer create-analyzer \
  --analyzer-name pipeline-analyzer \
  --type ACCOUNT
```

**Criterio de aceptación**: 0 políticas con wildcards en acciones o recursos.

---

## 6. Test de Autenticación (SECURITY-08, SECURITY-12)

```bash
# Intentar acceder al Dashboard sin token → debe retornar 401
curl -X GET "${API_GATEWAY_URL}/api/subjects" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

# Intentar con token inválido → debe retornar 401
curl -X GET "${API_GATEWAY_URL}/api/subjects" \
  -H "Authorization: Bearer invalid-token" \
  -w "\nHTTP Status: %{http_code}\n"
```

**Criterio de aceptación**: Ambas requests retornan HTTP 401.

---

## 7. Verificación de Logs sin Secretos (SECURITY-03)

```bash
# Buscar en CloudWatch Logs cualquier aparición de tokens o API keys
aws logs filter-log-events \
  --log-group-name "/academic-pipeline/dev/u2" \
  --filter-pattern "api_key OR oauth_token OR Bearer OR secret" \
  --query "events[].message"
```

**Criterio de aceptación**: 0 ocurrencias de credenciales en logs.

---

## 8. Verificación de Retención de Logs (SECURITY-14)

```bash
# Verificar retención de 90 días en todos los log groups
for unit in u1 u2 u3 u4 u5 u6 u7; do
  aws logs describe-log-groups \
    --log-group-name-prefix "/academic-pipeline/dev/${unit}" \
    --query "logGroups[].{name:logGroupName,retention:retentionInDays}"
done
```

**Criterio de aceptación**: Todos los log groups tienen `retentionInDays = 90`.
