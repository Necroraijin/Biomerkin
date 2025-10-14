"""
Data models for drug discovery and clinical trial results.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from enum import Enum


class TrialPhase(Enum):
    """Clinical trial phases."""
    PRECLINICAL = "preclinical"
    PHASE_0 = "phase_0"
    PHASE_I = "phase_1"
    PHASE_II = "phase_2"
    PHASE_III = "phase_3"
    PHASE_IV = "phase_4"
    APPROVED = "approved"
    WITHDRAWN = "withdrawn"


class DrugType(Enum):
    """Types of drugs."""
    SMALL_MOLECULE = "small_molecule"
    BIOLOGIC = "biologic"
    ANTIBODY = "antibody"
    VACCINE = "vaccine"
    GENE_THERAPY = "gene_therapy"
    CELL_THERAPY = "cell_therapy"


@dataclass
class SideEffect:
    """Represents a drug side effect."""
    name: str
    severity: str  # mild, moderate, severe
    frequency: Optional[str] = None  # common, uncommon, rare
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SideEffect':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class TrialInformation:
    """Represents clinical trial information."""
    trial_id: str
    title: str
    phase: TrialPhase
    status: str  # recruiting, completed, terminated, etc.
    condition: str
    intervention: str
    primary_outcome: Optional[str] = None
    enrollment: Optional[int] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['phase'] = self.phase.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrialInformation':
        """Create instance from dictionary."""
        data['phase'] = TrialPhase(data['phase'])
        return cls(**data)


@dataclass
class DrugCandidate:
    """Represents a potential drug candidate."""
    drug_id: str
    name: str
    drug_type: DrugType
    mechanism_of_action: str
    target_proteins: List[str]
    trial_phase: TrialPhase
    effectiveness_score: float
    side_effects: List[SideEffect]
    indication: Optional[str] = None
    manufacturer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'drug_id': self.drug_id,
            'name': self.name,
            'drug_type': self.drug_type.value,
            'mechanism_of_action': self.mechanism_of_action,
            'target_proteins': self.target_proteins,
            'trial_phase': self.trial_phase.value,
            'effectiveness_score': self.effectiveness_score,
            'side_effects': [effect.to_dict() for effect in self.side_effects],
            'indication': self.indication,
            'manufacturer': self.manufacturer
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DrugCandidate':
        """Create instance from dictionary."""
        return cls(
            drug_id=data['drug_id'],
            name=data['name'],
            drug_type=DrugType(data['drug_type']),
            mechanism_of_action=data['mechanism_of_action'],
            target_proteins=data.get('target_proteins', []),
            trial_phase=TrialPhase(data['trial_phase']),
            effectiveness_score=data.get('effectiveness_score', 0.0),
            side_effects=[SideEffect.from_dict(effect) for effect in data.get('side_effects', [])],
            indication=data.get('indication'),
            manufacturer=data.get('manufacturer')
        )


@dataclass
class InteractionAnalysis:
    """Represents drug-drug interaction analysis."""
    drug_pairs: List[tuple]  # pairs of drug IDs
    interaction_severity: str  # low, moderate, high
    interaction_type: str  # pharmacokinetic, pharmacodynamic
    clinical_significance: str
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractionAnalysis':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class DrugResults:
    """Complete results from drug discovery analysis."""
    target_genes: List[str]
    drug_candidates: List[DrugCandidate]
    clinical_trials: List[TrialInformation]
    interaction_analysis: Optional[InteractionAnalysis]
    analysis_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'target_genes': self.target_genes,
            'drug_candidates': [drug.to_dict() for drug in self.drug_candidates],
            'clinical_trials': [trial.to_dict() for trial in self.clinical_trials],
            'interaction_analysis': self.interaction_analysis.to_dict() if self.interaction_analysis else None,
            'analysis_timestamp': self.analysis_timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DrugResults':
        """Create instance from dictionary."""
        interaction_analysis = None
        if data.get('interaction_analysis'):
            interaction_analysis = InteractionAnalysis.from_dict(data['interaction_analysis'])
        
        return cls(
            target_genes=data.get('target_genes', []),
            drug_candidates=[DrugCandidate.from_dict(drug) for drug in data.get('drug_candidates', [])],
            clinical_trials=[TrialInformation.from_dict(trial) for trial in data.get('clinical_trials', [])],
            interaction_analysis=interaction_analysis,
            analysis_timestamp=data.get('analysis_timestamp')
        )