"""
Security middleware for the Biomerkin multi-agent system.

This module provides decorators and middleware functions to integrate
security features into existing agents and services.
"""

import functools
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass

from .security import (
    EncryptionManager, InputValidator, OutputSanitizer, AuditLogger,
    SecurityLevel, AuditEventType, AuditEvent, SecurityError
)
from .security_config import get_security_config, validate_compliance_requirements
from .logging_config import get_logger


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    data_classification: str = "confidential"


class SecurityMiddleware:
    """Security middleware for agent operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.encryption_manager = EncryptionManager()
        self.input_validator = InputValidator()
        self.output_sanitizer = OutputSanitizer()
        self.audit_logger = AuditLogger()
        self.security_config = get_security_config()
    
    def secure_operation(self, 
                        operation_name: str,
                        resource_type: str,
                        data_classification: str = "confidential",
                        require_encryption: bool = True,
                        validate_input: bool = True,
                        sanitize_output: bool = True,
                        audit_log: bool = True):
        """
        Decorator to secure agent operations.
        
        Args:
            operation_name: Name of the operation
            resource_type: Type of resource being accessed
            data_classification: Classification level of the data
            require_encryption: Whether to encrypt sensitive data
            validate_input: Whether to validate input data
            sanitize_output: Whether to sanitize output data
            audit_log: Whether to log the operation
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract security context
                security_context = kwargs.pop('security_context', SecurityContext())
                
                start_time = time.time()
                operation_result = "success"
                error_details = None
                
                try:
                    # Pre-operation security checks
                    self._pre_operation_checks(
                        operation_name, resource_type, data_classification,
                        args, kwargs, security_context
                    )
                    
                    # Validate inputs if required
                    if validate_input:
                        self._validate_inputs(args, kwargs, resource_type)
                    
                    # Execute the operation
                    result = func(*args, **kwargs)
                    
                    # Post-operation security processing
                    if sanitize_output:
                        result = self._sanitize_output(result, security_context.security_level)
                    
                    if require_encryption and self._should_encrypt_result(result, data_classification):
                        result = self._encrypt_result(result, data_classification)
                    
                    return result
                    
                except Exception as e:
                    operation_result = "failure"
                    error_details = {
                        'error_type': type(e).__name__,
                        'error_message': str(e)
                    }
                    raise
                    
                finally:
                    # Audit logging
                    if audit_log:
                        self._log_operation(
                            operation_name, resource_type, security_context,
                            operation_result, time.time() - start_time, error_details
                        )
            
            return wrapper
        return decorator
    
    def _pre_operation_checks(self, operation_name: str, resource_type: str,
                            data_classification: str, args: tuple, kwargs: dict,
                            security_context: SecurityContext):
        """Perform pre-operation security checks."""
        
        # Check compliance requirements
        compliance_requirements = validate_compliance_requirements(
            data_classification, operation_name
        )
        
        if compliance_requirements:
            self.logger.info(f"Operation {operation_name} must meet compliance requirements: {compliance_requirements}")
        
        # Check data residency requirements
        if self.security_config.compliance.data_residency_regions:
            # This would typically check the current AWS region
            self.logger.debug(f"Data residency check for operation {operation_name}")
        
        # Check access control requirements
        if self.security_config.access_control.require_secure_transport:
            # This would typically check if the request came over HTTPS
            self.logger.debug(f"Secure transport check for operation {operation_name}")
    
    def _validate_inputs(self, args: tuple, kwargs: dict, resource_type: str):
        """Validate input data based on resource type."""
        
        # Look for common input patterns
        for arg in args:
            if isinstance(arg, str):
                if resource_type == 'genomic' and len(arg) > 100:
                    # Likely a DNA sequence
                    is_valid, errors = self.input_validator.validate_dna_sequence(arg)
                    if not is_valid:
                        raise SecurityError(f"Invalid DNA sequence: {errors}")
                
                elif resource_type == 'protein' and len(arg) > 50:
                    # Likely a protein sequence
                    is_valid, errors = self.input_validator.validate_protein_sequence(arg)
                    if not is_valid:
                        raise SecurityError(f"Invalid protein sequence: {errors}")
        
        # Validate specific kwargs
        if 'workflow_id' in kwargs:
            is_valid, errors = self.input_validator.validate_workflow_id(kwargs['workflow_id'])
            if not is_valid:
                raise SecurityError(f"Invalid workflow ID: {errors}")
        
        # Validate JSON payloads
        for key, value in kwargs.items():
            if isinstance(value, (dict, list)) or (isinstance(value, str) and value.startswith('{')):
                is_valid, errors = self.input_validator.validate_json_payload(value)
                if not is_valid:
                    raise SecurityError(f"Invalid JSON payload in {key}: {errors}")
    
    def _sanitize_output(self, result: Any, security_level: SecurityLevel) -> Any:
        """Sanitize output data based on security level."""
        return self.output_sanitizer.sanitize_output(result, security_level)
    
    def _should_encrypt_result(self, result: Any, data_classification: str) -> bool:
        """Determine if result should be encrypted based on classification."""
        if not self.security_config.encryption.enforce_encryption:
            return False
        
        # Encrypt restricted and confidential data
        if data_classification in ['restricted', 'confidential']:
            return True
        
        # Check if result contains sensitive patterns
        if isinstance(result, (dict, list)):
            result_str = str(result).lower()
            sensitive_patterns = ['patient', 'genomic', 'medical', 'dna', 'protein', 'mutation']
            return any(pattern in result_str for pattern in sensitive_patterns)
        
        return False
    
    def _encrypt_result(self, result: Any, data_classification: str) -> Dict[str, Any]:
        """Encrypt result data."""
        security_level = SecurityLevel.RESTRICTED if data_classification == 'restricted' else SecurityLevel.CONFIDENTIAL
        
        encrypted_data = self.encryption_manager.encrypt_data(result, security_level)
        
        return {
            'encrypted': True,
            'data': encrypted_data,
            'classification': data_classification,
            'encryption_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _log_operation(self, operation_name: str, resource_type: str,
                      security_context: SecurityContext, result: str,
                      duration: float, error_details: Optional[Dict[str, Any]]):
        """Log operation for audit purposes."""
        
        details = {
            'operation': operation_name,
            'resource_type': resource_type,
            'duration_seconds': round(duration, 3),
            'data_classification': security_context.data_classification
        }
        
        if error_details:
            details.update(error_details)
        
        event_type = AuditEventType.ERROR_OCCURRED if result == "failure" else AuditEventType.DATA_PROCESSING
        
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=security_context.user_id,
            session_id=security_context.session_id,
            resource=resource_type,
            action=operation_name,
            result=result,
            details=details,
            ip_address=security_context.ip_address,
            user_agent=security_context.user_agent,
            workflow_id=security_context.workflow_id,
            security_level=security_context.security_level
        )
        
        self.audit_logger.log_event(event)


