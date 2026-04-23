# Componentes Frontend — U7: Interfaz Web

## Jerarquía de Componentes

```
App
├── AuthGuard (protege todas las rutas)
├── LoginPage
│   └── LoginForm
│       ├── EmailInput          [data-testid="login-email-input"]
│       ├── PasswordInput       [data-testid="login-password-input"]
│       └── LoginButton         [data-testid="login-submit-button"]
├── DashboardPage
│   ├── DashboardHeader
│   ├── UploadSection
│   │   ├── FileDropzone        [data-testid="file-dropzone"]
│   │   ├── FileList            [data-testid="file-list"]
│   │   └── UploadButton        [data-testid="upload-submit-button"]
│   └── SubjectTable
│       ├── SubjectRow          [data-testid="subject-row-{subject_id}"]
│       │   ├── StatusBadge     [data-testid="status-badge-{subject_id}"]
│       │   └── ActionButton    [data-testid="action-button-{subject_id}"]
│       └── RefreshIndicator    [data-testid="refresh-indicator"]
└── CheckpointPage
    ├── ContentPreview
    │   ├── QAReportSummary     [data-testid="qa-report-summary"]
    │   ├── DescriptiveCardView [data-testid="descriptive-card-view"]
    │   └── ContentCountsView   [data-testid="content-counts-view"]
    └── DecisionPanel
        ├── ApproveButton       [data-testid="approve-button"]
        ├── RejectButton        [data-testid="reject-button"]
        ├── CommentsInput       [data-testid="rejection-comments-input"]
        └── EditButton          [data-testid="edit-content-button"]
```

## Props y Estado por Componente

### DashboardPage
- State: `subjects: PipelineStatus[]`, `loading: boolean`, `pollingInterval: number`
- Effect: polling cada 30s a GET /api/subjects

### UploadSection
- State: `files: File[]`, `uploading: boolean`, `error: string | null`
- Props: `onUploadSuccess: (subjectIds: string[]) => void`
- Validation: formato (BR-W01), tamaño (BR-W02)

### CheckpointPage
- Props: `subjectId: string`
- State: `summary: CheckpointSummary | null`, `decision: string`, `comments: string`
- API: GET /api/subjects/{id}/checkpoint, POST /api/subjects/{id}/decision

## Flujos de Interacción

### Flujo de Carga
1. Staff arrastra/selecciona archivos en FileDropzone
2. Validación client-side: formato y tamaño
3. Click UploadButton → POST /api/upload (presigned URL S3)
4. Carga directa a S3 → trigger automático del pipeline
5. Redirect a DashboardPage con polling activo

### Flujo de Validación
1. Staff ve asignatura en PENDING_APPROVAL en SubjectTable
2. Click ActionButton → navega a CheckpointPage
3. Revisa ContentPreview (QA report, carta descriptiva, conteos)
4. Click ApproveButton → POST /api/subjects/{id}/decision {decision: "APPROVED"}
5. O click RejectButton → ingresa comentarios → POST con {decision: "REJECTED", comments}
6. Redirect a DashboardPage
