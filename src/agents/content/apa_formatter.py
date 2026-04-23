"""
Formateador de bibliografía APA 7 — U4: Agente Content.
Función pura — sin efectos secundarios, testeable con PBT.
"""
from __future__ import annotations


def format_apa_reference(paper: dict) -> str:
    """
    Formatea un paper en estilo APA 7.
    Formato: Autor(es). (Año). Título. Revista. https://doi.org/...

    Args:
        paper: dict con keys: authors, year, title, journal, doi (opcional)

    Returns:
        String con la referencia APA formateada
    """
    authors = paper.get("authors", ["Autor desconocido"])
    year = paper.get("year", "s.f.")
    title = paper.get("title", "Sin título")
    journal = paper.get("journal", "")
    doi = paper.get("doi")

    # Formatear autores: Apellido, I. para cada uno
    formatted_authors = _format_authors(authors)
    ref = f"{formatted_authors} ({year}). {title}. *{journal}*."
    if doi:
        ref += f" https://doi.org/{doi}"
    return ref


def _format_authors(authors: list[str]) -> str:
    """Formatea lista de autores en estilo APA."""
    if not authors:
        return "Autor desconocido"
    if len(authors) == 1:
        return authors[0]
    if len(authors) <= 20:
        return "; ".join(authors[:-1]) + f" & {authors[-1]}"
    # Más de 20 autores: primeros 19 + ... + último
    return "; ".join(authors[:19]) + f"; ... {authors[-1]}"


def generate_apa_bibliography(papers: list[dict]) -> list[str]:
    """
    Genera la bibliografía completa en formato APA 7.
    Invariante: retorna lista de strings, ordenada alfabéticamente.

    Args:
        papers: lista de dicts de papers (Top 20 de Scopus)

    Returns:
        Lista de strings APA ordenada alfabéticamente
    """
    refs = [format_apa_reference(p) for p in papers]
    return sorted(refs)
