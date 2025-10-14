"""
AI Guardrails and Safety Framework for Biomerkin.
Ensures responsible AI usage and medical safety.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from .logging_config import get_logger


class SafetyLevel(Enum):
    """Safety levels for AI outputs."""
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


class MedicalClaimType(Enum):
    """Types of medical claims."""
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    PROGNOSIS = "prognosis"
    DRUG_RECOMMENDATION = "drug_recommendation"
    RISK_ASSESSMENT = "risk_assessment"


@dataclass
class SafetyCheck:
    """Result of a safety check."""
    level: SafetyLevel
    message: str
    confidence: float
    check_type: str
    timestamp: datetime


class AIGuardrails:
    """
    AI Guardrails system for medical AI safety.
    Implements multiple layers of safety checks.
    """
    
    def __init__(self):
        """Initialize AI guardrails."""
        self.logger = get_logger(__name__)
        
        # Medical safety patterns
        self.dangerous_patterns = [
            r"definitive diagnosis",
            r"certain cancer",
            r"guaranteed cure",
            r"100% effective",
            r"no side effects",
            r"immediate treatment",
            r"emergency surgery",
            r"life-threatening"
        ]
        
        self.warning_patterns = [
            r"high risk",
            r"serious condition",
            r"urgent care",
            r"consult doctor",
            r"medical emergency",
            r"adverse effects",
            r"contraindication"
        ]
        
        # Medical disclaimer patterns
        self.disclaimer_patterns = [
            r"not a substitute",
            r"consult healthcare",
            r"for research only",
            r"not medical advice",
            r"preliminary analysis"
        ]
    
    def check_medical_output(self, output: str, context: Dict[str, Any]) -> List[SafetyCheck]:
        """
        Comprehensive safety check for medical AI outputs.
        
        Args:
            output: AI-generated text to check
            context: Context about the analysis
            
        Returns:
            List of safety check results
        """
        checks = []
        
        # Check for dangerous medical claims
        checks.extend(self._check_dangerous_claims(output))
        
        # Check for missing disclaimers
        checks.extend(self._check_disclaimers(output))
        
        # Check for overconfidence
        checks.extend(self._check_overconfidence(output))
        
        # Check for inappropriate recommendations
        checks.extend(self._check_inappropriate_recommendations(output, context))
        
        # Check for bias indicators
        checks.extend(self._check_bias_indicators(output))
        
        return checks
    
    def _check_dangerous_claims(self, output: str) -> List[SafetyCheck]:
        """Check for dangerous medical claims."""
        checks = []
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                checks.append(SafetyCheck(
                    level=SafetyLevel.DANGEROUS,
                    message=f"Dangerous medical claim detected: {pattern}",
                    confidence=0.9,
                    check_type="dangerous_claim",
                    timestamp=datetime.now()
                ))
        
        return checks
    
    def _check_disclaimers(self, output: str) -> List[SafetyCheck]:
        """Check for appropriate medical disclaimers."""
        checks = []
        
        has_disclaimer = any(
            re.search(pattern, output, re.IGNORECASE) 
            for pattern in self.disclaimer_patterns
        )
        
        if not has_disclaimer:
            checks.append(SafetyCheck(
                level=SafetyLevel.WARNING,
                message="Missing medical disclaimer - output may be interpreted as medical advice",
                confidence=0.8,
                check_type="missing_disclaimer",
                timestamp=datetime.now()
            ))
        
        return checks
    
    def _check_overconfidence(self, output: str) -> List[SafetyCheck]:
        """Check for overconfident language."""
        checks = []
        
        overconfident_patterns = [
            r"definitely",
            r"certainly",
            r"without doubt",
            r"proven fact",
            r"established truth"
        ]
        
        for pattern in overconfident_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                checks.append(SafetyCheck(
                    level=SafetyLevel.WARNING,
                    message=f"Overconfident language detected: {pattern}",
                    confidence=0.7,
                    check_type="overconfidence",
                    timestamp=datetime.now()
                ))
        
        return checks
    
    def _check_inappropriate_recommendations(self, output: str, context: Dict[str, Any]) -> List[SafetyCheck]:
        """Check for inappropriate medical recommendations."""
        checks = []
        
        # Check if output contains drug recommendations without proper context
        drug_patterns = [
            r"take \w+",
            r"prescribe \w+",
            r"use \w+ medication",
            r"start \w+ therapy"
        ]
        
        has_drug_recommendation = any(
            re.search(pattern, output, re.IGNORECASE) 
            for pattern in drug_patterns
        )
        
        if has_drug_recommendation:
            # Check if proper context is provided
            if not context.get("has_proper_context", False):
                checks.append(SafetyCheck(
                    level=SafetyLevel.DANGEROUS,
                    message="Drug recommendation without proper medical context",
                    confidence=0.9,
                    check_type="inappropriate_drug_recommendation",
                    timestamp=datetime.now()
                ))
        
        return checks
    
    def _check_bias_indicators(self, output: str) -> List[SafetyCheck]:
        """Check for potential bias indicators."""
        checks = []
        
        bias_patterns = [
            r"all \w+ patients",
            r"typical \w+ person",
            r"normal \w+ individual",
            r"standard \w+ case"
        ]
        
        for pattern in bias_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                checks.append(SafetyCheck(
                    level=SafetyLevel.WARNING,
                    message=f"Potential bias indicator: {pattern}",
                    confidence=0.6,
                    check_type="bias_indicator",
                    timestamp=datetime.now()
                ))
        
        return checks
    
    def sanitize_output(self, output: str, safety_checks: List[SafetyCheck]) -> Tuple[str, List[SafetyCheck]]:
        """
        Sanitize output based on safety checks.
        
        Args:
            output: Original output
            safety_checks: Results of safety checks
            
        Returns:
            Tuple of (sanitized_output, remaining_checks)
        """
        sanitized = output
        remaining_checks = []
        
        for check in safety_checks:
            if check.level == SafetyLevel.BLOCKED:
                # Block the entire output
                sanitized = "This analysis has been blocked due to safety concerns. Please consult a healthcare professional."
                remaining_checks.append(check)
            elif check.level == SafetyLevel.DANGEROUS:
                # Add warning and disclaimer
                sanitized = self._add_safety_warning(sanitized, check)
                remaining_checks.append(check)
            elif check.level == SafetyLevel.WARNING:
                # Add disclaimer
                sanitized = self._add_disclaimer(sanitized)
                remaining_checks.append(check)
        
        return sanitized, remaining_checks
    
    def _add_safety_warning(self, output: str, check: SafetyCheck) -> str:
        """Add safety warning to output."""
        warning = f"""
        
        ⚠️ SAFETY WARNING: {check.message}
        
        This analysis contains potentially dangerous medical claims and should not be used for clinical decision-making.
        Please consult a qualified healthcare professional for medical advice.
        
        """
        return warning + output
    
    def _add_disclaimer(self, output: str) -> str:
        """Add medical disclaimer to output."""
        disclaimer = """
        
        ⚠️ MEDICAL DISCLAIMER:
        This analysis is for research and educational purposes only. It is not intended as medical advice, diagnosis, or treatment recommendation. Always consult with a qualified healthcare professional for medical decisions.
        
        """
        return disclaimer + output
    
    def generate_safety_report(self, safety_checks: List[SafetyCheck]) -> Dict[str, Any]:
        """Generate comprehensive safety report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": len(safety_checks),
            "safety_levels": {},
            "check_types": {},
            "recommendations": []
        }
        
        # Count by safety level
        for check in safety_checks:
            level = check.level.value
            report["safety_levels"][level] = report["safety_levels"].get(level, 0) + 1
            
            check_type = check.check_type
            report["check_types"][check_type] = report["check_types"].get(check_type, 0) + 1
        
        # Generate recommendations
        if report["safety_levels"].get("dangerous", 0) > 0:
            report["recommendations"].append("Review and sanitize dangerous medical claims")
        
        if report["safety_levels"].get("warning", 0) > 0:
            report["recommendations"].append("Add appropriate medical disclaimers")
        
        if report["safety_levels"].get("blocked", 0) > 0:
            report["recommendations"].append("Output blocked - manual review required")
        
        return report


# Global guardrails instance
ai_guardrails = AIGuardrails()

