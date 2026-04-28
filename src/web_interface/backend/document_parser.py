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
    # Check for explicit "Bloque:" label first (Anáhuac format)
    bloque_match = re.search(r"[Bb]loque[:\s]+(\w+)", text)
    if bloque_match:
        bloque = bloque_match.group(1).lower()
        if bloque in ("profesional", "fundamentos", "básico", "basico"):
            return "FUNDAMENTOS"
        if bloque in ("concentración", "concentracion", "especialización"):
            return "CONCENTRACION"
        if bloque in ("proyecto", "integrador", "terminal"):
            return "PROYECTO"
    # Fallback to keyword detection
    if any(kw in text_lower for kw in ["tipo: proyecto", "bloque: proyecto", "tesis", "thesis"]):
        return "PROYECTO"
    if any(kw in text_lower for kw in ["tipo: concentracion", "concentración", "especialización", "advanced"]):
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
    Maneja formato Anáhuac (tablas con labels) y texto plano.
    Función pura — sin efectos secundarios.
    """
    # Try structured extraction first (Anáhuac DOCX format)
    subject_name = _extract_field(text, [
        r"[Dd]enominaci[oó]n\s+de\s+la\s+asignatura[:\s|]+(.+?)(?:\n|\|)",
        r"[Nn]ombre\s+de\s+la\s+asignatura[:\s|]+(.+?)(?:\n|\|)",
        r"[Aa]signatura[:\s|]+(.+?)(?:\n|\|)",
    ])
    if not subject_name:
        # Fallback: first non-empty line
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        subject_name = lines[0][:255] if lines else "Asignatura sin nombre"

    # Program name from filename or text
    program_name = _extract_field(text, [
        r"[Pp]rograma[:\s|]+(.+?)(?:\n|\|)",
        r"[Mm]aestr[ií]a\s+en\s+(.+?)(?:\n|\|)",
    ])
    if not program_name:
        # Try to extract from filename: OK_PA001_MADTFIN_...
        fn_match = re.search(r"MADTFIN|MADIA|MADCI", source_file)
        if fn_match:
            program_name = "Maestria en Direccion y Tecnologia Financiera - Anahuac Online"
        else:
            program_name = "Programa sin nombre"

    program_type = detect_program_type(text)
    subject_type = detect_subject_type(text)

    # Detect language
    language = "ES"
    if re.search(r"\b(learning outcome|competency|syllabus)\b", text, re.IGNORECASE):
        language = "EN" if not re.search(r"\b(resultado|competencia|temario)\b", text, re.IGNORECASE) else "BILINGUAL"

    # Extract graduation profile
    profile_match = re.search(
        r"(?:perfil\s+de\s+egreso|graduation\s+profile|[Pp]erfil\s+m[ií]nimo)[:\s]+(.+?)(?=\n\n|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    graduation_profile = " ".join(profile_match.group(1).split())[:1000] if profile_match else ""

    # Extract learning outcomes — Anáhuac format: "Fines de aprendizaje / Resultados de aprendizaje:"
    learning_outcomes = _extract_learning_outcomes_structured(text)
    if not learning_outcomes:
        learning_outcomes = extract_learning_outcomes(text)

    # Extract competencies
    competencies = extract_competencies(text)

    # Extract syllabus — Anáhuac format: "Contenido temático:"
    syllabus = _extract_syllabus(text)

    # Fallbacks
    if not learning_outcomes:
        learning_outcomes = [{"ra_id": "RA1", "description": f"Desarrollar competencias en {subject_name}"}]
    if not competencies:
        # Use program-level competencies for MADTFIN
        if "MADTFIN" in source_file or "financ" in text.lower():
            competencies = [
                {"competency_id": "C1", "description": "PENSAMIENTO CRITICO - Analiza informacion y argumentos financieros para sustentar juicios profesionales"},
                {"competency_id": "C2", "description": "PENSAMIENTO INNOVADOR - Disena soluciones financieras mediante enfoques innovadores basados en datos"},
                {"competency_id": "C3", "description": "PENSAMIENTO RELACIONAL - Integra comprension sistemica de mercados y variables macro financieras"},
                {"competency_id": "C4", "description": "PENSAMIENTO ETICO Y MORAL - Aplica criterios eticos en decisiones financieras"},
            ]
        else:
            competencies = [{"competency_id": "C1", "description": f"Competencia profesional en {program_name}"}]

    if not graduation_profile:
        graduation_profile = f"Profesional capaz de aplicar conocimientos de {subject_name} en contextos organizacionales."

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
        syllabus=syllabus,
        source_file=source_file,
    )


def _extract_field(text: str, patterns: list[str]) -> str:
    """Try multiple regex patterns and return the first match."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Clean up pipe separators and extra whitespace
            value = re.sub(r'\s*\|\s*', ' ', value).strip()
            if len(value) > 5:
                return value[:255]
    return ""


