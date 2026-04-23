# Unit Test Execution
## Pipeline Académico → Canvas LMS

---

## Ejecutar Todos los Tests Unitarios

```bash
# Activar entorno virtual
source .venv/bin/activate

# Ejecutar suite completa con cobertura
pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-report=html:coverage-report/

# Solo tests rápidos (sin CDK assertions)
pytest tests/unit/ -v -k "not stack" --tb=short
```

**Resultado esperado**: Todos los tests pasan, cobertura ≥ 80%.

---

## Tests por Unidad

### U1 — Infraestructura Base

```bash
pytest tests/unit/infrastructure/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_schema_validator.py | 10 | 3 | Esquema JSON v1.0, transiciones de estado |
| test_state_manager.py | 4 | 1 | save_subject_json, update_subject_state |
| test_logger.py | 5 | 2 | Redacción de secretos (SECURITY-03) |
| test_infrastructure_base_stack.py | 10 | 0 | CDK assertions (S3, DynamoDB, KMS, SNS) |

### U2 — Agente Scholar

```bash
pytest tests/unit/agents/scholar/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_keyword_generator.py | 6 | 2 | Keywords ≤ 10, sin stopwords |
| test_relevance_scorer.py | 5 | 2 | Score [0,1], Top 20 ≤ 20 |
| test_corpus_validator.py | 4 | 2 | Corpus insuficiente, paper_count |

### U3 — Agente DI

```bash
pytest tests/unit/agents/di/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_bloom_mapper.py | 9 | 2 | Verbos Bloom, mapeo a competencias |
| test_traceability.py | 8 | 2 | Matriz trazabilidad, coverage_ratio [0,1] |
| test_card_builder.py | 9 | 0 | Mapa 4 semanas, Carta Descriptiva V1 |

### U4 — Agente Content

```bash
pytest tests/unit/agents/content/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_apa_formatter.py | 6 | 2 | APA 7, bibliografía ordenada |
| test_coverage_checker.py | 8 | 2 | coverage_ratio [0,1], artefactos Maestría |

### U5 — QA Gate + Checkpoint

```bash
pytest tests/unit/qa-checkpoint/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_qa_gate.py | 12 | 2 | Validaciones RA, Bloom, Maestría, idempotencia |
| test_checkpoint.py | 9 | 0 | Aprobación, rechazo, edición manual |
| test_timeout_checker.py | 6 | 2 | is_past_timeout invariantes |

### U6 — Canvas Publisher

```bash
pytest tests/unit/canvas-publisher/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_formatters.py | 16 | 3 | Markdown→HTML, payloads Canvas API |

### U7 — Interfaz Web

```bash
pytest tests/unit/web-interface/ -v
```

| Archivo | Tests | PBT | Cubre |
|---|---|---|---|
| test_document_parser.py | 12 | 2 | Validación upload, parsing documentos |

---

## Resumen de Tests Unitarios

| Unidad | Tests Unitarios | Tests PBT | Total |
|---|---|---|---|
| U1 | 29 | 6 | 35 |
| U2 | 15 | 6 | 21 |
| U3 | 26 | 4 | 30 |
| U4 | 14 | 4 | 18 |
| U5 | 27 | 4 | 31 |
| U6 | 16 | 3 | 19 |
| U7 | 12 | 2 | 14 |
| **Total** | **139** | **29** | **168** |

---

## Ejecutar Solo Tests PBT

```bash
# PBT con semilla fija para reproducibilidad (PBT-08)
pytest tests/unit/ -v -k "PBT" --hypothesis-seed=12345

# PBT con logging de semilla en CI
pytest tests/unit/ -v -k "PBT" --hypothesis-show-statistics
```

---

## Cobertura Mínima Requerida

```bash
# Verificar cobertura ≥ 80% (configurado en pyproject.toml)
pytest tests/unit/ --cov=src --cov-fail-under=80
```

Si la cobertura falla:
1. Revisar el reporte en `coverage-report/index.html`
2. Identificar módulos con cobertura baja
3. Agregar tests para los casos no cubiertos
