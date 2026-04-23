# Entidades de Dominio — U6: Publicación Canvas LMS

## CanvasCourse
```python
@dataclass
class CanvasCourse:
    canvas_course_id: str
    name: str
    course_code: str
    workflow_state: str   # "unpublished" (draft) | "available"
    canvas_url: str
```

## CanvasModule
```python
@dataclass
class CanvasModule:
    module_id: str
    name: str
    position: int
    items: list[CanvasModuleItem]
```

## CanvasModuleItem
```python
@dataclass
class CanvasModuleItem:
    item_id: str
    title: str
    item_type: str   # "Page" | "Quiz" | "Assignment" | "File"
    content_id: str
    canvas_url: str
```

## CanvasQuiz
```python
@dataclass
class CanvasQuiz:
    quiz_id: str
    title: str
    ra_id: str
    questions_count: int
```

## CanvasRubric
```python
@dataclass
class CanvasRubric:
    rubric_id: str
    title: str
    competency_ids: list[str]   # vinculadas al programa
    criteria: list[dict]
```

## PublicationResult
```python
@dataclass
class PublicationResult:
    subject_id: str
    canvas_course_id: str
    canvas_course_url: str
    module_urls: list[str]
    published_at: str
    status: str   # "PUBLISHED" | "FAILED"
```
