# NFR Requirements — U3: Agente DI

## Rendimiento
- Tiempo máximo por asignatura: 4 minutos (Bedrock Agent timeout: 240s)
- Temperatura LLM: 0 para garantizar idempotencia (BR-DI08)

## Seguridad
- IAM least-privilege: rol del agente solo accede a S3/DynamoDB de la asignatura (SECURITY-06)
- Logs sin datos de competencias sensibles ni PII (SECURITY-03)

## Resiliencia
- Idempotencia: misma entrada → mismo resultado con temperatura 0 (BR-DI08)
- Si el agente falla, el estado permanece en `KNOWLEDGE_MATRIX_READY` para reintento

## Observabilidad
- Métrica: `AlignmentGapsDetected`, `ObjectivesGenerated`, `DIExecutionDuration`
- Alarma SNS si `AlignmentGapsDetected > 0`

## PBT
- Invariantes clave: bloom_level siempre en enum válido, traceability_matrix cubre todos los RA, score de cobertura en [0, 1]
