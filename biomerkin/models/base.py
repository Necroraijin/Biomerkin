"""
Base data models and common types for the Biomerkin system.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json


class WorkflowStatus(Enum):
    """Workflow execution status enumeration."""
    INITIATED = "initiated"
    GENOMICS_PROCESSING = "genomics_processing"
    PROTEOMICS_PROCESSING = "proteomics_processing"
    LITERATURE_PROCESSING = "literature_processing"
    DRUG_PROCESSING = "drug_processing"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"


class MutationType(Enum):
    """Types of genetic mutations."""
    SNP = "single_nucleotide_polymorphism"
    INSERTION = "insertion"
    DELETION = "deletion"
    SUBSTITUTION = "substitution"
    FRAMESHIFT = "frameshift"
    MISSENSE = "missense"
    NONSENSE = "nonsense"
    SILENT = "silent"
    INVERSION = "inversion"
    TRANSLOCATION = "translocation"


@dataclass
class GenomicLocation:
    """Represents a genomic location."""
    chromosome: str
    start_position: int
    end_position: int
    strand: Optional[str] = None


@dataclass
class QualityMetrics:
    """Quality metrics for genomic analysis."""
    coverage_depth: float
    quality_score: float
    confidence_level: float
    coverage: float
    accuracy: float
    error_rate: Optional[float] = None


@dataclass
class WorkflowError:
    """Represents an error that occurred during workflow execution."""
    agent: str
    error_type: str
    message: str
    timestamp: datetime
    recoverable: bool = True


@dataclass
class WorkflowState:
    """Manages the state of a workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    current_agent: str
    progress_percentage: float
    results: Dict[str, Any]
    errors: List[WorkflowError]
    created_at: datetime
    updated_at: datetime
    input_data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create instance from dictionary."""
        data['status'] = WorkflowStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['errors'] = [WorkflowError(**error) for error in data.get('errors', [])]
        data['input_data'] = data.get('input_data', {})
        return cls(**data)