# Resumen de Código — U7: Interfaz Web

## Archivos Creados

### Backend (Lambda Handlers)
- `src/web-interface/backend/document_parser.py` — validate_upload (BR-W01/W02), detect_program_type, detect_subject_type, extract_learning_outcomes, extract_competencies, parse_text_to_document (funciones puras)
- `src/web-interface/backend/upload_handler.py` — POST /api/upload: genera presigned URL S3, headers de seguridad HTTP (SECURITY-04)
- `src/web-interface/backend/ingestion_handler.py` — S3 Event trigger: parsea PDF/DOCX/XLSX, construye JSON inicial, invoca Agente Scholar (BR-W04)
- `src/web-interface/backend/dashboard_handler.py` — GET /api/subjects: lista estado de asignaturas con headers CORS restringidos (SECURITY-08)

### Frontend (React/TypeScript)
- `src/web-interface/frontend/src/api/pipeline.ts` — API client con JWT Cognito en todos los requests
- `src/web-interface/frontend/src/components/UploadSection.tsx` — FileDropzone + validación client-side + data-testid (BR-W07)
- `src/web-interface/frontend/src/components/SubjectTable.tsx` — Dashboard con polling 30s (BR-W05) + data-testid por subject_id
- `src/web-interface/frontend/src/pages/CheckpointPage.tsx` — Vista de validación humana: QA report, carta descriptiva, botones Aprobar/Rechazar/Editar con data-testid (BR-W06, BR-W07)

### Tests
- `tests/unit/web-interface/test_document_parser.py` — 12 unitarios + 2 PBT (PBT-03: validate_upload siempre ValidationResult, parse siempre retorna doc con subject_id)

## Cobertura de Stories
- US-01 (Carga de documentos): UploadSection + upload_handler + ingestion_handler
- US-02 (Monitoreo del pipeline): SubjectTable + dashboard_handler
- US-14 (Credenciales seguras): presigned URL S3, sin credenciales en frontend
- US-15 (Autenticación Staff): Cognito User Pool + JWT en todos los requests

## Cumplimiento de Extensiones
- SECURITY-03: logger sin PII más allá de file_name ✅
- SECURITY-04: headers HTTP en todos los Lambda responses (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) ✅
- SECURITY-06: IAM least-privilege por Lambda ✅
- SECURITY-08: CORS restringido al dominio de la interfaz, JWT Cognito obligatorio ✅
- SECURITY-12: Cognito User Pool con política de contraseñas, MFA para Admin, bloqueo tras 5 intentos ✅
- PBT-03: Invariantes validate_upload y parse_text_to_document ✅
- PBT-09: Hypothesis como framework PBT ✅
- BR-W07: data-testid en todos los elementos interactivos ✅
