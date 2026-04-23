"""Validador del esquema JSON v1.0 para SubjectJSON."""
from __future__ import annotations

from dataclasses import dataclass, field

import jsonschema

from src.infrastructure.schema.subject_schema_v1 import SUBJECT_SCHEMA_V1, VALID_STATE_TRANSITIONS


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_subject_json(subject_json: dict) -> ValidationResult:
    """
    Valida un SubjectJSON contra el esquema v1.0.
    Retorna ValidationResult con is_valid=True si es válido, o lista de errores si no.
    Nunca lanza excepción — siempre retorna un resultado.
    """
    validator = jsonschema.Draft7Validator(SUBJECT_SCHEMA_V1)
    errors = [
        f"{'.'.join(str(p) for p in e.absolute_path) or 'root'}: {e.message}"
        for e in sorted(validator.iter_errors(subject_json), key=str)
    ]
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def is_valid_state_transition(current_state: str, new_state: str) -> bool:
    """
    Verifica si la transición de estado es válida según BR-04.
    Retorna True si la transición está permitida.
    """
    allowed = VALID_STATE_TRANSITIONS.get(current_state, [])
    return new_state in allowed
