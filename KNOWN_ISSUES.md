# Known Issues — Pipeline Académico → Canvas LMS

## Resueltos

### Issue 1: Agentes no reciben contexto académico ✅
**Resuelto**: Cada agente carga el subject JSON de S3 via `_load_subject_context()` y construye prompts con syllabus, competencias, RAs y papers reales.

### Issue 2: MaxTokensReachedException en DI y Content ✅
**Resuelto**: `max_tokens` aumentado a 16384, prompts compactados, system prompts simplificados.

### Issue 3: TypeError string indices en Content tools ✅
**Resuelto**: `_ensure_dicts()` convierte strings JSON a dicts en los 3 tools del Content agent.

### Issue 4: Auto-persistencia falla (permisos IAM) ✅
**Resuelto**: Policy `AcademicPipelineDataAccess` agregada a los 3 roles de AgentCore Runtime con S3, DynamoDB, KMS y Secrets Manager.

### Issue 5: Estado regresa de PENDING_APPROVAL a CONTENT_READY ✅
**Resuelto**: Los 3 agentes verifican el estado actual antes de escribir — no regresan estados avanzados.

### Issue 6: QA Report no se persiste en S3 ✅
**Resuelto**: QA Gate usa `_save_json_direct()` para guardar qa_report sin pasar por el schema validator.

### Issue 7: DOCX parser no extrae datos de tablas ✅
**Resuelto**: `_extract_docx()` lee tablas además de párrafos. Parser reconoce formato Anáhuac (Denominación, Fines de aprendizaje, Contenido temático).

### Issue 8: CORS en API Gateway ✅
**Resuelto**: Gateway Responses para DEFAULT_4XX y DEFAULT_5XX con CORS headers. Frontend usa IdToken (no AccessToken).

### Issue 9: Canvas Publisher import error (httpx/tenacity) ✅
**Resuelto**: `canvas_client.py` usa import lazy de httpx dentro de `_request()`. Eliminada dependencia de tenacity.

---

## Pendientes

### Issue 10: Registros de prueba en DynamoDB
**Severidad**: Baja
**Descripción**: Hay ~18 registros de pruebas anteriores en DynamoDB que aparecen en el dashboard.
**Solución**: Limpiar manualmente los registros con `aws dynamodb delete-item`.

### Issue 11: Test coverage 26%
**Severidad**: Media
**Descripción**: 191 tests pasan pero la cobertura es 26% (muchos Lambda handlers sin tests unitarios).
**Solución**: Agregar tests para ingestion_handler, dashboard_handler, checkpoint, canvas_publisher.

### Issue 12: Procesamiento paralelo no implementado (RF-09)
**Severidad**: Baja (funcional para 1 asignatura a la vez)
**Descripción**: Step Functions procesa 1 asignatura por ejecución. Para paralelo, necesita Map state.

### Issue 13: Notificaciones SNS no configuradas (RF-11)
**Severidad**: Baja
**Descripción**: Los topics SNS existen pero no tienen suscriptores. No hay alarmas CloudWatch.

### Issue 14: Infrastructure test expects 2 secrets, finds 3
**Severidad**: Baja
**Descripción**: `test_secrets_manager_secrets_created` espera 2 secrets pero hay 3 (se agregó Canvas token).
**Solución**: Actualizar el test a `resource_count_is("AWS::SecretsManager::Secret", 3)`.
