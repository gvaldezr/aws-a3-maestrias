"""Modelos de dominio — U2: Agente Scholar."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Paper:
    scopus_id: str
    title: str
    authors: list[str]
    year: int
    journal: str
    quartile: str  # "Q1" | "Q2"
    key_finding: str
    doi: str | None = None
    abstract: str | None = None
    citation_count: int = 0
    relevance_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "scopus_id": self.scopus_id,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "quartile": self.quartile,
            "key_finding": self.key_finding,
            "doi": self.doi,
        }


@dataclass
class KnowledgeMatrixEntry:
    concept: str
    source_paper_id: str
    methodology: str
    executive_application: str
    ra_relevance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "concept": self.concept,
            "source_paper_id": self.source_paper_id,
            "methodology": self.methodology,
            "executive_application": self.executive_application,
            "ra_relevance": self.ra_relevance,
        }


@dataclass
class ScopusSearchQuery:
    keywords: list[str]
    subject_area: str | None = None
    year_from: int = 2019
    quartile_filter: list[str] = field(default_factory=lambda: ["Q1", "Q2"])
    max_results: int = 20


@dataclass
class CorpusValidation:
    is_sufficient: bool
    paper_count: int
    min_required: int = 5
    gaps: list[str] = field(default_factory=list)


@dataclass
class ScholarResult:
    subject_id: str
    top20_papers: list[Paper]
    knowledge_matrix: list[KnowledgeMatrixEntry]
    search_query: ScopusSearchQuery
    corpus_validation: CorpusValidation
