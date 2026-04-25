"""
Mock Canvas Client — simulates Canvas API responses for testing.
Returns realistic-looking IDs and URLs without making real API calls.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from src.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

_counter = 0


def _next_id() -> int:
    global _counter
    _counter += 1
    return 90000 + _counter


class MockCanvasClient:
    """Drop-in replacement for CanvasClient that returns mock responses."""

    def __init__(self, base_url: str = "https://mock-canvas.example.com", **kwargs):
        self._base_url = base_url
        self._courses: dict[str, dict] = {}
        self._modules: dict[str, dict] = {}
        self._pages: dict[str, dict] = {}
        self._quizzes: dict[str, dict] = {}
        logger.info("mock_canvas_client_initialized", extra={"base_url": base_url})

    def find_course_by_code(self, account_id: str, course_code: str) -> dict | None:
        for c in self._courses.values():
            if c.get("course_code") == course_code:
                return c
        return None

    def create_course(self, account_id: str, payload: dict) -> dict:
        cid = _next_id()
        course_data = payload.get("course", {})
        course = {
            "id": cid,
            "name": course_data.get("name", "Mock Course"),
            "course_code": course_data.get("course_code", f"MOCK-{cid}"),
            "workflow_state": course_data.get("workflow_state", "unpublished"),
            "html_url": f"{self._base_url}/courses/{cid}",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._courses[str(cid)] = course
        logger.info("mock_course_created", extra={"course_id": cid, "name": course["name"]})
        return course

    def create_module(self, course_id: str, name: str, position: int = 1) -> dict:
        mid = _next_id()
        module = {
            "id": mid,
            "name": name,
            "position": position,
            "items_count": 0,
            "html_url": f"{self._base_url}/courses/{course_id}/modules/{mid}",
        }
        self._modules[str(mid)] = module
        logger.info("mock_module_created", extra={"module_id": mid, "name": name})
        return module

    def create_module_item(self, course_id: str, module_id: str, item: dict) -> dict:
        iid = _next_id()
        result = {
            "id": iid,
            "title": item.get("title", ""),
            "type": item.get("type", "Page"),
            "html_url": f"{self._base_url}/courses/{course_id}/modules/{module_id}/items/{iid}",
        }
        logger.info("mock_module_item_created", extra={"item_id": iid, "title": result["title"]})
        return result

    def create_page(self, course_id: str, payload: dict) -> dict:
        pid = _next_id()
        page_data = payload.get("wiki_page", {})
        title = page_data.get("title", "Mock Page")
        url_slug = title.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")[:50]
        page = {
            "page_id": pid,
            "url": url_slug,
            "title": title,
            "body": page_data.get("body", "")[:100] + "...",
            "html_url": f"{self._base_url}/courses/{course_id}/pages/{url_slug}",
            "published": page_data.get("published", False),
        }
        self._pages[str(pid)] = page
        logger.info("mock_page_created", extra={"page_id": pid, "title": title})
        return page

    def create_quiz(self, course_id: str, payload: dict) -> dict:
        qid = _next_id()
        quiz_data = payload.get("quiz", {})
        quiz = {
            "id": qid,
            "title": quiz_data.get("title", "Mock Quiz"),
            "quiz_type": quiz_data.get("quiz_type", "assignment"),
            "html_url": f"{self._base_url}/courses/{course_id}/quizzes/{qid}",
            "published": False,
        }
        self._quizzes[str(qid)] = quiz
        logger.info("mock_quiz_created", extra={"quiz_id": qid, "title": quiz["title"]})
        return quiz

    def create_quiz_question(self, course_id: str, quiz_id: str, payload: dict) -> dict:
        qqid = _next_id()
        q_data = payload.get("question", {})
        return {
            "id": qqid,
            "question_name": q_data.get("question_name", ""),
            "question_type": q_data.get("question_type", "multiple_choice_question"),
        }

    def create_rubric(self, course_id: str, payload: dict) -> dict:
        rid = _next_id()
        rubric_data = payload.get("rubric", {})
        return {
            "id": rid,
            "title": rubric_data.get("title", "Mock Rubric"),
            "criteria_count": len(rubric_data.get("criteria", [])),
        }

    def get_summary(self) -> dict:
        """Return a summary of all mock resources created."""
        return {
            "courses": len(self._courses),
            "modules": len(self._modules),
            "pages": len(self._pages),
            "quizzes": len(self._quizzes),
            "details": {
                "courses": list(self._courses.values()),
                "pages": [{"title": p["title"], "url": p["html_url"]} for p in self._pages.values()],
                "quizzes": [{"title": q["title"], "url": q["html_url"]} for q in self._quizzes.values()],
            },
        }
