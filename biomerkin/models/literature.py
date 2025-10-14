"""
Data models for literature research results.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Article:
    """Represents a scientific article from literature search."""
    pmid: str  # PubMed ID
    title: str
    authors: List[str]
    journal: str
    publication_date: str
    abstract: str
    doi: Optional[str] = None
    relevance_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Article':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class StudySummary:
    """Represents a summary of a research study."""
    study_type: str  # clinical trial, observational, meta-analysis, etc.
    key_findings: List[str]
    sample_size: Optional[int] = None
    statistical_significance: Optional[str] = None
    limitations: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudySummary':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class LiteratureSummary:
    """Complete summary of literature research results."""
    search_terms: List[str]
    total_articles_found: int
    articles_analyzed: int
    key_findings: List[str]
    relevant_studies: List[StudySummary]
    research_gaps: List[str]
    confidence_level: float
    analysis_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'search_terms': self.search_terms,
            'total_articles_found': self.total_articles_found,
            'articles_analyzed': self.articles_analyzed,
            'key_findings': self.key_findings,
            'relevant_studies': [study.to_dict() for study in self.relevant_studies],
            'research_gaps': self.research_gaps,
            'confidence_level': self.confidence_level,
            'analysis_timestamp': self.analysis_timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiteratureSummary':
        """Create instance from dictionary."""
        return cls(
            search_terms=data.get('search_terms', []),
            total_articles_found=data.get('total_articles_found', 0),
            articles_analyzed=data.get('articles_analyzed', 0),
            key_findings=data.get('key_findings', []),
            relevant_studies=[StudySummary.from_dict(study) for study in data.get('relevant_studies', [])],
            research_gaps=data.get('research_gaps', []),
            confidence_level=data.get('confidence_level', 0.0),
            analysis_timestamp=data.get('analysis_timestamp')
        )


@dataclass
class LiteratureResults:
    """Complete results from literature analysis."""
    articles: List[Article]
    summary: LiteratureSummary
    search_metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'articles': [article.to_dict() for article in self.articles],
            'summary': self.summary.to_dict(),
            'search_metadata': self.search_metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiteratureResults':
        """Create instance from dictionary."""
        return cls(
            articles=[Article.from_dict(article) for article in data.get('articles', [])],
            summary=LiteratureSummary.from_dict(data.get('summary', {})),
            search_metadata=data.get('search_metadata', {})
        )