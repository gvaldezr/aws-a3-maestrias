"""Tests unitarios y PBT para timeout_checker — U5."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.qa_checkpoint.timeout_checker import is_past_timeout


class TestIsPastTimeout:
    def test_past_48h_returns_true(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
        assert is_past_timeout(past) is True

    def test_within_48h_returns_false(self):
        recent = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        assert is_past_timeout(recent) is False

    def test_exactly_48h_returns_true(self):
        exactly = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        # Exactamente 48h SÍ es past timeout (>=)
        assert is_past_timeout(exactly) is True

    def test_invalid_date_returns_false(self):
        assert is_past_timeout("not-a-date") is False

    def test_empty_string_returns_false(self):
        assert is_past_timeout("") is False

    def test_custom_now_parameter(self):
        pending = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
        future_now = datetime(2026, 1, 3, 1, 0, 0, tzinfo=timezone.utc)  # 49h later
        assert is_past_timeout(pending, now=future_now) is True


class TestTimeoutCheckerPBT:
    @given(st.integers(min_value=49, max_value=1000))
    @settings(max_examples=30)
    def test_more_than_48h_always_past_timeout(self, hours: int):
        """PBT-03 invariant: > 48h siempre es past timeout."""
        past = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        assert is_past_timeout(past) is True

    @given(st.integers(min_value=0, max_value=47))
    @settings(max_examples=30)
    def test_less_than_48h_never_past_timeout(self, hours: int):
        """PBT-03 invariant: < 48h nunca es past timeout."""
        recent = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        assert is_past_timeout(recent) is False
