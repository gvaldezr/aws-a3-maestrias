# Reglas de Negocio — U3: Agente DI

## BR-DI01 — Verbos Bloom obligatorios
Cada objetivo de aprendizaje debe usar un verbo de la Taxonomía de Bloom con nivel cognitivo explícito. No se aceptan verbos genéricos como "conocer", "entender" o "saber".

## BR-DI02 — Mapeo obligatorio a competencias
Cada objetivo debe mapearse a al menos una competencia del programa por ID. Si no existe mapeo posible, se registra como AlignmentGap y se escala al Staff antes de continuar.

## BR-DI03 — Cobertura total de RA
El conjunto de objetivos generados debe cubrir el 100% de los RA de la asignatura. Cada RA debe tener al menos un objetivo asociado.

## BR-DI04 — Nivel Bloom por tipo de materia
- Fundamentos: objetivos predominantemente en RECORDAR / COMPRENDER / APLICAR
- Concentración: objetivos predominantemente en ANALIZAR / EVALUAR
- Proyecto: objetivos predominantemente en EVALUAR / CREAR

## BR-DI05 — Mapa de 4 semanas obligatorio
La Carta Descriptiva V1 debe incluir un mapa de exactamente 4 semanas con progresión Ingesta → Síntesis.

## BR-DI06 — Escalación por gap de alineación
Si algún objetivo no puede mapearse a ninguna competencia, el agente marca el JSON con estado `DI_ALIGNMENT_GAP`, notifica al Staff vía SNS con el detalle del gap, y detiene el pipeline para esa asignatura.

## BR-DI07 — Matriz de trazabilidad completa
La matriz de trazabilidad debe contener una entrada por cada par (objetivo, RA). Cada entrada incluye: objective_id, bloom_level, competency_ids, ra_id.

## BR-DI08 — Idempotencia
Re-ejecutar el agente DI con el mismo JSON de entrada produce la misma Carta Descriptiva (dado el mismo modelo LLM y temperatura 0).
