# Patrones NFR — U1: Infraestructura Base + JSON Schema

---

## Patrón: Optimistic Locking en DynamoDB
Para evitar escrituras concurrentes que corrompan el estado de una asignatura, se usa `ConditionExpression` en cada `UpdateItem`:
```python
ConditionExpression="updated_at = :expected_updated_at"
```
Si la condición falla (otro agente actualizó primero), se reintenta con backoff exponencial.

## Patrón: Retry con Backoff Exponencial
Todas las operaciones S3 y DynamoDB usan el retry handler de boto3 con configuración explícita:
```python
config = Config(retries={"max_attempts": 3, "mode": "adaptive"})
```
Aplica a: `PutObject`, `GetObject`, `PutItem`, `UpdateItem`, `GetItem`.

## Patrón: Schema Validation Gate
Antes de toda escritura en S3, el JSON se valida contra el esquema v1.0. Si la validación falla, la operación se rechaza y se registra el error en CloudWatch con nivel ERROR. Nunca se escribe un JSON inválido.

## Patrón: Append-Only State History
El array `state_history` en el JSON nunca se modifica — solo se agregan entradas. Esto garantiza trazabilidad completa y permite auditoría forense del pipeline.

## Patrón: Envelope Encryption
Los datos en S3 y DynamoDB se cifran con una CMK de KMS. La clave KMS tiene política de acceso restringida a los roles IAM de las unidades del pipeline. La rotación automática de la CMK está habilitada (anual).

## Patrón: Structured Logging
Todos los logs siguen el formato JSON estructurado:
```json
{
  "timestamp": "ISO-8601",
  "level": "INFO|WARN|ERROR",
  "subject_id": "uuid",
  "operation": "save_subject_json|update_state|...",
  "result": "SUCCESS|FAILURE",
  "duration_ms": 42,
  "correlation_id": "uuid"
}
```
Nunca se loguean valores de secretos, tokens ni PII (SECURITY-03).
