# Métodos de Componentes
## Pipeline Académico → Canvas LMS

> Nota: Las firmas aquí son de alto nivel. La lógica de negocio detallada se define en Functional Design (fase de Construcción por unidad).

---

## C1 — DocumentIngestionComponent

```python
def ingest_document(s3_key: str, bucket: str) -> IngestionResult
# Descarga y parsea el documento desde S3; retorna resultado con estado y errores

def extract_academic_data(document: ParsedDocument) -> AcademicData
# Extrae Perfil de Egreso, Matriz de Competencias, RA y temario del documento parseado

def detect_program_type(academic_data: AcademicData) -> ProgramType
# Detecta si es Maestría u otro nivel; detecta tipo de materia (Fundamentos/Concentración/Proyecto)

def build_initial_json(academic_data: AcademicData, program_type: ProgramType) -> SubjectJSON
# Construye el JSON inicial de la asignatura con estado INGESTED

def persist_and_trigger(subject_json: SubjectJSON) -> TriggerResult
# Persiste el JSON en S3 + DynamoDB y dispara el evento de inicio del pipeline
```

---

## C2 — ScholarAgentComponent

```python
def generate_search_keywords(learning_outcomes: list[str], competencies: list[Competency]) -> list[str]
# Genera keywords de alta precisión para Scopus a partir de RA y competencias

def search_scopus(keywords: list[str], filters: ScopusFilters) -> list[Paper]
# Ejecuta búsqueda en Scopus API con filtros Q1/Q2; gestiona rate limiting y reintentos

def rank_and_select_top20(papers: list[Paper]) -> list[Paper]
# Rankea papers por relevancia y retorna el Top 20

def extract_knowledge_matrix(papers: list[Paper]) -> KnowledgeMatrix
# Extrae conceptos, metodologías y casos de éxito con enfoque directivo

def validate_corpus_quality(papers: list[Paper]) -> CorpusValidation
# Valida que el corpus tiene suficiente cantidad y calidad; retorna gaps si los hay

def escalate_insufficient_corpus(subject_id: str, validation: CorpusValidation) -> None
# Notifica al Staff vía SNS con detalle del gap y detiene el pipeline para la asignatura

def enrich_json_with_research(subject_json: SubjectJSON, papers: list[Paper], matrix: KnowledgeMatrix) -> SubjectJSON
# Enriquece el JSON con Top 20 y Matriz de Conocimiento; actualiza estado a KNOWLEDGE_MATRIX_READY
```

---

## C3 — DIAgentComponent

```python
def structure_by_subject_type(knowledge_matrix: KnowledgeMatrix, subject_type: SubjectType) -> StructuredContent
# Organiza el conocimiento según Fundamentos / Concentración / Proyecto

def generate_content_map(structured_content: StructuredContent, learning_outcomes: list[str]) -> ContentMap
# Genera el Mapa de Contenidos y Objetivos con verbos Bloom en nivel Analizar/Evaluar

def generate_learning_objectives(content_map: ContentMap, competencies: list[Competency]) -> list[LearningObjective]
# Redacta objetivos con verbo Bloom, nivel cognitivo y mapeo a competencias por ID

def build_traceability_matrix(objectives: list[LearningObjective], learning_outcomes: list[str]) -> TraceabilityMatrix
# Construye matriz objetivo → nivel Bloom → competencia(s) → RA

def detect_alignment_gaps(objectives: list[LearningObjective], competencies: list[Competency]) -> list[AlignmentGap]
# Detecta objetivos sin competencia asociada

def escalate_alignment_gap(subject_id: str, gaps: list[AlignmentGap]) -> None
# Notifica al Staff con detalle del gap y detiene el pipeline

def draft_descriptive_card(content_map: ContentMap, objectives: list[LearningObjective]) -> DescriptiveCard
# Redacta la Carta Descriptiva V1 con mapa de 4 semanas y casos de estudio

def enrich_json_with_di(subject_json: SubjectJSON, card: DescriptiveCard, matrix: TraceabilityMatrix) -> SubjectJSON
# Enriquece el JSON con Carta Descriptiva V1 y matriz de trazabilidad; actualiza estado a DI_READY
```

