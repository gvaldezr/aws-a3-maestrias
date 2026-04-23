"""Tests para structured logger — SECURITY-03 (sin secretos en logs)."""
from __future__ import annotations

import json
import logging

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.infrastructure.observability.logger import _redact, get_logger


class TestRedact:
    def test_redacts_token_key(self):
        assert _redact("secret-value", "token") == "[REDACTED]"

    def test_redacts_api_key(self):
        assert _redact("my-key-123", "api_key") == "[REDACTED]"

    def test_does_not_redact_safe_key(self):
        assert _redact("some-value", "subject_id") == "some-value"

    def test_redacts_nested_dict(self):
        data = {"subject_id": "abc", "token": "secret123", "nested": {"api_key": "key"}}
        result = _redact(data)
        assert result["subject_id"] == "abc"
        assert result["token"] == "[REDACTED]"
        assert result["nested"]["api_key"] == "[REDACTED]"

    def test_redacts_in_list(self):
        data = [{"token": "secret"}, {"subject_id": "abc"}]
        result = _redact(data)
        assert result[0]["token"] == "[REDACTED]"
        assert result[1]["subject_id"] == "abc"


class TestStructuredLogger:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test.module")
        assert logger is not None

    def test_logger_emits_json(self, caplog):
        logger = get_logger("test.json")
        with caplog.at_level(logging.INFO, logger="test.json"):
            logger.info("test_operation", extra={"subject_id": "abc-123"})
        assert len(caplog.records) == 1
        record_msg = caplog.records[0].getMessage()
        parsed = json.loads(record_msg)
        assert parsed["operation"] == "test_operation"
        assert parsed["subject_id"] == "abc-123"
        assert "level" in parsed

    def test_logger_redacts_secrets(self, caplog):
        logger = get_logger("test.security")
        with caplog.at_level(logging.INFO, logger="test.security"):
            logger.info("test_op", extra={"token": "super-secret", "subject_id": "abc"})
        record_msg = caplog.records[0].getMessage()
        assert "super-secret" not in record_msg
        assert "[REDACTED]" in record_msg


# ── PBT: Redact invariant (PBT-03) ───────────────────────────────────────────

_SENSITIVE_KEYS = ["token", "api_key", "secret", "password", "authorization"]


class TestRedactPBT:
    @given(st.text(), st.sampled_from(_SENSITIVE_KEYS))
    @settings(max_examples=50)
    def test_sensitive_keys_always_redacted(self, value: str, key: str):
        """PBT-03 invariant: valores con claves sensibles siempre se redactan."""
        result = _redact(value, key)
        assert result == "[REDACTED]"

    @given(st.text(min_size=1), st.text(min_size=1).filter(lambda k: k.lower() not in {
        "password", "token", "api_key", "secret", "authorization",
        "canvas_oauth_token", "scopus_api_key", "credential",
    }))
    @settings(max_examples=50)
    def test_safe_keys_never_redacted(self, value: str, key: str):
        """PBT-03 invariant: claves no sensibles nunca se redactan."""
        result = _redact(value, key)
        assert result == value
