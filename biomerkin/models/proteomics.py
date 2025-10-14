"""
Data models for proteomics analysis results.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class ProteinStructure:
    """Represents 3D protein structure data."""
    pdb_id: Optional[str]
    structure_method: Optional[str]  # X-ray, NMR, etc.
    resolution: Optional[float]
    coordinates: Optional[List[Tuple[float, float, float]]] = None
    secondary_structure: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProteinStructure':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class FunctionAnnotation:
    """Represents functional annotation of a protein."""
    function_type: str
    description: str
    confidence_score: float
    source: str  # UniProt, GO, etc.
    evidence_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionAnnotation':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ProteinDomain:
    """Represents a protein domain."""
    domain_id: str
    name: str
    start_position: int
    end_position: int
    description: Optional[str] = None
    family: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProteinDomain':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ProteinInteraction:
    """Represents protein-protein interaction."""
    partner_protein_id: str
    interaction_type: str
    confidence_score: float
    source_database: str
    experimental_evidence: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProteinInteraction':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class ProteomicsResults:
    """Complete results from proteomics analysis."""
    protein_id: str
    structure_data: Optional[ProteinStructure]
    functional_annotations: List[FunctionAnnotation]
    domains: List[ProteinDomain]
    interactions: List[ProteinInteraction]
    analysis_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'protein_id': self.protein_id,
            'structure_data': self.structure_data.to_dict() if self.structure_data else None,
            'functional_annotations': [ann.to_dict() for ann in self.functional_annotations],
            'domains': [domain.to_dict() for domain in self.domains],
            'interactions': [interaction.to_dict() for interaction in self.interactions],
            'analysis_timestamp': self.analysis_timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProteomicsResults':
        """Create instance from dictionary."""
        structure_data = None
        if data.get('structure_data'):
            structure_data = ProteinStructure.from_dict(data['structure_data'])
        
        return cls(
            protein_id=data['protein_id'],
            structure_data=structure_data,
            functional_annotations=[FunctionAnnotation.from_dict(ann) for ann in data.get('functional_annotations', [])],
            domains=[ProteinDomain.from_dict(domain) for domain in data.get('domains', [])],
            interactions=[ProteinInteraction.from_dict(interaction) for interaction in data.get('interactions', [])],
            analysis_timestamp=data.get('analysis_timestamp')
        )