# Global security middleware instance
security_middleware = SecurityMiddleware()


def secure_genomic_operation(operation_name: str, **kwargs):
    """Decorator for securing genomic data operations."""
    return security_middleware.secure_operation(
        operation_name=operation_name,
        resource_type="genomic",
        data_classification="restricted",
        **kwargs
    )


def secure_protein_operation(operation_name: str, **kwargs):
    """Decorator for securing protein data operations."""
    return security_middleware.secure_operation(
        operation_name=operation_name,
        resource_type="protein",
        data_classification="confidential",
        **kwargs
    )


def secure_literature_operation(operation_name: str, **kwargs):
    """Decorator for securing literature operations."""
    return security_middleware.secure_operation(
        operation_name=operation_name,
        resource_type="literature",
        data_classification="internal",
        require_encryption=False,
        **kwargs
    )


def secure_drug_operation(operation_name: str, **kwargs):
    """Decorator for securing drug discovery operations."""
    return security_middleware.secure_operation(
        operation_name=operation_name,
        resource_type="drug",
        data_classification="confidential",
        **kwargs
    )


def secure_medical_operation(operation_name: str, **kwargs):
    """Decorator for securing medical report operations."""
    return security_middleware.secure_operation(
        operation_name=operation_name,
        resource_type="medical",
        data_classification="restricted",
        **kwargs
    )


