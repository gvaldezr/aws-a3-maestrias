"""
Document Parser — U7: Extrae datos académicos de PDF, DOCX y XLSX.
Funciones puras — sin efectos secundarios, testeables con PBT.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_ACCEPTED_CONTENT_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
})

_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@dataclass
class ParsedDocument:
    subject_id: str
    subject_name: str
    program_name: str
    program_type: str   # "MAESTRIA" | "OTRO"
    subject_type: str   # "FUNDAMENTOS" | "CONCENTRACION" | "PROYECTO"
    language: str       # "ES" | "EN" | "BILINGUAL"
    graduation_profile: str
    competencies: list[dict] = field(default_factory=list)
    learning_outcomes: list[dict] = field(default_factory=list)
    syllabus: str = ""
    source_file: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


def validate_upload(file_name: str, file_size_bytes: int, content_type: str) -> ValidationResult:
    """
    Valida formato y tamaño del archivo antes de la carga. (BR-W01, BR-W02)
    Función pura — invariante: retorna ValidationResult siempre.
    """
    errors: list[str] = []

    # Validar formato (BR-W01)
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if ext not in {"pdf", "docx", "xlsx"} and content_type not in _ACCEPTED_CONTENT_TYPES:
        errors.append(f"Formato no soportado: '{ext}'. Use PDF, DOCX o XLSX.")

    # Validar tamaño (BR-W02)
    if file_size_bytes > _MAX_FILE_SIZE_BYTES:
        mb = file_size_bytes / (1024 * 1024)
        errors.append(f"Archivo demasiado grande: {mb:.1f}MB. Máximo permitido: 50MB.")

    return ValidationResult(is_valid=len(errors) == 0, errors=errors)


def detect_program_type(text: str) -> str:
    """Detecta si el programa es Maestría u otro nivel. Función pura."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["maestría", "maestria", "master", "msc", "m.sc"]):
        return "MAESTRIA"
    return "OTRO"


def detect_subject_type(text: str) -> str:
    """Detecta el tipo de materia. Función pura."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["proyecto", "project", "tesis", "thesis"]):
        return "PROYECTO"
    if any(kw in text_lower for kw in ["concentración", "concentracion", "especialización", "advanced"]):
        return "CONCENTRACION"
    return "FUNDAMENTOS"


def extract_learning_outcomes(text: str) -> list[dict]:
    """
    Extrae Resultados de Aprendizaje del texto del documento.
    Busca patrones: 'RA1:', 'RA 1.', 'Resultado 1:', etc.
    Función pura.
    """
    patterns = [
        r"RA\s*(\d+)[:\.\)]\s*(.+?)(?=RA\s*\d+|$)",
        r"Resultado\s+(?:de\s+[Aa]prendizaje\s+)?(\d+)[:\.\)]\s*(.+?)(?=Resultado|$)",
        r"(\d+)\.\s+(?:El\s+estudiante\s+)?([A-ZÁÉÍÓÚ][^.]+\.)",
    ]
    outcomes = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            for i, (num, desc) in enumerate(matches):
                desc_clean = " ".join(desc.strip().split())[:500]
                if len(desc_clean) > 10:
                    outcomes.append({"ra_id": f"RA{num.strip()}", "description": desc_clean})
            break
    return outcomes


def extract_competencies(text: str) -> list[dict]:
    """
    Extrae competencias del texto del documento.
    Busca patrones: 'C1:', 'Competencia 1:', etc.
    Función pura.
    """
    patterns = [
        r"C\s*(\d+)[:\.\)]\s*(.+?)(?=C\s*\d+|$)",
        r"Competencia\s+(\d+)[:\.\)]\s*(.+?)(?=Competencia|$)",
    ]
    competencies = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            for num, desc in matches:
                desc_clean = " ".join(desc.strip().split())[:500]
                if len(desc_clean) > 10:
                    competencies.append({"competency_id": f"C{num.strip()}", "description": desc_clean})
            break
    return competencies


def parse_text_to_document(
    text: str,
    subject_id: str,
    source_file: str = "",
) -> ParsedDocument:
    """
    Parsea texto extraído de un documento a ParsedDocument.
    Función pura — sin efectos secundarios.
    Invariante: siempre retorna ParsedDocument con subject_id válido.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    subject_name = lines[0][:255] if lines else "Asignatura sin nombre"
    program_name = lines[1][:255] if len(lines) > 1 else "Programa sin nombre"

    program_type = detect_program_type(text)
    subject_type = detect_subject_type(text)

    # Detectar idioma
    language = "ES"
    if re.search(r"\b(learning outcome|competency|syllabus)\b", text, re.IGNORECASE):
        language = "EN" if not re.search(r"\b(resultado|competencia|temario)\b", text, re.IGNORECASE) else "BILINGUAL"

    # Extraer perfil de egreso
    profile_match = re.search(
        r"(?:perfil\s+de\s+egreso|graduation\s+profile)[:\s]+(.+?)(?=\n\n|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    graduation_profile = " ".join(profile_match.group(1).split())[:1000] if profile_match else program_name

    learning_outcomes = extract_learning_outcomes(text)
    competencies = extract_competencies(text)

    # Fallback: si no se detectaron RA, crear uno genérico
    if not learning_outcomes:
        learning_outcomes = [{"ra_id": "RA1", "description": f"Desarrollar competencias en {subject_name}"}]
    if not competencies:
        competencies = [{"competency_id": "C1", "description": f"Competencia profesional en {program_name}"}]

    return ParsedDocument(
        subject_id=subject_id,
        subject_name=subject_name,
        program_name=program_name,
        program_type=program_type,
        subject_type=subject_type,
        language=language,
        graduation_profile=graduation_profile,
        competencies=competencies,
        learning_outcomes=learning_outcomes,
        source_file=source_file,
    )
