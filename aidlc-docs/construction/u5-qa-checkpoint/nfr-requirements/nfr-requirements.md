# NFR Requirements — U5: QA Gate + Checkpoint Humano

## Seguridad
- Toda decisión del Staff requiere JWT válido (Cognito) — sin aprobaciones anónimas (SECURITY-08)
- El campo `decided_by` se extrae del JWT, no del payload del request
- Logs de decisiones sin PII más allá del username (SECURITY-03)
- Roles IAM: Lambda de QA Gate solo puede leer/escribir S3 y DynamoDB de la asignatura (SECURITY-06)

## Resiliencia
- El QA Gate es idempotente: re-ejecutarlo con el mismo JSON produce el mismo resultado
- Si la notificación SNS falla, se reintenta 3 veces con backoff exponencial

## Observabilidad
- Métricas: `QAGatePassed`, `QAGateFailed`, `ApprovalsReceived`, `RejectionsReceived`, `TimeoutReminders`
- Alarma SNS si `QAGateFailed > 0` o `TimeoutReminders > 0`
- Log de cada decisión con: subject_id, decision, decided_by, timestamp (SECURITY-14)

## Disponibilidad
- Lambda timeout: 30s para QA Gate (operación rápida, sin LLM)
- EventBridge Scheduler para el check de timeout de 48h (no polling)
