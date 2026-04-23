# NFR Requirements — U1: Infraestructura Base + JSON Schema

---

## Escalabilidad
- S3 y DynamoDB escalan automáticamente — sin límite de capacidad provisionada fija
- DynamoDB en modo On-Demand (pay-per-request) para absorber picos de 20 asignaturas paralelas sin degradación
- El esquema JSON debe soportar evolución backward-compatible (nuevos campos opcionales, sin eliminar campos existentes)

## Rendimiento
- Lectura del JSON desde S3: latencia < 200ms (p99) para objetos < 1MB
- Escritura/actualización en DynamoDB: latencia < 10ms (p99)
- Consultas por estado (GSI-1): latencia < 50ms (p99)

## Disponibilidad
- S3: SLA 99.99% — multi-AZ por defecto
- DynamoDB: SLA 99.999% — multi-AZ por defecto
- Secrets Manager: SLA 99.99%
- No se requiere configuración adicional de HA — los servicios administrados la proveen

## Seguridad (SECURITY-01, SECURITY-06, SECURITY-07, SECURITY-12)
- Cifrado en reposo: SSE-KMS en S3 y DynamoDB (SECURITY-01)
- Cifrado en tránsito: TLS 1.2+ en todas las operaciones (SECURITY-01)
- S3 Block Public Access habilitado — sin acceso público (SECURITY-09)
- IAM least-privilege por unidad — sin wildcards en acciones ni recursos (SECURITY-06)
- Secrets Manager para todas las credenciales — sin hardcoding (SECURITY-12)
- VPC Endpoints para S3 y DynamoDB (tráfico interno sin salir a internet) (SECURITY-07)

## Observabilidad (SECURITY-03, SECURITY-14)
- CloudWatch Logs con retención mínima 90 días (SECURITY-14)
- Métricas de DynamoDB: ConsumedReadCapacityUnits, ConsumedWriteCapacityUnits, ThrottledRequests
- Métricas de S3: NumberOfObjects, BucketSizeBytes
- Alarmas SNS para: ThrottledRequests > 0, errores de escritura en DynamoDB
- Logs estructurados con campos: timestamp, subject_id, operation, result, duration_ms (SECURITY-03)

## Resiliencia
- Reintentos automáticos en operaciones S3/DynamoDB con backoff exponencial (máx. 3 intentos)
- Validación del esquema JSON antes de toda escritura — falla rápido ante datos inválidos
- Versionado S3 habilitado — permite recuperación ante escrituras erróneas

## Mantenibilidad
- Esquema JSON versionado (campo `schema_version`) para migraciones futuras
- IaC 100% en CDK Python — sin recursos creados manualmente
- Tags obligatorios en todos los recursos: `Project`, `Unit`, `Environment`
