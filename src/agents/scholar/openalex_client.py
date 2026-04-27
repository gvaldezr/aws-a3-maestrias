"""
OpenAlex API Client — free, open source complement to Scopus.
Provides abstracts for papers that Scopus API key doesn't cover.
https://docs.openalex.org/
"""
from __future__ import annotations

import httpx
import time


def fetch_abstract_by_doi(doi: str) -> str:
    """Fetch abstract from OpenAlex using DOI. Returns empty string if not found."""
    if not doi:
        return ""
    try:
        url = f"https://api.openalex.org/works/doi:{doi}"
        resp = httpx.get(url, headers={"User-Agent": "academic-pipeline/1.0"}, timeout=10.0)
        if resp.status_code != 200:
            return ""
        data = resp.json()
        # OpenAlex stores abstract as inverted index — reconstruct it
        abstract_inv = data.get("abstract_inverted_index", {})
        if abstract_inv:
            return _reconstruct_abstract(abstract_inv)
        return ""
    except Exception:
        return ""


def fetch_abstracts_batch(papers: list, max_papers: int = 20, delay: float = 0.2) -> dict:
    """Fetch abstracts for a batch of papers using their DOIs.
    
    Returns dict mapping scopus_id -> abstract text.
    Respects OpenAlex rate limits (10 req/sec for polite pool).
    """
    results = {}
    for paper in papers[:max_papers]:
        doi = paper.get("doi", "")
        scopus_id = paper.get("scopus_id", "")
        if not doi or not scopus_id:
            continue
        abstract = fetch_abstract_by_doi(doi)
        if abstract:
            results[scopus_id] = abstract
        time.sleep(delay)  # Rate limiting
    return results


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract text from OpenAlex inverted index format.
    
    OpenAlex stores abstracts as {word: [position1, position2, ...]}
    We need to reconstruct the original text.
    """
    if not inverted_index:
        return ""
    # Build position -> word mapping
    positions = {}
    for word, pos_list in inverted_index.items():
        for pos in pos_list:
            positions[pos] = word
    # Reconstruct in order
    if not positions:
        return ""
    max_pos = max(positions.keys())
    words = [positions.get(i, "") for i in range(max_pos + 1)]
    return " ".join(w for w in words if w)
