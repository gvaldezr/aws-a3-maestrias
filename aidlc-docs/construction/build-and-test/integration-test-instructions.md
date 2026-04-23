# Integration Test Instructions
## Pipeline Académico → Canvas LMS

---

## Propósito
Validar que las unidades interactúan correctamente entre sí a través de los contratos de datos definidos (JSON de fuente única de verdad).

---

## Configuración del Entorno de Integración

```bash
# Usar moto para simular AWS localmente
pip install "moto[s3,dynamodb,secretsmanager,sns,kms]"

# Variables de entorno para tests de integración
export SUBJECTS_BUCKET_NAME=test-subjects-bucket
export SUBJECTS_TABLE_NAME=test-subjects-table
export SCOPUS_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:test-scopus
export CANVAS_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:test-canvas
export STAFF_NOTIFICATIONS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:test-staff
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=testing
export AWS_SECRET_ACCESS_KEY=testing
```

---

## Escenario 1: U1 → U2 (Ingesta → Scholar)

**Descripción**: El JSON inicial creado por U1 es consumido correctamente por el Agente Scholar.

```bash
pytest tests/integration/test_u1_u2_integration.py -v
```

**Pasos**:
1. Crear JSON inicial con estado `INGESTED` usando `save_subject_json`
2. Verificar que el JSON es válido contra el esquema v1.0
3. Verificar que `validate_corpus` puede procesar los `learning_outcomes` del JSON
4. Verificar que `generate_search_keywords` produce keywords desde los RA y competencias

**Resultado esperado**: JSON válido → keywords generadas → corpus validable.

---

## Escenario 2: U2 → U3 (Scholar → DI)

**Descripción**: El JSON enriquecido por Scholar (con `knowledge_matrix`) es consumido por el Agente DI.

```bash
pytest tests/integration/test_u2_u3_integration.py -v
```

**Pasos**:
1. Crear JSON con `knowledge_matrix` y `top20_papers` (estado `KNOWLEDGE_MATRIX_READY`)
2. Verificar que `build_content_map` procesa la `knowledge_matrix`
3. Verificar que `generate_learning_objectives` produce objetivos con Bloom y competencias
4. Verificar que `build_traceability_matrix` cubre todos los RA

**Resultado esperado**: Carta Descriptiva V1 generada con trazabilidad completa.

---

## Escenario 3: U3 → U4 (DI → Content)

**Descripción**: La Carta Descriptiva V1 del Agente DI alimenta al Agente Content.

```bash
pytest tests/integration/test_u3_u4_integration.py -v
```

**Pasos**:
1. Crear JSON con `descriptive_card` y `learning_objectives` (estado `DI_READY`)
2. Verificar que `check_ra_coverage` puede evaluar quizzes contra los RA del JSON
3. Para Maestría: verificar que `check_maestria_artifacts_complete` valida los 4 artefactos
4. Verificar que `generate_apa_bibliography` procesa `top20_papers` del JSON

**Resultado esperado**: ContentPackage completo con cobertura 100% de RA.

---

## Escenario 4: U4 → U5 (Content → QA Gate)

**Descripción**: El paquete de contenido es validado por el QA Gate.

```bash
pytest tests/integration/test_u4_u5_integration.py -v
```

**Pasos**:
1. Crear JSON con `content_package` completo (estado `CONTENT_READY`)
2. Ejecutar `run_qa_gate` sobre el JSON
3. Verificar que el QA Gate detecta gaps correctamente
4. Verificar que el QA Gate pasa cuando el contenido es completo

**Resultado esperado**: QA Gate PASS → estado `PENDING_APPROVAL`.

---

## Escenario 5: U5 → U6 (Checkpoint → Canvas)

**Descripción**: El contenido aprobado es publicado en Canvas.

```bash
pytest tests/integration/test_u5_u6_integration.py -v
```

**Pasos** (con mock de Canvas API):
1. Crear JSON con estado `APPROVED`
2. Mockear Canvas API con respuestas válidas
3. Ejecutar `publish_course` con el CanvasClient mockeado
4. Verificar que el JSON se actualiza con `canvas_course_url` y estado `PUBLISHED`

**Resultado esperado**: Curso publicado en Canvas con todos los recursos.

---

## Escenario 6: U7 → U1 (Upload → Ingesta)

**Descripción**: La carga de un documento dispara correctamente la ingesta.

```bash
pytest tests/integration/test_u7_u1_integration.py -v
```

**Pasos**:
1. Simular evento S3 PutObject con un documento de prueba
2. Ejecutar `ingestion_handler.lambda_handler` con el evento
3. Verificar que el JSON inicial se crea en S3 (moto)
4. Verificar que el estado `INGESTED` se registra en DynamoDB (moto)

**Resultado esperado**: JSON inicial válido creado en S3 + DynamoDB.

---

## Escenario 7: Pipeline Completo End-to-End (Smoke Test)

**Descripción**: Flujo completo desde ingesta hasta QA Gate con datos de prueba.

```bash
pytest tests/integration/test_pipeline_e2e.py -v -k "smoke"
```

**Pasos**:
1. Crear documento de prueba con RA y competencias
2. Parsear con `parse_text_to_document`
3. Crear JSON inicial y persistir
4. Ejecutar validaciones de Scholar (keywords + corpus mock)
5. Ejecutar DI (objetivos + trazabilidad)
6. Ejecutar Content (quizzes + artefactos Maestría)
7. Ejecutar QA Gate
8. Verificar estado final `PENDING_APPROVAL`

**Resultado esperado**: Pipeline completo sin errores, estado `PENDING_APPROVAL`.

---

## Ejecutar Todos los Tests de Integración

```bash
pytest tests/integration/ -v --tb=short -x
```

---

## Tests de Contrato — APIs Externas

### Contrato Scopus API

```bash
pytest tests/integration/test_scopus_contract.py -v
```

Valida que el mock de Scopus retorna la estructura esperada por `ScholarAgent`:
- `dc:identifier`, `dc:title`, `dc:creator`, `prism:publicationName`, `prism:coverDate`

### Contrato Canvas API

```bash
pytest tests/integration/test_canvas_contract.py -v
```

Valida que el mock de Canvas retorna la estructura esperada por `CanvasClient`:
- `id`, `html_url` en respuestas de course, module, page, quiz
