# Modelo de Lógica de Negocio — U7: Interfaz Web

## Backend (Lambda + API Gateway)

### upload_handler — POST /api/upload
1. Validar formato y tamaño del archivo (BR-W01, BR-W02)
2. Generar subject_id (UUID v4)
3. Generar presigned URL de S3 para carga directa
4. Retornar presigned URL + subject_id al frontend

### document_ingestion_handler — S3 Event Trigger
1. Recibir evento S3 PutObject (archivo cargado)
2. Detectar formato y parsear documento (PDF/DOCX/XLSX)
3. Extraer datos académicos → ParsedDocument
4. Construir JSON inicial con estado INGESTED
5. Persistir en S3 + DynamoDB (StateManagementComponent)
6. Disparar Agente Scholar (invocar AgentCore Runtime)

### dashboard_handler — GET /api/subjects
1. Leer JWT del header (Cognito authorizer)
2. Consultar DynamoDB GSI-1 para listar asignaturas del Staff
3. Retornar lista de PipelineStatus

### checkpoint_handler — GET /api/subjects/{id}/checkpoint
1. Leer JSON de la asignatura desde S3
2. Construir CheckpointSummary con resumen del contenido
3. Retornar al frontend para previsualización

## Document Parser (funciones puras)

### parse_pdf(file_bytes) → ParsedDocument
- Usa PyPDF2/pdfplumber para extraer texto
- Detecta secciones: Perfil de Egreso, Competencias, RA, Temario

### parse_docx(file_bytes) → ParsedDocument
- Usa python-docx para extraer párrafos y tablas
- Mapea estructura del documento a ParsedDocument

### parse_xlsx(file_bytes) → ParsedDocument
- Usa openpyxl para leer hojas y celdas
- Asume estructura tabular: columna RA, columna Competencia
