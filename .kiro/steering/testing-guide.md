---
inclusion: auto
---

# Guía de Testing — Pipeline Académico

## Framework y ejecución

- **Framework**: pytest 9.x
- **Ejecutar todos los tests**: `python -m pytest tests/ -q`
- **Tests unitarios**: `python -m pytest tests/unit/ -q`
- **Test específico**: `python -m pytest tests/unit/infrastructure/test_state_manager.py -q`
- **Con coverage**: `python -m pytest tests/ --cov=src --cov-report=term-missing`
- **Estado actual**: 191 tests passing, ~26% coverage

## Estructura de tests

```
tests/
├── unit/
│   ├── agents/
│   │   ├── scholar/          # Tests del agente Scholar
│   │   ├── di/               # Tests del agente DI
│   │   └── content/          # Tests del agente Content
│   ├── infrastructure/       # Schema validator, state manager, logger
│   ├── canvas-publisher/     # Formatters, publisher
│   ├── qa-checkpoint/        # QA gate, checkpoint, timeout
│   └── web-interface/        # Document parser
├── integration/              # Tests entre unidades
└── e2e_test.py               # Test end-to-end
```

## Convenciones de tests

### Naming
- Archivos: `test_{module}.py`
- Funciones: `test_{behavior}_when_{condition}` o `test_{method}_{scenario}`
- Clases (opcional): `TestClassName` agrupando tests relacionados

### Mocking
- **AWS services**: Usar `moto` o `unittest.mock.patch` para S3, DynamoDB, Secrets Manager
- **LLM calls**: Mockear `strands.Agent.__call__` o las tools individuales
- **APIs externas**: Mockear `httpx.Client` para Scopus, Canvas API
- **Nunca** hacer llamadas reales a AWS, Scopus, Canvas o LLMs en tests unitarios

### Fixtures comunes
- `subject_json`: Subject JSON completo de ejemplo con todos los campos
- `s3_client` / `dynamodb_table`: Clientes mockeados con moto
- `env_vars`: Variables de entorno necesarias (SUBJECTS_BUCKET_NAME, SUBJECTS_TABLE_NAME)

## Property-Based Testing (PBT)

La extensión PBT está habilitada en modo **Full** (bloqueante). Usar Hypothesis:

```python
from hypothesis import given, strategies as st

@given(subject_name=st.text(min_size=1, max_size=255))
def test_metadata_accepts_valid_names(subject_name):
    ...
```

### Dónde aplicar PBT
- Schema validation (subject_schema_v1)
- State transitions (VALID_STATE_TRANSITIONS)
- Bloom mapper (verb selection, competency matching)
- APA formatter (bibliographic formatting)
- Document parser (table extraction)

## Extensión Security Baseline

Habilitada como **bloqueante**. Los tests deben verificar:
- No hay secretos hardcodeados en código
- Redacción de campos sensibles en logs
- Validación de inputs (subject_id, payloads)
- IAM least-privilege en CDK stacks

## Scripts de verificación de datos

```bash
# Verificar estado de un subject JSON
python test-data/check_subject.py /tmp/subject.json

# Verificar calidad del contenido generado
python test-data/check_new_content.py /tmp/subject.json

# Mostrar tamaños de lecturas
python test-data/show_readings.py /tmp/subject.json
```

## Qué NO testear en unitarios
- Llamadas reales a Bedrock/LLM (son no-deterministas)
- APIs externas reales (Scopus, Canvas, OpenAlex)
- Despliegue de CDK stacks
- Frontend React (usar tests separados con vitest si se necesitan)
