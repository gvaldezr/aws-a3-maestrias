"""Tests unitarios y PBT para document_parser — U7."""
from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.web_interface.backend.document_parser import (
    detect_program_type,
    detect_subject_type,
    extract_competencies,
    extract_learning_outcomes,
    parse_text_to_document,
    validate_upload,
)


class TestValidateUpload:
    def test_valid_pdf_passes(self):
        result = validate_upload("doc.pdf", 1024, "application/pdf")
        assert result.is_valid

    def test_valid_docx_passes(self):
        result = validate_upload(
            "doc.docx", 1024,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert result.is_valid

    def test_invalid_format_fails(self):
        result = validate_upload("doc.txt", 1024, "text/plain")
        assert not result.is_valid
        assert any("Formato" in e for e in result.errors)

    def test_oversized_file_fails(self):
        result = validate_upload("doc.pdf", 60 * 1024 * 1024, "application/pdf")
        assert not result.is_valid
        assert any("grande" in e for e in result.errors)

    def test_returns_validation_result(self):
        from src.web_interface.backend.document_parser import ValidationResult
        result = validate_upload("doc.pdf", 100, "application/pdf")
        assert isinstance(result, ValidationResult)


class TestDetectProgramType:
    def test_maestria_detected(self):
        assert detect_program_type("Maestría en Gestión Tecnológica") == "MAESTRIA"

    def test_master_english_detected(self):
        assert detect_program_type("Master of Science in AI") == "MAESTRIA"

    def test_otro_for_licenciatura(self):
        assert detect_program_type("Licenciatura en Sistemas") == "OTRO"


class TestDetectSubjectType:
    def test_proyecto_detected(self):
        assert detect_subject_type("Proyecto de Tesis Final") == "PROYECTO"

    def test_concentracion_detected(self):
        assert detect_subject_type("Concentración en Machine Learning") == "CONCENTRACION"

    def test_fundamentos_default(self):
        assert detect_subject_type("Introducción a la Programación") == "FUNDAMENTOS"


class TestExtractLearningOutcomes:
    def test_extracts_ra_pattern(self):
        text = "RA1: Analizar sistemas complejos\nRA2: Evaluar soluciones tecnológicas"
        outcomes = extract_learning_outcomes(text)
        assert len(outcomes) >= 1
        assert any(o["ra_id"] == "RA1" for o in outcomes)

    def test_empty_text_returns_empty(self):
        assert extract_learning_outcomes("") == []


class TestParseTextToDocument:
    def test_returns_parsed_document(self):
        text = "Innovación Tecnológica\nMaestría en Gestión TI\nRA1: Analizar tendencias"
        doc = parse_text_to_document(text, "test-id")
        assert doc.subject_id == "test-id"
        assert doc.subject_name == "Innovación Tecnológica"

    def test_always_has_at_least_one_ra(self):
        doc = parse_text_to_document("Subject\nProgram", "test-id")
        assert len(doc.learning_outcomes) >= 1

    def test_always_has_at_least_one_competency(self):
        doc = parse_text_to_document("Subject\nProgram", "test-id")
        assert len(doc.competencies) >= 1

    def test_maestria_detected_in_program_name(self):
        doc = parse_text_to_document("Asignatura\nMaestría en Negocios", "test-id")
        assert doc.program_type == "MAESTRIA"


class TestDocumentParserPBT:
    @given(st.text(min_size=0, max_size=50), st.integers(min_value=0, max_value=100 * 1024 * 1024))
    @settings(max_examples=30)
    def test_validate_upload_always_returns_validation_result(self, name: str, size: int):
        """PBT-03 invariant: validate_upload siempre retorna ValidationResult."""
        from src.web_interface.backend.document_parser import ValidationResult
        result = validate_upload(name, size, "application/pdf")
        assert isinstance(result, ValidationResult)
        assert isinstance(result.is_valid, bool)

    @given(st.text(min_size=5, max_size=500))
    @settings(max_examples=30)
    def test_parse_always_returns_document_with_subject_id(self, text: str):
        """PBT-03 invariant: parse_text_to_document siempre retorna doc con subject_id."""
        doc = parse_text_to_document(text, "fixed-id")
        assert doc.subject_id == "fixed-id"
        assert len(doc.learning_outcomes) >= 1
        assert len(doc.competencies) >= 1
