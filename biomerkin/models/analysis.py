"""
Combined analysis results data models.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
from .genomics import GenomicsResults
from .proteomics import ProteomicsResults
from .literature import LiteratureResults
from .drug import DrugResults
from .medical import MedicalReport


@dataclass
class CombinedAnalysis:
    """Combined results from all analysis agents."""
    workflow_id: str
    genomics_results: Optional[GenomicsResults]
    proteomics_results: Optional[ProteomicsResults]
    literature_results: Optional[LiteratureResults]
    drug_results: Optional[DrugResults]
    medical_report: Optional[MedicalReport]
    analysis_start_time: datetime
    analysis_end_time: Optional[datetime] = None
    total_processing_time: Optional[float] = None  # in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'workflow_id': self.workflow_id,
            'genomics_results': self.genomics_results.to_dict() if self.genomics_results else None,
            'proteomics_results': self.proteomics_results.to_dict() if self.proteomics_results else None,
            'literature_results': self.literature_results.to_dict() if self.literature_results else None,
            'drug_results': self.drug_results.to_dict() if self.drug_results else None,
            'medical_report': self.medical_report.to_dict() if self.medical_report else None,
            'analysis_start_time': self.analysis_start_time.isoformat(),
            'analysis_end_time': self.analysis_end_time.isoformat() if self.analysis_end_time else None,
            'total_processing_time': self.total_processing_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CombinedAnalysis':
        """Create instance from dictionary."""
        genomics_results = None
        if data.get('genomics_results'):
            genomics_results = GenomicsResults.from_dict(data['genomics_results'])
        
        proteomics_results = None
        if data.get('proteomics_results'):
            proteomics_results = ProteomicsResults.from_dict(data['proteomics_results'])
        
        literature_results = None
        if data.get('literature_results'):
            literature_results = LiteratureResults.from_dict(data['literature_results'])
        
        drug_results = None
        if data.get('drug_results'):
            drug_results = DrugResults.from_dict(data['drug_results'])
        
        medical_report = None
        if data.get('medical_report'):
            medical_report = MedicalReport.from_dict(data['medical_report'])
        
        analysis_end_time = None
        if data.get('analysis_end_time'):
            analysis_end_time = datetime.fromisoformat(data['analysis_end_time'])
        
        return cls(
            workflow_id=data['workflow_id'],
            genomics_results=genomics_results,
            proteomics_results=proteomics_results,
            literature_results=literature_results,
            drug_results=drug_results,
            medical_report=medical_report,
            analysis_start_time=datetime.fromisoformat(data['analysis_start_time']),
            analysis_end_time=analysis_end_time,
            total_processing_time=data.get('total_processing_time')
        )


@dataclass
class AnalysisResults:
    """Final analysis results for API responses."""
    success: bool
    workflow_id: str
    results: Optional[CombinedAnalysis]
    error_message: Optional[str] = None
    warnings: Optional[list] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'success': self.success,
            'workflow_id': self.workflow_id,
            'results': self.results.to_dict() if self.results else None,
            'error_message': self.error_message,
            'warnings': self.warnings
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResults':
        """Create instance from dictionary."""
        results = None
        if data.get('results'):
            results = CombinedAnalysis.from_dict(data['results'])
        
        return cls(
            success=data['success'],
            workflow_id=data['workflow_id'],
            results=results,
            error_message=data.get('error_message'),
            warnings=data.get('warnings')
        )