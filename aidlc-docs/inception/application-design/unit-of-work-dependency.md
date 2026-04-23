# Dependencias entre Unidades de Trabajo
## Pipeline Académico → Canvas LMS

---

## Matriz de Dependencias

| Unidad | Depende de | Tipo de dependencia |
|---|---|---|
| U1 — Infraestructura Base | Ninguna | — |
| U2 — Agente Scholar | U1 | JSON schema, S3, DynamoDB, Secrets Manager, SNS |
| U3 — Agente DI | U1, U2 | JSON con Matriz de Conocimiento (estado KNOWLEDGE_MATRIX_READY) |
| U4 — Agente Content | U1, U3 | JSON con Carta Descriptiva V1 (estado DI_READY) |
| U5 — QA Gate + Checkpoint | U1, U4 | JSON con paquete de contenido (estado CONTENT_READY) |
| U6 — Publicación Canvas | U1, U5 | JSON con estado APPROVED + Secrets Manager (Canvas Token) |
| U7 — Interfaz Web | U1, U5, U6 | DynamoDB (estado), API Gateway, URLs Canvas (confirmación) |

---

## Secuencia de Desarrollo Recomendada

```
U1 (Infraestructura Base)
    |
    +--> U2 (Scholar)  +--> U3 (DI)  +--> U4 (Content)  +--> U5 (QA+Checkpoint)
                                                                    |
                                                               +--> U6 (Canvas)
                                                               +--> U7 (Web)
```

**Ruta crítica**: U1 → U2 → U3 → U4 → U5 → U6

U7 puede desarrollarse en paralelo con U2–U4 una vez que U1 y U5 estén disponibles (U7 depende del contrato de API del checkpoint, no de la implementación completa de los agentes).

---

## Contratos de Datos entre Unidades

| Productor | Consumidor | Contrato |
|---|---|---|
| U1 | Todos | Esquema JSON de asignatura (versión 1.0) |
| U2 | U3 | JSON con `top20_papers` + `knowledge_matrix` + estado `KNOWLEDGE_MATRIX_READY` |
| U3 | U4 | JSON con `descriptive_card` + `traceability_matrix` + estado `DI_READY` |
| U4 | U5 | JSON con `content_package` (incluyendo 4 artefactos Maestría) + estado `CONTENT_READY` |
| U5 | U6 | JSON con estado `APPROVED` + `qa_report` + `approval_metadata` |
| U5 | U7 | API REST: `GET /subjects/{id}/checkpoint`, `POST /subjects/{id}/decision` |
| U6 | U7 | JSON con `canvas_urls` + estado `PUBLISHED` |

---

## Estrategia de Testing por Dependencia

| Dependencia | Estrategia de test |
|---|---|
| U2 → Scopus API | Test de contrato con mock de Scopus (respuestas Q1/Q2 simuladas) |
| U6 → Canvas API | Test de contrato con mock de Canvas API (sandbox Canvas si disponible) |
| U2 → U3 | Test de integración: Scholar produce JSON válido que DI puede consumir |
| U3 → U4 | Test de integración: DI produce Carta Descriptiva que Content puede expandir |
| U4 → U5 | Test de integración: Content produce paquete que QA Gate puede validar |
| U5 → U6 | Test de integración: QA Gate aprueba y Canvas Publisher publica correctamente |
| U5 → U7 | Test de integración: Checkpoint API responde correctamente a decisiones del Staff |

---

## Riesgos de Dependencia

| Riesgo | Unidades afectadas | Mitigación |
|---|---|---|
| Scopus API no disponible | U2 | Mock de Scopus para desarrollo; circuit breaker en producción |
| Canvas API cambia contrato | U6 | Tests de contrato automatizados; versionar la integración |
| Esquema JSON evoluciona | Todas | Versionado del esquema en U1; migraciones backward-compatible |
| Latencia de Bedrock Agents | U2, U3, U4 | Timeouts configurables; reintentos con backoff exponencial |
