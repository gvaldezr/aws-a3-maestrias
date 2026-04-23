# Reglas de Negocio — U7: Interfaz Web

## BR-W01 — Formatos de documento aceptados
Solo se aceptan: PDF (.pdf), Word (.docx) y Excel (.xlsx). Cualquier otro formato es rechazado con mensaje de error claro.

## BR-W02 — Tamaño máximo de archivo
Cada archivo no puede superar 50MB. El sistema valida el tamaño antes de iniciar la carga a S3.

## BR-W03 — Autenticación obligatoria
Todas las rutas de la interfaz web (excepto /login) requieren sesión activa de Cognito. Sesión expira tras 8 horas de inactividad.

## BR-W04 — Disparo automático del pipeline
La carga exitosa de documentos dispara automáticamente el pipeline para cada asignatura detectada. No requiere acción adicional del Staff.

## BR-W05 — Dashboard en tiempo real
El estado de cada asignatura se actualiza con polling cada 30 segundos. El Staff no necesita refrescar manualmente.

## BR-W06 — Checkpoint visible solo para PENDING_APPROVAL
La vista de validación humana solo se muestra para asignaturas en estado PENDING_APPROVAL.

## BR-W07 — Elementos con data-testid
Todos los elementos interactivos (botones, inputs, formularios) deben tener atributos data-testid para automatización de pruebas.

## BR-W08 — Documentos parseados antes de disparar pipeline
El backend parsea el documento y extrae los datos académicos antes de crear el JSON inicial y disparar el pipeline.
