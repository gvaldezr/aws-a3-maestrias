# Entidades de Dominio — U2: Agente Scholar

## Paper
```python
@dataclass
class Paper:
    scopus_id: str
    title: str
    authors: list[str]
    year: int
    journal: str
    quartile: str          # "Q1" | "Q2"
    key_finding: str
    doi: str | None = None
    abstract: str | None = None
    citation_count: int = 0
    relevance_score: float = 0.0  # 0.0–1.0, calculado internamente
```

## KnowledgeMatrixEntry
```python
@dataclass
class KnowledgeMatrixEntry:
    concept: str
    source_paper_id: str
    methodology: str
    executive_application: str
    ra_relevance: list[str]   # lista de ra_id
```

## ScopusSearchQuery
```python
@dataclass
class ScopusSearchQuery:
    keywords: list[str]
    subject_area: str | None = None
    year_from: int = 2019
    quartile_filter: list[str] = field(default_factory=lambda: ["Q1", "Q2"])
    max_results: int = 20
```

## CorpusValidation
```python
@dataclass
class CorpusValidation:
    is_sufficient: bool
    paper_count: int
    min_required: int = 5
    gaps: list[str] = field(default_factory=list)  # RA IDs sin cobertura
```

## ScholarResult
```python
@dataclass
class ScholarResult:
    subject_id: str
    top20_papers: list[Paper]
    knowledge_matrix: list[KnowledgeMatrixEntry]
    search_query: ScopusSearchQuery
    corpus_validation: CorpusValidation
```
