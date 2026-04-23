"""Tests unitarios y PBT para state_manager — U1."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.infrastructure.state.models import StateMetadata, SubjectState


# ── Helpers ───────────────────────────────────────────────────────────────────

def _minimal_subject(subject_id: str | None = None, state: str = "INGESTED") -> dict:
    sid = subject_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    return {
        "subject_id": sid,
        "schema_version": "1.0",
        "created_at": now,
        "updated_at": now,
        "metadata": {
            "subject_name": "Test Subject",
            "program_name": "Test Program",
            "program_type": "MAESTRIA",
            "subject_type": "CONCENTRACION",
            "language": "ES",
        },
        "academic_inputs": {
            "graduation_profile": "Profile",
            "competencies": [{"competency_id": "C1", "description": "Competency 1"}],
            "learning_outcomes": [{"ra_id": "RA1", "description": "Outcome 1"}],
        },
        "pipeline_state": {
            "current_state": state,
            "state_history": [],
        },
    }


# ── Tests for save_subject_json ───────────────────────────────────────────────

class TestSaveSubjectJson:
    @patch.dict(os.environ, {"SUBJECTS_BUCKET_NAME": "test-bucket", "SUBJECTS_TABLE_NAME": "test-table"})
    @patch("src.infrastructure.state.state_manager._s3_client")
    def test_saves_valid_json_to_s3(self, mock_s3_factory):
        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {"VersionId": "v1"}
        mock_s3_factory.return_value = mock_s3

        from src.infrastructure.state.state_manager import save_subject_json
        subject = _minimal_subject()
        ref = save_subject_json(subject)

        mock_s3.put_object.assert_called_once()
        call_kwargs = mock_s3.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert f"subjects/{subject['subject_id']}/subject.json" in call_kwargs["Key"]
        assert ref.version_id == "v1"

    @patch.dict(os.environ, {"SUBJECTS_BUCKET_NAME": "test-bucket", "SUBJECTS_TABLE_NAME": "test-table"})
    def test_raises_value_error_for_invalid_json(self):
        from src.infrastructure.state.state_manager import save_subject_json
        with pytest.raises(ValueError, match="JSON inválido"):
            save_subject_json({"invalid": "data"})


# ── Tests for update_subject_state ────────────────────────────────────────────

class TestUpdateSubjectState:
    @patch.dict(os.environ, {"SUBJECTS_BUCKET_NAME": "test-bucket", "SUBJECTS_TABLE_NAME": "test-table"})
    @patch("src.infrastructure.state.state_manager._upsert_state_record")
    @patch("src.infrastructure.state.state_manager.save_subject_json")
    @patch("src.infrastructure.state.state_manager.get_subject_json")
    def test_valid_transition_appends_history(self, mock_get, mock_save, mock_upsert):
        subject = _minimal_subject(state="INGESTED")
        mock_get.return_value = subject
        mock_save.return_value = MagicMock()

        from src.infrastructure.state.state_manager import update_subject_state
        update_subject_state(
            subject["subject_id"],
            SubjectState.KNOWLEDGE_MATRIX_READY,
            StateMetadata(agent="scholar-agent", result_hash="abc123"),
        )

        saved_json = mock_save.call_args[0][0]
        assert saved_json["pipeline_state"]["current_state"] == "KNOWLEDGE_MATRIX_READY"
        assert len(saved_json["pipeline_state"]["state_history"]) == 1
        assert saved_json["pipeline_state"]["state_history"][0]["agent"] == "scholar-agent"

    @patch.dict(os.environ, {"SUBJECTS_BUCKET_NAME": "test-bucket", "SUBJECTS_TABLE_NAME": "test-table"})
    @patch("src.infrastructure.state.state_manager.get_subject_json")
    def test_invalid_transition_raises_value_error(self, mock_get):
        subject = _minimal_subject(state="INGESTED")
        mock_get.return_value = subject

        from src.infrastructure.state.state_manager import update_subject_state
        with pytest.raises(ValueError, match="Transición inválida"):
            update_subject_state(
                subject["subject_id"],
                SubjectState.PUBLISHED,
                StateMetadata(agent="test"),
            )


# ── PBT: Round-trip JSON serialization (PBT-02) ───────────────────────────────

class TestStateManagerPBT:
    @given(st.text(min_size=1, max_size=100), st.text(min_size=1, max_size=100))
    @settings(max_examples=30)
    def test_subject_json_serialization_round_trip(self, subject_name: str, program_name: str):
        """PBT-02: serializar y deserializar el JSON preserva los datos."""
        subject = _minimal_subject()
        subject["metadata"]["subject_name"] = subject_name
        subject["metadata"]["program_name"] = program_name

        serialized = json.dumps(subject, ensure_ascii=False)
        deserialized = json.loads(serialized)

        assert deserialized["metadata"]["subject_name"] == subject_name
        assert deserialized["metadata"]["program_name"] == program_name
        assert deserialized["subject_id"] == subject["subject_id"]
