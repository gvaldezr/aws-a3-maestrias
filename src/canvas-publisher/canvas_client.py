"""
Canvas LMS API Client — U6.
Encapsula todas las llamadas a Canvas REST API con retry/backoff.
"""
from __future__ import annotations

import json
import os
import time

import boto3
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)


class CanvasAPIError(Exception):
    pass


class CanvasClient:
    """
    Cliente para Canvas LMS REST API.
    Obtiene el OAuth Token desde Secrets Manager (BR-CV07).
    """

    def __init__(self, base_url: str, secret_arn: str):
        self._base_url = base_url.rstrip("/")
        self._token = self._get_token(secret_arn)
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    @staticmethod
    def _get_token(secret_arn: str) -> str:
        """Obtiene el OAuth Token desde Secrets Manager (BR-CV07, SECURITY-12)."""
        client = boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(resp["SecretString"])
        return secret["oauth_token"]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(CanvasAPIError),
        reraise=True,
    )
    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        """Ejecuta una llamada a Canvas API con retry/backoff (BR-CV06)."""
        url = f"{self._base_url}/api/v1{path}"
        with httpx.Client(timeout=30.0) as client:
            response = getattr(client, method)(url, headers=self._headers, json=payload)

        if response.status_code >= 500:
            raise CanvasAPIError(f"Canvas server error {response.status_code}: {path}")
        if response.status_code == 401:
            raise CanvasAPIError("Canvas authentication failed — check OAuth token")
        if response.status_code >= 400:
            raise CanvasAPIError(f"Canvas client error {response.status_code}: {response.text[:200]}")

        return response.json() if response.content else {}

    # ── Course ────────────────────────────────────────────────────────────────

    def find_course_by_code(self, account_id: str, course_code: str) -> dict | None:
        """Busca un curso existente por course_code (BR-CV09 idempotencia)."""
        try:
            courses = self._request("get", f"/accounts/{account_id}/courses?search_term={course_code}&per_page=5")
            if isinstance(courses, list):
                for c in courses:
                    if c.get("course_code") == course_code:
                        return c
        except CanvasAPIError:
            pass
        return None

    def create_course(self, account_id: str, payload: dict) -> dict:
        return self._request("post", f"/accounts/{account_id}/courses", payload)

    # ── Modules ───────────────────────────────────────────────────────────────

    def create_module(self, course_id: str, name: str, position: int = 1) -> dict:
        return self._request("post", f"/courses/{course_id}/modules",
                             {"module": {"name": name, "position": position}})

    def create_module_item(self, course_id: str, module_id: str, item: dict) -> dict:
        return self._request("post", f"/courses/{course_id}/modules/{module_id}/items",
                             {"module_item": item})

    # ── Pages ─────────────────────────────────────────────────────────────────

    def create_page(self, course_id: str, payload: dict) -> dict:
        return self._request("post", f"/courses/{course_id}/pages", payload)

    # ── Quizzes ───────────────────────────────────────────────────────────────

    def create_quiz(self, course_id: str, payload: dict) -> dict:
        return self._request("post", f"/courses/{course_id}/quizzes", payload)

    def create_quiz_question(self, course_id: str, quiz_id: str, payload: dict) -> dict:
        return self._request("post", f"/courses/{course_id}/quizzes/{quiz_id}/questions", payload)

    # ── Rubrics ───────────────────────────────────────────────────────────────

    def create_rubric(self, course_id: str, payload: dict) -> dict:
        return self._request("post", f"/courses/{course_id}/rubrics", payload)
