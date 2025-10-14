"""
Data models for genomics analysis results.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from .base import GenomicLocation, QualityMetrics, MutationType


@dataclass
class Gene:
    """Represents a gene identified in genomic analysis."""
    id: str
    name: str
    location: GenomicLocation
    function: str
    confidence_score: float
    gene_type: Optional[str] = None
    synonyms: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Gene':
        """Create instance from dictionary."""
        if 'location' in data and isinstance(data['location'], dict):
            data['location'] = GenomicLocation(**data['location'])
        return cls(**data)


@dataclass
class Mutation:
    """Represents a genetic mutation."""
    position: int
    reference_base: str
    alternate_base: str
    mutation_type: MutationType
    clinical_significance: str
    gene_id: Optional[str] = None
    effect_prediction: Optional[str] = None
    frequency: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['mutation_type'] = self.mutation_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mutation':
        """Create instance from dictionary."""
        data['mutation_type'] = MutationType(data['mutation_type'])
        return cls(**data)


@dataclass
class ProteinSequence:
    """Represents a protein sequence derived from DNA."""
    sequence: str
    gene_id: str
    length: int
    molecular_weight: float
    protein_id: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProteinSequence':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class GenomicsResults:
    """Complete results from genomics analysis."""
    genes: List[Gene]
    mutations: List[Mutation]
    protein_sequences: List[ProteinSequence]
    quality_metrics: QualityMetrics
    sequence_length: Optional[int] = None
    analysis_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'genes': [gene.to_dict() for gene in self.genes],
            'mutations': [mutation.to_dict() for mutation in self.mutations],
            'protein_sequences': [seq.to_dict() for seq in self.protein_sequences],
            'quality_metrics': asdict(self.quality_metrics),
            'sequence_length': self.sequence_length,
            'analysis_timestamp': self.analysis_timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenomicsResults':
        """Create instance from dictionary."""
        return cls(
            genes=[Gene.from_dict(gene) for gene in data.get('genes', [])],
            mutations=[Mutation.from_dict(mut) for mut in data.get('mutations', [])],
            protein_sequences=[ProteinSequence.from_dict(seq) for seq in data.get('protein_sequences', [])],
            quality_metrics=QualityMetrics(**data.get('quality_metrics', {})),
            sequence_length=data.get('sequence_length'),
            analysis_timestamp=data.get('analysis_timestamp')
        )