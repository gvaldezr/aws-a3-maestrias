"""Tests unitarios para checkpoint — U5."""
from __future__ import annotations

import pytest

from src.qa_checkpoint.checkpoint import (
    apply_manual_edits,
    count_rejection_cycles,
    process_approval,
    process_rejection,
)


def _subject(subject_id: str = "test-id", rejection_history: int = 0) -> dict:
    history = [{"state": "REJECTED", "agent": "staff:user", "timestamp": "2026-01-01T00:00:00Z", "result_hash": "x"}
               for _ in range(rejection_history)]
    return {
        "subject_id": subject_id,
        "metadata": {"subject_name": "Test", "program_type": "MAESTRIA"},
        "pipeline_state": {"current_state": "PENDING_APPROVAL", "state_history": history},
        "validation": {},
    }


class TestProcessApproval:
    def test_returns_approved_decision(self):
        subject = _subject()
        decision = process_approval(subject, "staff_user_1")
        assert decision.decision == "APPROVED"
        assert decision.decided_by == "staff_user_1"
        assert decision.subject_id == "test-id"

    def test_decided_at_is_set(self):
        subject = _subject()
        decision = process_approval(subject, "user")
        assert decision.decided_at != ""


class TestProcessRejection:
    def test_returns_rejected_decision(self):
        subject = _subject()
        decision = process_rejection(subject, "staff_user_1", "El contenido no cubre el RA3")
        assert decision.decision == "REJECTED"
        assert decision.comments == "El contenido no cubre el RA3"

    def test_empty_comments_raises_value_error(self):
        subject = _subject()
        with pytest.raises(ValueError, match="obligatorios"):
            process_rejection(subject, "user", "")

    def test_whitespace_comments_raises_value_error(self):
        subject = _subject()
        with pytest.raises(ValueError):
            process_rejection(subject, "user", "   ")


class TestCountRejectionCycles:
    def test_no_rejections_returns_zero(self):
        assert count_rejection_cycles(_subject()) == 0

    def test_counts_rejected_states(self):
        assert count_rejection_cycles(_subject(rejection_history=2)) == 2

    def test_three_rejections_detected(self):
        assert count_rejection_cycles(_subject(rejection_history=3)) == 3


class TestApplyManualEdits:
    def test_applies_edit_to_field(self):
        subject = _subject()
        subject["instructional_design"] = {"descriptive_card": {"general_objective": "Old objective"}}
        apply_manual_edits(subject, {"instructional_design.descriptive_card.general_objective": "New objective"}, "user")
        assert subject["instructional_design"]["descriptive_card"]["general_objective"] == "New objective"

    def test_records_edit_in_manual_edits(self):
        subject = _subject()
        subject["instructional_design"] = {"descriptive_card": {"general_objective": "Old"}}
        apply_manual_edits(subject, {"instructional_design.descriptive_card.general_objective": "New"}, "user")
        edits = subject["validation"]["manual_edits"]
        assert len(edits) == 1
        assert edits[0]["old_value"] == "Old"
        assert edits[0]["new_value"] == "New"
        assert edits[0]["edited_by"] == "user"

    def test_multiple_edits_all_recorded(self):
        subject = _subject()
        subject["metadata"] = {"subject_name": "Old Name", "program_type": "MAESTRIA"}
        apply_manual_edits(subject, {"metadata.subject_name": "New Name"}, "user")
        assert len(subject["validation"]["manual_edits"]) == 1
