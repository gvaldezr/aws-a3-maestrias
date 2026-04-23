# NFR Requirements — U2: Agente Scholar

## Rendimiento
- Tiempo máximo de ejecución por asignatura: 5 minutos (incluyendo llamadas a Scopus)
- Lambda timeout: 300s; Bedrock Agent timeout: 300s
- Scopus API: máx. 3 llamadas por asignatura con rate limiting (BR-S06)

## Escalabilidad
- Hasta 20 ejecuciones paralelas (una por asignatura); cada una es una invocación independiente de Bedrock Agent
- Sin estado compartido entre ejecuciones — cada agente lee/escribe su propio JSON en S3

## Seguridad (SECURITY-01, SECURITY-06, SECURITY-09, SECURITY-12)
- API Key de Scopus exclusivamente desde Secrets Manager (SECURITY-12)
- IAM least-privilege: el rol del agente solo puede leer el secreto de Scopus y leer/escribir en S3/DynamoDB (SECURITY-06)
- Logs sin API Keys ni valores de secretos (SECURITY-03)
- TLS 1.2+ en todas las llamadas a Scopus API (SECURITY-01)

## Resiliencia
- Backoff exponencial ante errores de Scopus API (429, 5xx): 1s, 2s, 4s (BR-S06)
- Circuit breaker: si Scopus falla 3 veces consecutivas, escalar al Staff (BR-S07)
- Idempotencia: re-ejecutar el agente con el mismo subject_id produce el mismo resultado si el JSON no ha cambiado

## Observabilidad (SECURITY-03, SECURITY-14)
- Log estructurado por cada llamada a Scopus: keywords, resultados, duración
- Métrica CloudWatch: `ScopusSearchDuration`, `PapersRetrieved`, `CorpusEscalations`
- Alarma SNS si `CorpusEscalations > 0` en una ventana de 1 hora