---

## C4 — ContentAgentComponent

```python
def generate_executive_readings(descriptive_card: DescriptiveCard, language: Language) -> list[Reading]
# Genera lecturas ejecutivas por semana en el idioma configurado

def generate_masterclass_scripts(descriptive_card: DescriptiveCard, language: Language) -> list[Script]
# Genera guiones de masterclass con estructura de sesión

def generate_quizzes(learning_outcomes: list[str], language: Language) -> list[Quiz]
# Genera quizzes con mínimo 3 preguntas por RA, respuestas y retroalimentación

def generate_lab_cases(descriptive_card: DescriptiveCard, competencies: list[Competency], language: Language) -> list[LabCase]
# Genera casos de laboratorio agéntico con contexto, datos, preguntas y rúbrica

def generate_evidence_dashboard(papers: list[Paper], language: Language) -> EvidenceDashboard
# Genera el Dashboard de Evidencia en Markdown/HTML (solo Maestría)

def generate_critical_path_map(descriptive_card: DescriptiveCard, language: Language) -> CriticalPathMap
# Genera el Mapa de Ruta Crítica de 3 semanas (solo Maestría)

def generate_executive_cases_repository(lab_cases: list[LabCase], competencies: list[Competency], language: Language) -> CasesRepository
# Genera el Repositorio de Casos Ejecutivos con fichas técnicas (solo Maestría)

def generate_facilitator_guide(descriptive_card: DescriptiveCard, language: Language) -> FacilitatorGuide
# Genera la Guía del Facilitador minuto a minuto (solo Maestría)

def validate_ra_coverage(content_package: ContentPackage, learning_outcomes: list[str]) -> CoverageReport
# Valida que el contenido cubre el 100% de los RA

def enrich_json_with_content(subject_json: SubjectJSON, package: ContentPackage) -> SubjectJSON
# Enriquece el JSON con el paquete completo; actualiza estado a CONTENT_READY
```

---

## C5 — QAGateComponent

```python
def validate_ra_coverage(subject_json: SubjectJSON) -> ValidationResult
# Verifica que cada RA tiene al menos un recurso de contenido asociado

def validate_bloom_alignment(subject_json: SubjectJSON) -> ValidationResult
# Verifica que cada objetivo tiene nivel Bloom y competencia mapeada

def validate_maestria_artifacts(subject_json: SubjectJSON) -> ValidationResult
# Para Maestría: verifica presencia y completitud de los 4 artefactos de RF-05a

def run_full_qa(subject_json: SubjectJSON) -> QAReport
# Ejecuta todas las validaciones y retorna reporte consolidado

def trigger_retry(subject_id: str, gap: QAGap, attempt: int) -> RetryResult
# Activa reintento en el agente responsable del gap (máx. 3 intentos)

def escalate_qa_failure(subject_id: str, report: QAReport) -> None
# Notifica al Staff vía SNS con detalle de gaps persistentes tras 3 intentos

def update_json_with_qa(subject_json: SubjectJSON, report: QAReport) -> SubjectJSON
# Actualiza el JSON con el reporte QA y estado PENDING_APPROVAL o QA_FAILED
```

---

## C6 — HumanValidationComponent

```python
def notify_staff_for_review(subject_id: str, summary: ContentSummary) -> None
# Notifica al Staff vía SNS que el contenido está listo para revisión

def get_validation_summary(subject_json: SubjectJSON) -> ContentSummary
# Construye el resumen de contenido para presentar en la interfaz web

def process_approval(subject_id: str, staff_user: str) -> ApprovalResult
# Registra la aprobación en JSON y DynamoDB con timestamp y usuario

def process_rejection(subject_id: str, staff_user: str, comments: str) -> RejectionResult
# Registra el rechazo y enruta el feedback al agente responsable

def process_manual_edit(subject_id: str, staff_user: str, edits: dict) -> EditResult
# Aplica ediciones manuales del Staff y las registra como modificación humana en auditoría

def check_approval_timeout(subject_id: str) -> TimeoutStatus
# Verifica si han pasado 48h sin respuesta y dispara recordatorio SNS

def update_json_with_decision(subject_json: SubjectJSON, decision: ValidationDecision) -> SubjectJSON
# Actualiza el JSON con estado APPROVED o REJECTED y detalle de la decisión
```

