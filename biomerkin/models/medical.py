"""
Data models for medical reports and treatment recommendations.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk assessment levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TreatmentType(Enum):
    """Types of treatments."""
    MEDICATION = "medication"
    SURGERY = "surgery"
    LIFESTYLE = "lifestyle"
    MONITORING = "monitoring"
    GENETIC_COUNSELING = "genetic_counseling"
    PREVENTIVE = "preventive"


@dataclass
class RiskFactor:
    """Represents a genetic or clinical risk factor."""
    factor_name: str
    risk_level: RiskLevel
    description: str
    genetic_basis: Optional[str] = None
    prevalence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['risk_level'] = self.risk_level.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskFactor':
        """Create instance from dictionary."""
        data['risk_level'] = RiskLevel(data['risk_level'])
        return cls(**data)


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment based on genetic analysis."""
    overall_risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    protective_factors: List[str]
    recommendations: List[str]
    confidence_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'overall_risk_level': self.overall_risk_level.value,
            'risk_factors': [factor.to_dict() for factor in self.risk_factors],
            'protective_factors': self.protective_factors,
            'recommendations': self.recommendations,
            'confidence_score': self.confidence_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RiskAssessment':
        """Create instance from dictionary."""
        return cls(
            overall_risk_level=RiskLevel(data['overall_risk_level']),
            risk_factors=[RiskFactor.from_dict(factor) for factor in data.get('risk_factors', [])],
            protective_factors=data.get('protective_factors', []),
            recommendations=data.get('recommendations', []),
            confidence_score=data.get('confidence_score', 0.0)
        )


@dataclass
class TreatmentOption:
    """Represents a treatment option."""
    treatment_id: str
    name: str
    treatment_type: TreatmentType
    description: str
    effectiveness_rating: float
    evidence_level: str  # A, B, C, D based on clinical evidence
    contraindications: List[str]
    monitoring_requirements: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['treatment_type'] = self.treatment_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TreatmentOption':
        """Create instance from dictionary."""
        data['treatment_type'] = TreatmentType(data['treatment_type'])
        return cls(**data)


@dataclass
class DrugRecommendation:
    """Specific drug recommendation with rationale."""
    drug_name: str
    drug_id: str
    dosage_recommendation: str
    rationale: str
    expected_benefit: str
    monitoring_parameters: List[str]
    duration: Optional[str] = None
    alternatives: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DrugRecommendation':
        """Create instance from dictionary."""
        return cls(**data)


@dataclass
class MedicalReport:
    """Comprehensive medical report combining all analysis results."""
    patient_id: str
    report_id: str
    analysis_summary: str
    genetic_findings: str
    protein_analysis: str
    literature_insights: str
    drug_recommendations: List[DrugRecommendation]
    treatment_options: List[TreatmentOption]
    risk_assessment: RiskAssessment
    clinical_recommendations: List[str]
    follow_up_recommendations: List[str]
    generated_date: datetime
    report_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'patient_id': self.patient_id,
            'report_id': self.report_id,
            'analysis_summary': self.analysis_summary,
            'genetic_findings': self.genetic_findings,
            'protein_analysis': self.protein_analysis,
            'literature_insights': self.literature_insights,
            'drug_recommendations': [rec.to_dict() for rec in self.drug_recommendations],
            'treatment_options': [option.to_dict() for option in self.treatment_options],
            'risk_assessment': self.risk_assessment.to_dict(),
            'clinical_recommendations': self.clinical_recommendations,
            'follow_up_recommendations': self.follow_up_recommendations,
            'generated_date': self.generated_date.isoformat(),
            'report_version': self.report_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MedicalReport':
        """Create instance from dictionary."""
        return cls(
            patient_id=data['patient_id'],
            report_id=data['report_id'],
            analysis_summary=data['analysis_summary'],
            genetic_findings=data['genetic_findings'],
            protein_analysis=data['protein_analysis'],
            literature_insights=data['literature_insights'],
            drug_recommendations=[DrugRecommendation.from_dict(rec) for rec in data.get('drug_recommendations', [])],
            treatment_options=[TreatmentOption.from_dict(option) for option in data.get('treatment_options', [])],
            risk_assessment=RiskAssessment.from_dict(data.get('risk_assessment', {})),
            clinical_recommendations=data.get('clinical_recommendations', []),
            follow_up_recommendations=data.get('follow_up_recommendations', []),
            generated_date=datetime.fromisoformat(data['generated_date']),
            report_version=data.get('report_version', '1.0')
        )