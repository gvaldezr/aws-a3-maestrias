# Plan de Generación de Código — U1: Infraestructura Base + JSON Schema

**Unidad**: U1 — Infraestructura Base + JSON Schema
**Directorio de código**: `src/infrastructure/`
**Stories**: US-16 (Auditoría de Acciones del Sistema)
**Dependencias**: Ninguna — unidad fundacional

---

## Contexto de la Unidad

- Provisiona todos los recursos AWS base que las demás unidades consumen
- Define y valida el esquema JSON de fuente única de verdad
- Implementa StateManagementComponent (C9) y ObservabilityComponent (C10)
- IaC en AWS CDK (Python); lógica de negocio en Python (Lambda)
- PBT Framework: Hypothesis (PBT-09)

---

## Pasos de Generación

- [x] Paso 1 — Estructura del Proyecto (Monorepo)

- [x] Paso 2 — Esquema JSON (Fuente Única de Verdad)
- [x] Paso 3 — StateManagementComponent (C9)
- [x] Paso 4 — ObservabilityComponent (C10)
- [x] Paso 5 — CDK Stack: InfrastructureBaseStack
- [x] Paso 6 — Documentación de Código

---

## Trazabilidad de Stories

| Story | Pasos que la implementan |
|---|---|
| US-16 (Auditoría) | Paso 4 (logger structured, retención 90d, sin permisos de borrado) + Paso 5 (CloudWatch Log Groups) |
