# NFR Requirements — U4: Agente Content

## Rendimiento
- Tiempo máximo por asignatura: 8 minutos (paquete completo con 4 artefactos Maestría)
- AgentCore Runtime timeout: 480s
- Modelo: Claude Sonnet para DI/Maestría artifacts, Claude Haiku para quizzes/lecturas (costo)

## Resiliencia
- Reintentos automáticos con prompt diferente (máx. 3) ante cobertura incompleta de RA (BR-C05, BR-C06)
- Si falla tras 3 intentos: estado CONTENT_QA_FAILED + notificación SNS

## Seguridad
- IAM least-privilege: solo acceso a S3/DynamoDB de la asignatura (SECURITY-06)
- Logs sin contenido de competencias sensibles ni PII (SECURITY-03)

## Observabilidad
- Métricas: `ContentPackageGenerated`, `MaestriaArtifactsGenerated`, `ContentRetries`, `ContentEscalations`
- Alarma SNS si `ContentEscalations > 0`

## PBT
- Invariantes: apa_bibliography siempre lista de strings, quiz siempre >= 3 preguntas por RA, coverage_ratio en [0,1]
