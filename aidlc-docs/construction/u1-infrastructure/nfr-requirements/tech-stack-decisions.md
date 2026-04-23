# Decisiones de Stack Tecnológico — U1: Infraestructura Base + JSON Schema

| Componente | Tecnología elegida | Alternativas consideradas | Justificación |
|---|---|---|---|
| Almacenamiento JSON | Amazon S3 (versionado + SSE-KMS) | DynamoDB (solo), EFS | S3 es ideal para objetos JSON grandes con versionado nativo; costo mínimo |
| Índice de estado | Amazon DynamoDB (On-Demand) | RDS PostgreSQL, ElastiCache | Latencia < 10ms, escala automática, sin gestión de servidor |
| Gestión de secretos | AWS Secrets Manager | SSM Parameter Store | Rotación automática, auditoría nativa, integración con IAM |
| Cifrado | AWS KMS (CMK) | SSE-S3 | Control de acceso granular a la clave; auditoría en CloudTrail |
| IaC | AWS CDK (Python) | CloudFormation YAML, Terraform | Tipado, reutilización de código, integración con tests unitarios de infraestructura |
| Logging | Amazon CloudWatch Logs | ELK Stack, Datadog | Nativo AWS, sin infraestructura adicional, integración con alarmas SNS |
| Notificaciones | Amazon SNS | SQS, EventBridge | Simple, bajo costo, soporte multi-protocolo (email, HTTP, Lambda) |
| Validación JSON | jsonschema (Python) | Pydantic, marshmallow | Estándar JSON Schema, sin dependencias de framework |
| PBT Framework | Hypothesis (Python) | pytest-quickcheck | Maduro, excelente shrinking, integración con pytest (PBT-09) |
