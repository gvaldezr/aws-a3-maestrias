# Modelo de Lógica de Negocio — U5: QA Gate + Checkpoint Humano

## run_qa_gate(subject_json) → QAReport
1. Validar cobertura de RA (BR-QA02): cada RA tiene quiz asociado
2. Validar alineación Bloom–Competencias (BR-QA03): cada objetivo tiene competencia
3. Si Maestría: validar 4 artefactos presentes (BR-QA04)
4. Determinar overall_status: PASS si todo OK, FAIL si alguna validación falla
5. Almacenar QAReport en el JSON
6. Retornar QAReport

## notify_staff_for_review(subject_id, summary) → None
1. Construir CheckpointSummary con resumen del contenido y resultado del QA
2. Calcular timeout_at = now + 48h
3. Publicar mensaje SNS al topic staff-notifications con el resumen
4. Actualizar JSON con estado PENDING_APPROVAL y pending_since

## process_approval(subject_id, staff_user) → ValidationDecision
1. Validar que el estado actual es PENDING_APPROVAL
2. Crear ValidationDecision con decision=APPROVED, decided_by, decided_at=now
3. Actualizar JSON: validation.status=APPROVED, decided_by, decided_at
4. Actualizar estado a APPROVED
5. Registrar en auditoría (BR-QA09)
6. Retornar ValidationDecision

## process_rejection(subject_id, staff_user, comments) → ValidationDecision
1. Validar que comments no está vacío (BR-QA07)
2. Crear ValidationDecision con decision=REJECTED
3. Actualizar JSON: validation.status=REJECTED, comments
4. Registrar en auditoría (BR-QA09)
5. Verificar ciclo de rechazo (BR-QA10): si >= 3 rechazos, escalar a soporte
6. Retornar ValidationDecision

## process_manual_edit(subject_id, staff_user, edits) → None
1. Aplicar ediciones al JSON en los campos especificados
2. Registrar cada edición en validation.manual_edits con: campo, valor_anterior, valor_nuevo, usuario, timestamp
3. Mantener estado en PENDING_APPROVAL (el Staff aún debe aprobar)

## check_approval_timeout(subject_id) → bool
1. Leer pending_since del JSON
2. Si now > pending_since + 48h → enviar recordatorio SNS → retornar True
3. Si no → retornar False
