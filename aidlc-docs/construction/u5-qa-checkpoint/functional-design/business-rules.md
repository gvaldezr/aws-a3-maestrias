# Reglas de Negocio — U5: QA Gate + Checkpoint Humano

## BR-QA01 — QA Gate es obligatorio y no omitible
El QA Gate debe ejecutarse antes de cualquier notificación al Staff. No puede ser saltado.

## BR-QA02 — Cobertura 100% de RA requerida
El QA Gate valida que cada RA tiene al menos un recurso de contenido (quiz) asociado.

## BR-QA03 — Alineación Bloom–Competencias requerida
El QA Gate valida que cada objetivo de aprendizaje tiene nivel Bloom asignado y al menos una competencia mapeada.

## BR-QA04 — Artefactos Maestría requeridos
Para programas de Maestría, el QA Gate valida que los 4 artefactos de RF-05a están presentes y no vacíos.

## BR-QA05 — Reintentos antes de escalar
Si el QA Gate falla, activa reintento en el agente responsable (máx. 3). Solo escala al Staff si persiste tras 3 intentos.

## BR-QA06 — Aprobación explícita obligatoria
El pipeline no avanza a publicación sin aprobación explícita del Staff. El estado APPROVED solo se puede establecer mediante una acción del Staff.

## BR-QA07 — Comentarios obligatorios en rechazo
Si el Staff rechaza el contenido, el campo `comments` es obligatorio y no puede estar vacío.

## BR-QA08 — Timeout de 48 horas con recordatorio
Si el Staff no responde en 48 horas, el sistema envía un recordatorio vía SNS. El pipeline permanece en PENDING_APPROVAL.

## BR-QA09 — Auditoría completa de decisiones
Toda decisión del Staff (aprobación, rechazo, edición manual) se registra en el JSON con: usuario, timestamp, comentarios y ediciones.

## BR-QA10 — Ciclo rechazo→corrección máximo 3 veces
El ciclo rechazo→corrección puede repetirse hasta 3 veces. Si persiste, escala a soporte técnico.