def _extract_learning_outcomes_structured(text: str) -> list[dict]:
    """Extract learning outcomes from Anáhuac structured format."""
    # Find the "Fines de aprendizaje" or "Resultados de aprendizaje" section
    ra_match = re.search(
        r"(?:Fines\s+de\s+aprendizaje|Resultados\s+de\s+aprendizaje)[^:]*:\s*(?:El\s+estudiante:?)?\s*(.+?)(?=Contenido\s+tem[aá]tico|Actividades\s+de\s+aprendizaje|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    if not ra_match:
        return []

    ra_text = ra_match.group(1).strip()
    # Split by sentences that start with a verb (Bloom taxonomy)
    bloom_verbs = r"(?:Aplica|Analiza|Evalúa|Evalua|Crea|Diseña|Disena|Construye|Identifica|Describe|Compara|Justifica|Examina|Interpreta|Desarrolla|Integra|Propone|Selecciona|Argumenta|Demuestra)"
    sentences = re.split(rf"(?={bloom_verbs})", ra_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

    outcomes = []
    for i, sentence in enumerate(sentences):
        clean = " ".join(sentence.split())[:500]
        outcomes.append({"ra_id": f"RA{i+1}", "description": clean})

    return outcomes


def _extract_syllabus(text: str) -> str:
    """Extract syllabus/content topics from Anáhuac structured format."""
    # Extract duration
    duration_match = re.search(r"[Dd]uraci[oó]n\s+del\s+ciclo[:\s]*(\d+)\s*semanas", text, re.IGNORECASE)
    num_weeks = int(duration_match.group(1)) if duration_match else 0

    # Extract credits
    credits_match = re.search(r"[Cc]r[eé]ditos[:\s]*(\d+)", text)
    credits = int(credits_match.group(1)) if credits_match else 0

    syllabus_match = re.search(
        r"[Cc]ontenido\s+tem[aá]tico[:\s]*(.+?)(?=Actividades\s+de\s+aprendizaje|Criterios\s+de\s+evaluaci[oó]n|Software|Recursos\s+[Bb]ibliogr[aá]ficos|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    if not syllabus_match:
        return ""

    raw = syllabus_match.group(1).strip()
    # Clean up: remove pipe separators, normalize whitespace
    raw = re.sub(r'\s*\|\s*', '\n', raw)
    lines = [l.strip() for l in raw.split("\n") if l.strip() and len(l.strip()) > 3]

    # Group into numbered topics
    topics = []
    current_topic = []
    for line in lines:
        # New topic starts with a line that looks like a heading (no verb prefix, often capitalized)
        if current_topic and len(current_topic) >= 3 and not line[0].islower():
            topics.append(" — ".join(current_topic))
            current_topic = [line]
        else:
            current_topic.append(line)
    if current_topic:
        topics.append(" — ".join(current_topic))

    # Build syllabus string with duration info
    numbered = [f"{i+1}) {t}" for i, t in enumerate(topics)]
    result = "Contenido tematico: " + ". ".join(numbered)

    # Append duration and credits
    meta_parts = []
    if num_weeks:
        meta_parts.append(f"Duracion: {num_weeks} semanas")
    if credits:
        meta_parts.append(f"{credits} creditos")
    if meta_parts:
        result += ". " + ", ".join(meta_parts) + "."

    return result
