"""
Secure genomics agent with integrated security features.

This is an example of how to integrate security middleware with existing agents.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .genomics_agent import GenomicsAgent
from ..utils.security_middleware import (
    secure_genomic_operation, with_security_context, validate_genomic_input,
    encrypt_sensitive_fields, audit_data_access, SecurityContext
)
from ..utils.security import SecurityLevel, AuditEventType, log_audit_event
from ..models.genomics import GenomicsResults


class SecureGenomicsAgent(GenomicsAgent):
    """
    Genomics agent with integrated security features.
    
    This agent extends the base GenomicsAgent with:
    - Input validation for DNA sequences
    - Output sanitization and encryption
    - Audit logging for all operations
    - Compliance with security policies
    """
    
    def __init__(self):
        super().__init__()
        self.agent_name = "SecureGenomicsAgent"
    
    @secure_genomic_operation("dna_sequence_analysis")
    @validate_genomic_input
    @encrypt_sensitive_fields("dna_sequence", "mutations")
    @audit_data_access("genomic_data", "analyze_sequence")
    def analyze_sequence(self, sequence_file: str, 
                        security_context: Optional[SecurityContext] = None) -> Dict[str, Any]:
        """
        Analyze DNA sequence with full security integration.
        
        Args:
            sequence_file: Path to DNA sequence file
            security_context: Security context for the operation
            
        Returns:
            Analysis results with security features applied
        """
        # Log the start of analysis
        log_audit_event(
            AuditEventType.DATA_PROCESSING,
            "genomic_data",
            "sequence_analysis_start",
            "success",
            security_context.user_id if security_context else None,
            security_context.workflow_id if security_context else None,
            {"sequence_file": sequence_file}
        )
        
        try:
            # Call the parent class method
            results = super().analyze_sequence(sequence_file)
            
            # Add security metadata
            if isinstance(results, dict):
                results.update({
                    "security_metadata": {
                        "processed_at": datetime.utcnow().isoformat(),
                        "security_level": SecurityLevel.RESTRICTED.value,
                        "data_classification": "genomic",
                        "compliance_frameworks": ["HIPAA", "GDPR"],
                        "encryption_applied": True,
                        "audit_logged": True
                    }
                })
            
            return results
            
        except Exception as e:
            # Log the error
            log_audit_event(
                AuditEventType.ERROR_OCCURRED,
                "genomic_data",
                "sequence_analysis_error",
                "failure",
                security_context.user_id if security_context else None,
                security_context.workflow_id if security_context else None,
                {"error": str(e), "sequence_file": sequence_file}
            )
            raise
    
    @secure_genomic_operation("mutation_detection")
    @validate_genomic_input
    @audit_data_access("genomic_data", "detect_mutations")
    def detect_mutations(self, sequence: str, reference: str,
                        security_context: Optional[SecurityContext] = None) -> List[Dict[str, Any]]:
        """
        Detect mutations with security features.
        
        Args:
            sequence: DNA sequence to analyze
            reference: Reference sequence for comparison
            security_context: Security context for the operation
            
        Returns:
            List of detected mutations with security metadata
        """
        # Validate input sequences
        if not sequence or not reference:
            raise ValueError("Both sequence and reference are required")
        
        # Log the operation
        log_audit_event(
            AuditEventType.DATA_PROCESSING,
            "genomic_data",
            "mutation_detection",
            "success",
            security_context.user_id if security_context else None,
            security_context.workflow_id if security_context else None,
            {
                "sequence_length": len(sequence),
                "reference_length": len(reference)
            }
        )
        
        try:
            # Call the parent class method
            mutations = super().detect_mutations(sequence, reference)
            
            # Add security metadata to each mutation
            for mutation in mutations:
                if isinstance(mutation, dict):
                    mutation["security_metadata"] = {
                        "detected_at": datetime.utcnow().isoformat(),
                        "data_classification": "genomic",
                        "requires_consent": True,
                        "retention_period_years": 7
                    }
            
            return mutations
            
        except Exception as e:
            log_audit_event(
                AuditEventType.ERROR_OCCURRED,
                "genomic_data",
                "mutation_detection_error",
                "failure",
                security_context.user_id if security_context else None,
                security_context.workflow_id if security_context else None,
                {"error": str(e)}
            )
            raise
    
    @secure_genomic_operation("protein_translation")
    @validate_genomic_input
    @encrypt_sensitive_fields("protein_sequence")
    @audit_data_access("genomic_data", "translate_to_protein")
    def translate_to_protein(self, dna_sequence: str,
                           security_context: Optional[SecurityContext] = None) -> List[Dict[str, Any]]:
        """
        Translate DNA to protein sequences with security features.
        
        Args:
            dna_sequence: DNA sequence to translate
            security_context: Security context for the operation
            
        Returns:
            List of protein sequences with security metadata
        """
        log_audit_event(
            AuditEventType.DATA_PROCESSING,
            "genomic_data",
            "protein_translation",
            "success",
            security_context.user_id if security_context else None,
            security_context.workflow_id if security_context else None,
            {"dna_sequence_length": len(dna_sequence)}
        )
        
        try:
            # Call the parent class method
            proteins = super().translate_to_protein(dna_sequence)
            
            # Add security metadata
            for protein in proteins:
                if isinstance(protein, dict):
                    protein["security_metadata"] = {
                        "translated_at": datetime.utcnow().isoformat(),
                        "source_dna_length": len(dna_sequence),
                        "data_classification": "protein",
                        "derived_from_genomic": True
                    }
            
            return proteins
            
        except Exception as e:
            log_audit_event(
                AuditEventType.ERROR_OCCURRED,
                "genomic_data",
                "protein_translation_error",
                "failure",
                security_context.user_id if security_context else None,
                security_context.workflow_id if security_context else None,
                {"error": str(e)}
            )
            raise
    
    @with_security_context(security_level=SecurityLevel.RESTRICTED, data_classification="genomic")
    def secure_batch_analysis(self, sequence_files: List[str],
                            user_id: str, workflow_id: str) -> Dict[str, Any]:
        """
        Perform batch analysis with comprehensive security.
        
        Args:
            sequence_files: List of sequence files to analyze
            user_id: User performing the analysis
            workflow_id: Workflow identifier
            
        Returns:
            Batch analysis results with security features
        """
        batch_results = {
            "batch_id": f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "user_id": user_id,
            "workflow_id": workflow_id,
            "files_processed": 0,
            "files_failed": 0,
            "results": [],
            "security_summary": {
                "total_sequences_analyzed": 0,
                "encryption_applied": True,
                "audit_events_logged": 0,
                "compliance_validated": True
            }
        }
        
        for sequence_file in sequence_files:
            try:
                # Create security context for this file
                security_context = SecurityContext(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    security_level=SecurityLevel.RESTRICTED,
                    data_classification="genomic"
                )
                
                # Analyze the sequence
                result = self.analyze_sequence(sequence_file, security_context=security_context)
                
                batch_results["results"].append({
                    "file": sequence_file,
                    "status": "success",
                    "result": result
                })
                batch_results["files_processed"] += 1
                batch_results["security_summary"]["audit_events_logged"] += 1
                
            except Exception as e:
                batch_results["results"].append({
                    "file": sequence_file,
                    "status": "failed",
                    "error": str(e)
                })
                batch_results["files_failed"] += 1
                
                # Log batch processing error
                log_audit_event(
                    AuditEventType.ERROR_OCCURRED,
                    "genomic_data",
                    "batch_analysis_file_error",
                    "failure",
                    user_id,
                    workflow_id,
                    {"file": sequence_file, "error": str(e)}
                )
        
        # Log batch completion
        log_audit_event(
            AuditEventType.DATA_PROCESSING,
            "genomic_data",
            "batch_analysis_complete",
            "success",
            user_id,
            workflow_id,
            {
                "files_processed": batch_results["files_processed"],
                "files_failed": batch_results["files_failed"],
                "batch_id": batch_results["batch_id"]
            }
        )
        
        return batch_results
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get security status and configuration for this agent.
        
        Returns:
            Security status information
        """
        from ..utils.security_config import get_security_config
        
        config = get_security_config()
        
        return {
            "agent_name": self.agent_name,
            "security_features": {
                "input_validation": True,
                "output_sanitization": True,
                "encryption": True,
                "audit_logging": True,
                "compliance_checking": True
            },
            "data_classification": "genomic/restricted",
            "encryption_enabled": config.encryption.enforce_encryption,
            "audit_enabled": config.audit.enable_audit_logging,
            "compliance_frameworks": [f.value for f in config.compliance.frameworks],
            "security_level": SecurityLevel.RESTRICTED.value,
            "last_updated": datetime.utcnow().isoformat()
        }