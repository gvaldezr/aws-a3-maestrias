# Reglas de Negocio — U1: Infraestructura Base + JSON Schema

---

## BR-01 — Unicidad del subject_id
Cada asignatura en una ejecución del pipeline tiene un `subject_id` único (UUID v4). No pueden existir dos registros activos con el mismo `subject_id`.

## BR-02 — Versionado del JSON en S3
Cada escritura al JSON de una asignatura genera una nueva versión en S3. El versionado de S3 debe estar habilitado. La versión más reciente es siempre la fuente de verdad.

## BR-03 — Inmutabilidad del historial de estados
El array `pipeline_state.state_history` es append-only. Ningún agente puede modificar o eliminar entradas previas del historial.

## BR-04 — Transiciones de estado válidas
Solo se permiten las siguientes transiciones de estado:

```
INGESTED → KNOWLEDGE_MATRIX_READY | RESEARCH_ESCALATED | FAILED
KNOWLEDGE_MATRIX_READY → DI_READY | DI_ALIGNMENT_GAP | FAILED
DI_READY → CONTENT_READY | CONTENT_QA_FAILED | FAILED
CONTENT_READY → PENDING_APPROVAL | QA_FAILED | FAILED
PENDING_APPROVAL → APPROVED | REJECTED
APPROVED → PUBLISHED | FAILED
REJECTED → CONTENT_READY (tras corrección del agente)
RESEARCH_ESCALATED → KNOWLEDGE_MATRIX_READY (tras intervención del Staff)
DI_ALIGNMENT_GAP → DI_READY (tras intervención del Staff)
QA_FAILED → CONTENT_READY (tras reintento exitoso)
```

Cualquier transición no listada es inválida y debe rechazarse con error.

## BR-05 — Cifrado obligatorio
Todo dato almacenado en S3 y DynamoDB debe estar cifrado en reposo (SSE-KMS). Toda comunicación debe usar TLS 1.2+. No se aceptan escrituras sin cifrado.

## BR-06 — Retención de logs mínima
Los CloudWatch Log Groups deben tener retención configurada en mínimo 90 días. No se permite retención indefinida sin justificación documentada.

## BR-07 — Secretos nunca en variables de entorno
Las credenciales (Scopus API Key, Canvas Token) deben almacenarse exclusivamente en AWS Secrets Manager. Ningún secreto puede aparecer en variables de entorno de Lambda, en el JSON de la asignatura, ni en logs de CloudWatch.

## BR-08 — Least-privilege por unidad
Cada unidad tiene su propio rol IAM con permisos mínimos necesarios. Ningún rol tiene acceso a recursos de otras unidades salvo los contratos de datos explícitamente definidos.

## BR-09 — Validación del esquema JSON
Antes de persistir el JSON de una asignatura, debe validarse contra el esquema v1.0. Un JSON inválido no puede ser escrito en S3 ni en DynamoDB.

## BR-10 — Índice DynamoDB consistente con S3
Toda escritura al JSON en S3 debe ir acompañada de una actualización del registro en DynamoDB. No puede existir un estado en DynamoDB que no tenga su JSON correspondiente en S3.