---

## C7 — CanvasPublisherComponent

```python
def generate_apa_bibliography(papers: list[Paper]) -> Bibliography
# Genera la bibliografía en formato APA a partir del Top 20 de Scopus

def export_to_canvas_templates(content_package: ContentPackage) -> CanvasPayload
# Exporta el paquete de contenido a plantillas HTML/Markdown para Canvas API

def create_course_shell(canvas_token: str, subject_json: SubjectJSON) -> CourseShell
# Crea la shell del curso en Canvas Cloud vía API REST

def publish_modules(course_id: str, canvas_payload: CanvasPayload) -> list[Module]
# Publica módulos con todos los recursos del paquete de contenido

def configure_assignments_and_quizzes(course_id: str, canvas_payload: CanvasPayload) -> list[Assignment]
# Configura tareas y quizzes en Canvas

def link_rubrics_to_competencies(course_id: str, rubrics: list[Rubric], competencies: list[Competency]) -> None
# Vincula rúbricas a competencias del programa por ID

def publish_maestria_artifacts(course_id: str, artifacts: MaestriaArtifacts) -> list[Page]
# Publica los 4 artefactos de Maestría como páginas independientes en el módulo

def update_json_with_publication(subject_json: SubjectJSON, course_urls: CourseURLs) -> SubjectJSON
# Actualiza el JSON con estado PUBLISHED y URLs de Canvas
```

---

## C8 — WebInterfaceComponent

```python
def authenticate_staff(credentials: Credentials) -> AuthSession
# Autentica al Staff y retorna sesión con expiración de 8 horas

def upload_documents(session: AuthSession, files: list[UploadedFile]) -> UploadResult
# Carga documentos a S3 y dispara el pipeline

def get_pipeline_dashboard(session: AuthSession) -> DashboardData
# Retorna estado en tiempo real de todas las asignaturas del Staff

def get_validation_checkpoint(session: AuthSession, subject_id: str) -> CheckpointView
# Retorna la vista de previsualización del checkpoint de validación humana

def submit_validation_decision(session: AuthSession, subject_id: str, decision: ValidationDecision) -> DecisionResult
# Envía la decisión de aprobación, rechazo o edición manual
```

---

## C9 — StateManagementComponent

```python
def save_subject_json(subject_json: SubjectJSON) -> S3Reference
# Persiste el JSON completo en S3 con versionado

def update_subject_state(subject_id: str, state: SubjectState, metadata: StateMetadata) -> None
# Actualiza el registro de estado en DynamoDB con timestamp, agente y hash

def get_subject_json(subject_id: str) -> SubjectJSON
# Recupera el JSON completo desde S3

def get_subject_state(subject_id: str) -> SubjectState
# Recupera el estado actual desde DynamoDB

def list_subjects_by_state(state: SubjectState) -> list[SubjectSummary]
# Lista asignaturas filtradas por estado (para dashboard y monitoreo)
```

---

## C10 — ObservabilityComponent

```python
def log_event(component: str, event_type: str, subject_id: str, details: dict, level: LogLevel) -> None
# Registra un evento estructurado en CloudWatch con timestamp, actor y correlation ID

def record_metric(metric_name: str, value: float, dimensions: dict) -> None
# Registra una métrica en CloudWatch Metrics

def send_notification(topic_arn: str, subject: str, message: str) -> None
# Envía notificación vía SNS (alertas, recordatorios, escalaciones)

def configure_alarm(alarm_name: str, metric: str, threshold: float, actions: list[str]) -> None
# Configura alarma en CloudWatch con acciones SNS
```
