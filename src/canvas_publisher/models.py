"""Modelos de dominio — U6: Publicación Canvas LMS."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CanvasCourse:
    canvas_course_id: str
    name: str
    course_code: str
    workflow_state: str
    canvas_url: str


@dataclass
class CanvasModuleItem:
    item_id: str
    title: str
    item_type: str
    content_id: str
    canvas_url: str = ""


@dataclass
class CanvasModule:
    module_id: str
    name: str
    position: int
    items: list[CanvasModuleItem] = field(default_factory=list)


@dataclass
class PublicationResult:
    subject_id: str
    canvas_course_id: str
    canvas_course_url: str
    module_urls: list[str]
    published_at: str
    status: str  # "PUBLISHED" | "FAILED"

    def to_dict(self) -> dict:
        return {
            "canvas_course_id": self.canvas_course_id,
            "canvas_course_url": self.canvas_course_url,
            "module_urls": self.module_urls,
            "published_at": self.published_at,
        }
