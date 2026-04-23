# Plan de Ejecución
## Pipeline Académico → Canvas LMS con Agent Core Framework

---

## Análisis de Impacto

### Evaluación de Cambios
- **Cambios orientados al usuario**: Sí — interfaz web para Staff de Tecnología Educativa (carga, monitoreo, checkpoint de validación)
- **Cambios estructurales**: Sí — sistema multi-agente nuevo con 5 fases de procesamiento
- **Cambios en modelo de datos**: Sí — JSON de fuente única de verdad con esquema enriquecido progresivamente; DynamoDB como índice de estado
- **Cambios en APIs**: Sí — integraciones con Scopus API, Canvas LMS API REST, Amazon Bedrock Agents
- **Impacto en NFRs**: Alto — seguridad (credenciales, autenticación, cifrado), escalabilidad (20 asignaturas paralelas), resiliencia (reintentos, backoff), observabilidad (CloudWatch, SNS)

### Evaluación de Riesgo
- **Nivel de riesgo**: Alto
- **Complejidad de rollback**: Moderada (arquitectura serverless, sin estado en cómputo)
- **Complejidad de testing**: Alta (3 agentes de IA, 2 APIs externas, flujos de aprobación humana)
- **Factores de riesgo principales**:
  - Dependencia de APIs externas (Scopus rate limiting, Canvas API availability)
  - Calidad no determinista de salidas de LLM (requiere QA Gate robusto)
  - Flujo de aprobación humana con timeout (estado persistente en DynamoDB)
  - Seguridad de credenciales en entorno multi-agente

---

## Visualización del Flujo de Trabajo

```
INCEPTION PHASE
+---------------------------+
| Workspace Detection  [OK] |
| Reverse Engineering  [--] |  <- SKIP (Greenfield)
| Requirements Analysis[OK] |
| User Stories         [OK] |
| Workflow Planning    [>>] |  <- EN PROGRESO
| Application Design   [EX] |  <- EXECUTE
| Units Generation     [EX] |  <- EXECUTE
+---------------------------+
            |
CONSTRUCTION PHASE (por unidad)
+---------------------------+
| Functional Design    [EX] |  <- EXECUTE
| NFR Requirements     [EX] |  <- EXECUTE
| NFR Design           [EX] |  <- EXECUTE
| Infrastructure Design[EX] |  <- EXECUTE
| Code Generation      [EX] |  <- EXECUTE (siempre)
+---------------------------+
            |
+---------------------------+
| Build and Test       [EX] |  <- EXECUTE (siempre)
+---------------------------+
            |
OPERATIONS PHASE
+---------------------------+
| Operations      [PENDING] |  <- PLACEHOLDER
+---------------------------+
```

---

## Fases a Ejecutar

### FASE DE INCEPTION

- [x] Workspace Detection — COMPLETADO
- [x] Reverse Engineering — OMITIDO (proyecto Greenfield)
- [x] Requirements Analysis — COMPLETADO
- [x] User Stories — COMPLETADO
- [x] Workflow Planning — EN PROGRESO

- [ ] **Application Design — EJECUTAR**
  - Rationale: El sistema requiere definir 5 componentes nuevos (Agente Scholar, Agente DI, Agente Content, Action Groups de Canvas, Interfaz Web), sus métodos, contratos de datos y dependencias entre sí. La complejidad de las interacciones agénticas y el JSON de fuente única de verdad requieren diseño explícito antes de generar código.

- [ ] **Units Generation — EJECUTAR**
  - Rationale: El sistema tiene múltiples unidades de trabajo independientes que pueden desarrollarse en paralelo: (1) Infraestructura base + JSON schema, (2) Agente Scholar, (3) Agente DI, (4) Agente Content, (5) QA Gate + Checkpoint Humano, (6) Publicación Canvas, (7) Interfaz Web. La descomposición en unidades permite desarrollo incremental y testing aislado.

### FASE DE CONSTRUCCIÓN (por unidad)

- [ ] **Functional Design — EJECUTAR** (por unidad)
  - Rationale: Cada agente tiene lógica de negocio compleja (prompts, transformaciones de datos, validaciones) que requiere diseño funcional detallado antes de generar código. El esquema del JSON enriquecido progresivamente necesita definición formal.

- [ ] **NFR Requirements — EJECUTAR** (por unidad)
  - Rationale: Requerimientos de seguridad (SECURITY-01 a SECURITY-15 habilitados), escalabilidad (20 asignaturas paralelas), resiliencia (reintentos con backoff), observabilidad (CloudWatch + SNS) y PBT (habilitado full) requieren evaluación explícita por unidad.

- [ ] **NFR Design — EJECUTAR** (por unidad)
  - Rationale: Los patrones de NFR (cifrado en reposo/tránsito, least-privilege IAM, rate limiting, structured logging, circuit breaker para APIs externas) deben incorporarse al diseño antes de generar código.

- [ ] **Infrastructure Design — EJECUTAR** (por unidad)
  - Rationale: Cada unidad requiere mapeo a servicios AWS específicos: Bedrock Agents, Lambda, S3, DynamoDB, API Gateway, Amplify, Secrets Manager, CloudWatch, SNS. El diseño de infraestructura es crítico para una arquitectura serverless event-driven.

- [ ] **Code Generation — EJECUTAR** (siempre, por unidad)
  - Rationale: Generación de código, tests (unitarios + PBT) y artefactos IaC (CDK/CloudFormation) para cada unidad.

- [ ] **Build and Test — EJECUTAR** (siempre)
  - Rationale: Instrucciones de build, tests unitarios, de integración (entre agentes), de contrato (Scopus API, Canvas API) y de seguridad.

### FASE DE OPERACIONES

- [ ] Operations — PLACEHOLDER (expansión futura)

---

## Unidades de Trabajo Propuestas

| # | Unidad | Descripción | Dependencias |
|---|---|---|---|
| U1 | Infraestructura Base + JSON Schema | S3, DynamoDB, Secrets Manager, IAM roles base, esquema JSON | Ninguna |
| U2 | Agente Scholar | Bedrock Agent + Scopus Action Group (Fases 1 y 2) | U1 |
| U3 | Agente DI | Bedrock Agent + lógica Bloom-Competencias (Fase 3) | U1, U2 |
| U4 | Agente Content | Bedrock Agent + 4 artefactos Maestría (Fase 4) | U1, U3 |
| U5 | QA Gate + Checkpoint Humano | Validación de cobertura RA, flujo aprobación/rechazo, notificaciones SNS | U1, U4 |
| U6 | Publicación Canvas LMS | Canvas API Action Group, montaje Fase 5, bibliografía APA | U1, U5 |
| U7 | Interfaz Web | Amplify/S3 static site, autenticación, dashboard, checkpoint UI | U1, U5, U6 |

---

## Criterios de Éxito del Plan

- Todos los agentes generan sus entregables dentro del JSON de fuente única de verdad
- El QA Gate valida cobertura 100% de RA y alineación Bloom–Competencias antes del checkpoint humano
- El checkpoint humano bloquea efectivamente la publicación hasta aprobación explícita
- Las extensiones Security Baseline (SECURITY-01 a SECURITY-15) y PBT (full) se cumplen en cada unidad
- El sistema procesa 6–20 asignaturas en paralelo sin errores de concurrencia
