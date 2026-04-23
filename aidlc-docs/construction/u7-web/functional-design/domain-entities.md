# Entidades de Dominio — U7: Interfaz Web

## UploadRequest
```python
@dataclass
class UploadRequest:
    file_name: str
    file_size_bytes: int
    content_type: str   # "application/pdf" | "application/vnd.openxmlformats..." | "application/vnd.ms-excel"
    s3_key: str         # generado: uploads/{subject_id}/{filename}
```

## ParsedDocument
```python
@dataclass
class ParsedDocument:
    subject_id: str
    subject_name: str
    program_name: str
    program_type: str
    subject_type: str
    language: str
    graduation_profile: str
    competencies: list[dict]
    learning_outcomes: list[dict]
    syllabus: str
    source_file: str
```

## PipelineStatus
```python
@dataclass
class PipelineStatus:
    subject_id: str
    subject_name: str
    program_name: str
    current_state: str
    updated_at: str
    canvas_course_url: str | None
    pending_approval: bool
    error_message: str | None
```

## DashboardData
```python
@dataclass
class DashboardData:
    subjects: list[PipelineStatus]
    total: int
    pending_approval_count: int
    published_count: int
    failed_count: int
```
