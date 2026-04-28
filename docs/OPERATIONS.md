# Guía de Operación

## Uso del Sistema

### 1. Subir una asignatura
1. Abrir el frontend (URL del S3 Static Website)
2. Login con credenciales de Cognito
3. En "Cargar Documentos", seleccionar el DOCX de la asignatura
4. Clic en "Cargar" — el pipeline se ejecuta automáticamente (~10-15 min)

### 2. Revisar contenido generado
1. En el Dashboard, buscar la asignatura con estado "⏳ Pendiente de aprobación"
2. Clic en "📋 Revisar"
3. Navegar las 10 tabs: Resumen, Objetivos, Lecturas, Quizzes, Foros, Papers, Maestría, Masterclass, Reto, Preview Canvas
4. Decidir: ✅ Aprobar / ❌ Rechazar con comentarios

### 3. Verificar en Canvas
- Al aprobar, el curso se crea automáticamente en Canvas LMS
- En el Dashboard, clic en "🔗 Ver en Canvas" para abrir el curso
- El curso se crea como borrador — activar manualmente cuando esté listo

## Administración

### Redesplegar agentes
```bash
agentcore deploy --agent AcademicPipelineScholarDev
agentcore deploy --agent AcademicPipelineDIDev
agentcore deploy --agent AcademicPipelineContentDev
```

### Redesplegar Lambdas
```bash
bash test-data/deploy_lambdas.sh      # QA Gate + Checkpoint
bash test-data/deploy_web_lambdas.sh   # Upload + Ingestion + Dashboard
bash test-data/deploy_canvas.sh        # Canvas Publisher
```

### Redesplegar frontend
```bash
cd src/web_interface/frontend
npm install && npx vite build
aws s3 sync dist/ s3://<FRONTEND_BUCKET>/ --delete
```

### Activar/desactivar Canvas real
```bash
bash test-data/activate_canvas.sh  # Modo real
# Para mock: cambiar CANVAS_MOCK_MODE=true en Lambda config
```

### Limpiar registros de prueba
```bash
python3 test-data/cleanup_dynamo.py
```

## Monitoreo

### CloudWatch Logs
```bash
# Agentes
aws logs tail /aws/bedrock-agentcore/runtimes/<RUNTIME_ID>-DEFAULT --since 1h --follow

# Step Functions
aws logs tail /aws/lambda/academic-pipeline-orch-contentstep-dev --since 1h

# Canvas Publisher
aws logs tail /aws/lambda/academic-pipeline-canvas-publisher-dev --since 1h
```

### Verificar estado de un subject
```bash
python3 test-data/check_subject.py /tmp/subject.json
python3 test-data/check_new_content.py /tmp/subject.json
python3 test-data/show_readings.py /tmp/subject.json
```

## Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| "Asignatura sin nombre" | Parser no extrajo datos del DOCX | Verificar que el DOCX tiene tablas con "Denominación de la asignatura" |
| Content agent timeout | LLM calls tardan >600s | Timeout aumentado a 900s |
| QA Gate FAILED | Quizzes sin ra_ids | QA Gate acepta ra_id y ra_ids |
| CORS error | Token expirado | Limpiar localStorage y re-login |
| Checkpoint 500 | Schema validator rechaza campos | Checkpoint usa direct S3 write |
| Rúbricas sin formato en Canvas | Markdown no renderiza tablas | Se genera HTML directo |
| Curso con nombre genérico | course_code como nombre | Usa subject_name + prefijo MADTFIN |
