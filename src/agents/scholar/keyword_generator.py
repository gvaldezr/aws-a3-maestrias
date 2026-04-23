"""
Generador de keywords de búsqueda para Scopus.
Función pura — sin efectos secundarios, testeable con PBT.
"""
from __future__ import annotations

import re

# Stopwords académicas a excluir de las keywords
_STOPWORDS = frozenset({
    "el", "la", "los", "las", "un", "una", "de", "del", "en", "y", "o",
    "que", "con", "para", "por", "the", "a", "an", "of", "in", "and",
    "or", "to", "for", "with", "on", "at", "from", "is", "are", "be",
    "will", "can", "should", "must", "may", "its", "their", "this", "that",
})

_MIN_KEYWORD_LENGTH = 4
_MAX_KEYWORDS = 10


def generate_search_keywords(
    learning_outcomes: list[dict],
    competencies: list[dict],
) -> list[str]:
    """
    Genera keywords de búsqueda a partir de RA y competencias.
    Retorna lista de 5–10 keywords ordenadas por frecuencia descendente.

    Args:
        learning_outcomes: lista de dicts con campo 'description'
        competencies: lista de dicts con campo 'description'

    Returns:
        Lista de keywords únicas, sin stopwords, longitud >= 4 chars
    """
    texts = (
        [lo["description"] for lo in learning_outcomes]
        + [c["description"] for c in competencies]
    )
    all_text = " ".join(texts).lower()
    tokens = re.findall(r"[a-záéíóúüña-z]{4,}", all_text)

    freq: dict[str, int] = {}
    for token in tokens:
        if token not in _STOPWORDS and len(token) >= _MIN_KEYWORD_LENGTH:
            freq[token] = freq.get(token, 0) + 1

    sorted_keywords = sorted(freq, key=lambda k: freq[k], reverse=True)
    return sorted_keywords[:_MAX_KEYWORDS]
