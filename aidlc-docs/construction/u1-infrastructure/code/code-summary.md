# Resumen de Código — U1: Infraestructura Base + JSON Schema

## Archivos Creados

### Configuración del Proyecto
- `pyproject.toml` — dependencias pinadas, configuración pytest y coverage
- `app.py` — CDK App entry point

### Esquema JSON (C9 — StateManagementComponent)
- `src/infrastructure/schema/subject_schema_v1.py` — esquema JSON v1.0 + transiciones de estado válidas
- `src/infrastructure/schema/schema_validator.py` — validador (validate_subject_json, is_valid_state_transition)

### Gestión de Estado (C9)
- `src/infrastructure/state/models.py` — SubjectState enum, StateMetadata, SubjectSummary, S3Reference
- `src/infrastructure/state/state_manager.py` — save_subject_json, update_subject_state, get_subject_json, list_subjects_by_state

### Observabilidad (C10)
- `src/infrastructure/observability/logger.py` — StructuredLogger con redacción de secretos (SECURITY-03)
- `src/infrastructure/observability/metrics.py` — record_metric, send_notification

### CDK Stack
- `src/infrastructure/stacks/infrastructure_base_stack.py` — InfrastructureBaseStack (KMS, S3, DynamoDB, Secrets Manager, SNS, CloudWatch, IAM)

### Tests
- `tests/unit/infrastructure/test_schema_validator.py` — 10 tests unitarios + 3 PBT (PBT-02, PBT-03)
- `tests/unit/infrastructure/test_state_manager.py` — 4 tests unitarios + 1 PBT round-trip (PBT-02)
- `tests/unit/infrastructure/test_logger.py` — 5 tests unitarios + 2 PBT (PBT-03)
- `tests/unit/infrastructure/test_infrastructure_base_stack.py` — 10 CDK assertion tests

## Cobertura de Stories
- US-16 (Auditoría): CloudWatch Log Groups con retención 90 días, roles IAM sin permisos de borrado de logs, structured logger sin secretos

## Cumplimiento de Extensiones
- SECURITY-01: S3 SSE-KMS + enforce_ssl, DynamoDB SSE-KMS ✅
- SECURITY-03: StructuredLogger con redacción de secretos ✅
- SECURITY-06: IAM least-privilege por unidad, sin wildcards ✅
- SECURITY-09: S3 Block Public Access habilitado ✅
- SECURITY-12: Secrets Manager para credenciales, sin hardcoding ✅
- SECURITY-14: CloudWatch Log Groups retención 90 días, roles sin permisos de borrado ✅
- PBT-02: Round-trip JSON serialization test ✅
- PBT-03: Invariants para validación de esquema y redacción de secretos ✅
- PBT-09: Hypothesis como framework PBT ✅
