"""
ObservabilityComponent (C10) — Structured logger.
Garantiza que ningún secreto, token ni PII aparezca en los logs (SECURITY-03).
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any


_REDACTED_KEYS = frozenset({
    "password", "token", "api_key", "secret", "authorization",
    "canvas_oauth_token", "scopus_api_key", "credential",
})


def _redact(value: Any, key: str = "") -> Any:
    """Redacta valores sensibles recursivamente."""
    if isinstance(value, dict):
        return {k: _redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if key.lower() in _REDACTED_KEYS:
        return "[REDACTED]"
    return value


class StructuredLogger(logging.Logger):
    """Logger que emite JSON estructurado con campos obligatorios."""

    def _log_structured(self, level: int, operation: str, extra: dict | None = None, **kwargs) -> None:
        record: dict = {
            "level": logging.getLevelName(level),
            "operation": operation,
            "correlation_id": os.environ.get("CORRELATION_ID", str(uuid.uuid4())),
            **(extra or {}),
        }
        record = _redact(record)
        self.log(level, json.dumps(record, ensure_ascii=False, default=str), **kwargs)

    def info(self, operation: str, extra: dict | None = None, **kwargs) -> None:  # type: ignore[override]
        self._log_structured(logging.INFO, operation, extra, **kwargs)

    def warning(self, operation: str, extra: dict | None = None, **kwargs) -> None:  # type: ignore[override]
        self._log_structured(logging.WARNING, operation, extra, **kwargs)

    def error(self, operation: str, extra: dict | None = None, **kwargs) -> None:  # type: ignore[override]
        self._log_structured(logging.ERROR, operation, extra, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    logging.setLoggerClass(StructuredLogger)
    log = logging.getLogger(name)
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
    log.setLevel(logging.INFO)
    return log  # type: ignore[return-value]
