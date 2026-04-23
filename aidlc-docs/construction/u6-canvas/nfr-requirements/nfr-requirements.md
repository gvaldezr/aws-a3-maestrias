# NFR Requirements — U6: Publicación Canvas LMS

## Rendimiento
- Tiempo máximo de publicación por asignatura: 5 minutos
- Lambda timeout: 300s; memory: 512MB (operaciones HTTP múltiples)

## Resiliencia
- Backoff exponencial ante errores Canvas API 5xx/timeout (BR-CV06): 1s, 2s, 4s
- Idempotencia: verificar curso existente antes de crear (BR-CV09)
- Si falla tras 3 reintentos: estado FAILED + notificación SNS

## Seguridad
- OAuth Token exclusivamente desde Secrets Manager (BR-CV07, SECURITY-12)
- TLS 1.2+ en todas las llamadas a Canvas API (SECURITY-01)
- IAM least-privilege: Lambda solo puede leer el secreto de Canvas y leer/escribir S3/DynamoDB (SECURITY-06)
- Logs sin tokens ni credenciales (SECURITY-03)

## Observabilidad
- Métricas: `CoursesPublished`, `PublicationErrors`, `CanvasAPILatency`
- Alarma SNS si `PublicationErrors > 0`
