# Modelo de Lógica de Negocio — U1: Infraestructura Base + JSON Schema

---

## Responsabilidades Funcionales

### 1. Gestión del JSON de Fuente Única de Verdad

**save_subject_json(subject_json)**
1. Validar el JSON contra el esquema v1.0 (rechazar si inválido)
2. Calcular hash SHA-256 del contenido
3. Escribir en S3 con clave `subjects/{subject_id}/subject.json` (versionado habilitado)
4. Retornar la referencia S3 (bucket, key, version_id)

**update_subject_state(subject_id, new_state, agent, llm_version)**
1. Validar que la transición de estado es válida (BR-04)
2. Leer el JSON actual desde S3
3. Agregar entrada al `state_history` (append-only, BR-03)
4. Actualizar `pipeline_state.current_state`
5. Actualizar `updated_at`
6. Escribir JSON actualizado en S3
7. Actualizar registro en DynamoDB (BR-10)

**get_subject_json(subject_id)**
1. Consultar DynamoDB para obtener el `s3_key` del subject
2. Leer la versión más reciente del JSON desde S3
3. Retornar el objeto deserializado

### 2. Gestión del Índice de Estado (DynamoDB)

**upsert_state_record(subject_id, state, metadata)**
1. Construir el registro con PK=subject_id, SK="STATE"
2. Actualizar atributos: current_state, updated_at, s3_key, retry_count
3. Escribir en DynamoDB con condición de consistencia

**list_subjects_by_state(state)**
1. Consultar GSI-1 (state-index) con PK=state
2. Retornar lista de SubjectSummary ordenada por updated_at desc

### 3. Validación del Esquema JSON

**validate_subject_json(subject_json)**
1. Cargar el esquema JSON v1.0 desde S3 (o memoria caché)
2. Ejecutar validación con jsonschema
3. Retornar lista de errores de validación (vacía si válido)
4. Rechazar escritura si hay errores (BR-09)

### 4. Inicialización de Infraestructura (CDK)

El stack CDK de U1 provisiona en orden:
1. KMS Key para cifrado de S3 y DynamoDB
2. S3 Bucket con versionado, cifrado SSE-KMS y bloqueo de acceso público
3. DynamoDB Table con GSI-1 y GSI-2, cifrado SSE-KMS
4. Secrets Manager secrets (Scopus API Key, Canvas Token) — valores vacíos, a rellenar manualmente
5. CloudWatch Log Groups con retención de 90 días
6. SNS Topics para notificaciones del pipeline
7. IAM Roles base por unidad con least-privilege