def with_security_context(user_id: Optional[str] = None,
                         session_id: Optional[str] = None,
                         workflow_id: Optional[str] = None,
                         security_level: SecurityLevel = SecurityLevel.INTERNAL,
                         data_classification: str = "confidential"):
    """
    Decorator to inject security context into function calls.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        workflow_id: Workflow identifier
        security_level: Security level for the operation
        data_classification: Data classification level
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            security_context = SecurityContext(
                user_id=user_id,
                session_id=session_id,
                workflow_id=workflow_id,
                security_level=security_level,
                data_classification=data_classification
            )
            kwargs['security_context'] = security_context
            return func(*args, **kwargs)
        return wrapper
    return decorator


def encrypt_sensitive_fields(*field_names: str):
    """
    Decorator to automatically encrypt sensitive fields in function results.
    
    Args:
        field_names: Names of fields to encrypt in the result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if isinstance(result, dict):
                encryption_manager = EncryptionManager()
                
                for field_name in field_names:
                    if field_name in result and result[field_name] is not None:
                        # Encrypt the field
                        encrypted_value = encryption_manager.encrypt_data(
                            result[field_name], SecurityLevel.CONFIDENTIAL
                        )
                        result[f"{field_name}_encrypted"] = encrypted_value
                        
                        # Optionally remove the original field
                        if get_security_config().encryption.enforce_encryption:
                            del result[field_name]
            
            return result
        return wrapper
    return decorator


def validate_genomic_input(func: Callable) -> Callable:
    """Decorator to validate genomic input data."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        validator = InputValidator()
        
        # Look for DNA sequences in arguments
        for i, arg in enumerate(args):
            if isinstance(arg, str) and len(arg) > 100:
                # Assume this might be a DNA sequence
                is_valid, errors = validator.validate_dna_sequence(arg)
                if not is_valid:
                    raise SecurityError(f"Invalid DNA sequence in argument {i}: {errors}")
        
        # Look for DNA sequences in keyword arguments
        for key, value in kwargs.items():
            if isinstance(value, str) and ('dna' in key.lower() or 'sequence' in key.lower()):
                is_valid, errors = validator.validate_dna_sequence(value)
                if not is_valid:
                    raise SecurityError(f"Invalid DNA sequence in {key}: {errors}")
        
        return func(*args, **kwargs)
    return wrapper


def sanitize_medical_output(security_level: SecurityLevel = SecurityLevel.INTERNAL):
    """Decorator to sanitize medical output data."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            sanitizer = OutputSanitizer()
            sanitized_result = sanitizer.sanitize_output(result, security_level)
            
            return sanitized_result
        return wrapper
    return decorator


def audit_data_access(resource_type: str, action: str):
    """Decorator to audit data access operations."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            audit_logger = AuditLogger()
            start_time = time.time()
            
            # Extract security context if available
            security_context = kwargs.get('security_context', SecurityContext())
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful access
                audit_logger.log_data_access(
                    resource=resource_type,
                    action=action,
                    user_id=security_context.user_id,
                    workflow_id=security_context.workflow_id,
                    result="success",
                    details={
                        'duration_seconds': round(time.time() - start_time, 3),
                        'function': func.__name__
                    }
                )
                
                return result
                
            except Exception as e:
                # Log failed access
                audit_logger.log_data_access(
                    resource=resource_type,
                    action=action,
                    user_id=security_context.user_id,
                    workflow_id=security_context.workflow_id,
                    result="failure",
                    details={
                        'duration_seconds': round(time.time() - start_time, 3),
                        'function': func.__name__,
                        'error': str(e)
                    }
                )
                raise
        return wrapper
    return decorator


def require_compliance(frameworks: List[str]):
    """
    Decorator to enforce compliance requirements.
    
    Args:
        frameworks: List of compliance frameworks to enforce
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            security_config = get_security_config()
            
            # Check if required frameworks are enabled
            enabled_frameworks = [f.value for f in security_config.compliance.frameworks]
            
            for framework in frameworks:
                if framework.lower() not in enabled_frameworks:
                    raise SecurityError(f"Compliance framework {framework} is required but not enabled")
            
            # Additional compliance checks could be added here
            
            return func(*args, **kwargs)
        return wrapper
    return decorator