"""
Security and compliance utilities for the Biomerkin multi-agent system.

This module provides encryption, input validation, output sanitization,
and audit logging capabilities to ensure data security and compliance.
"""

import base64
import hashlib
import hmac
import json
import logging
import re
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

import boto3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from botocore.exceptions import ClientError

from .logging_config import get_logger


class SecurityLevel(Enum):
    """Security levels for different types of data."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AuditEventType(Enum):
    """Types of audit events."""
    DATA_ACCESS = "data_access"
    DATA_PROCESSING = "data_processing"
    DATA_EXPORT = "data_export"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SYSTEM_ACCESS = "system_access"
    ERROR_OCCURRED = "error_occurred"
    CONFIGURATION_CHANGE = "configuration_change"


@dataclass
class AuditEvent:
    """Audit event information."""
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    resource: str
    action: str
    result: str  # success, failure, partial
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    workflow_id: Optional[str] = None
    security_level: SecurityLevel = SecurityLevel.INTERNAL


class EncryptionManager:
    """Manages encryption and decryption operations."""
    
    def __init__(self, kms_key_id: Optional[str] = None):
        """
        Initialize encryption manager.
        
        Args:
            kms_key_id: AWS KMS key ID for envelope encryption
        """
        self.logger = get_logger(__name__)
        self.kms_key_id = kms_key_id
        self.kms_client = boto3.client('kms') if kms_key_id else None
        
        # Generate or load application encryption key
        self._app_key = self._get_or_create_app_key()
        self._fernet = Fernet(self._app_key)
    
    def _get_or_create_app_key(self) -> bytes:
        """Get or create application encryption key."""
        key_file = Path('.biomerkin_key')
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                self.logger.warning(f"Could not read existing key file: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            key_file.chmod(0o600)
        except Exception as e:
            self.logger.warning(f"Could not save key file: {e}")
        
        return key
    
    def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]], 
                    security_level: SecurityLevel = SecurityLevel.CONFIDENTIAL) -> str:
        """
        Encrypt data with appropriate security level.
        
        Args:
            data: Data to encrypt
            security_level: Security level for the data
            
        Returns:
            Base64-encoded encrypted data
        """
        try:
            # Convert data to bytes if necessary
            if isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data
            
            # Use KMS for restricted data if available
            if security_level == SecurityLevel.RESTRICTED and self.kms_client:
                return self._encrypt_with_kms(data_bytes)
            else:
                # Use application-level encryption
                encrypted_data = self._fernet.encrypt(data_bytes)
                return base64.b64encode(encrypted_data).decode('utf-8')
                
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise SecurityError(f"Failed to encrypt data: {e}")
    
    def decrypt_data(self, encrypted_data: str, 
                    expected_type: type = str) -> Union[str, bytes, Dict[str, Any]]:
        """
        Decrypt data and return in expected format.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            expected_type: Expected type of decrypted data
            
        Returns:
            Decrypted data in expected format
        """
        try:
            # Check if this is KMS-encrypted data
            if encrypted_data.startswith('kms:'):
                decrypted_bytes = self._decrypt_with_kms(encrypted_data)
            else:
                # Application-level decryption
                encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
                decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Convert to expected type
            if expected_type == bytes:
                return decrypted_bytes
            elif expected_type == dict:
                return json.loads(decrypted_bytes.decode('utf-8'))
            else:
                return decrypted_bytes.decode('utf-8')
                
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise SecurityError(f"Failed to decrypt data: {e}")
    
    def _encrypt_with_kms(self, data: bytes) -> str:
        """Encrypt data using AWS KMS."""
        try:
            response = self.kms_client.encrypt(
                KeyId=self.kms_key_id,
                Plaintext=data
            )
            encrypted_blob = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
            return f"kms:{encrypted_blob}"
        except ClientError as e:
            self.logger.error(f"KMS encryption failed: {e}")
            raise SecurityError(f"KMS encryption failed: {e}")
    
    def _decrypt_with_kms(self, encrypted_data: str) -> bytes:
        """Decrypt data using AWS KMS."""
        try:
            # Remove 'kms:' prefix
            encrypted_blob = base64.b64decode(encrypted_data[4:])
            
            response = self.kms_client.decrypt(CiphertextBlob=encrypted_blob)
            return response['Plaintext']
        except ClientError as e:
            self.logger.error(f"KMS decryption failed: {e}")
            raise SecurityError(f"KMS decryption failed: {e}")
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: Union[str, bytes], salt: Optional[bytes] = None) -> Tuple[str, str]:
        """
        Hash data with salt for secure storage.
        
        Args:
            data: Data to hash
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (hash, salt) as base64-encoded strings
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        hash_value = kdf.derive(data)
        
        return (
            base64.b64encode(hash_value).decode('utf-8'),
            base64.b64encode(salt).decode('utf-8')
        )
    
    def verify_hash(self, data: Union[str, bytes], hash_value: str, salt: str) -> bool:
        """Verify data against stored hash."""
        try:
            computed_hash, _ = self.hash_data(data, base64.b64decode(salt))
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            self.logger.error(f"Hash verification failed: {e}")
            return False


class InputValidator:
    """Validates and sanitizes input data."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Define validation patterns
        self.patterns = {
            'dna_sequence': re.compile(r'^[ATCGN\s\n\r-]*$', re.IGNORECASE),
            'protein_sequence': re.compile(r'^[ACDEFGHIKLMNPQRSTVWY\s\n\r-]*$', re.IGNORECASE),
            'gene_id': re.compile(r'^[A-Za-z0-9_-]+$'),
            'workflow_id': re.compile(r'^[A-Za-z0-9_-]{8,64}$'),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'safe_string': re.compile(r'^[A-Za-z0-9\s._-]*$'),
        }
        
        # Define size limits
        self.size_limits = {
            'dna_sequence': 10_000_000,  # 10MB
            'protein_sequence': 1_000_000,  # 1MB
            'gene_id': 100,
            'workflow_id': 64,
            'email': 254,
            'safe_string': 1000,
            'json_payload': 50_000_000,  # 50MB
        }
    
    def validate_dna_sequence(self, sequence: str) -> Tuple[bool, List[str]]:
        """
        Validate DNA sequence format and content.
        
        Args:
            sequence: DNA sequence to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not sequence:
            errors.append("DNA sequence cannot be empty")
            return False, errors
        
        # Check size limit
        if len(sequence) > self.size_limits['dna_sequence']:
            errors.append(f"DNA sequence too large (max {self.size_limits['dna_sequence']} characters)")
        
        # Check format
        if not self.patterns['dna_sequence'].match(sequence):
            errors.append("DNA sequence contains invalid characters (only A, T, C, G, N allowed)")
        
        # Check for suspicious patterns
        if self._contains_suspicious_patterns(sequence):
            errors.append("DNA sequence contains suspicious patterns")
        
        return len(errors) == 0, errors
    
    def validate_protein_sequence(self, sequence: str) -> Tuple[bool, List[str]]:
        """
        Validate protein sequence format and content.
        
        Args:
            sequence: Protein sequence to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not sequence:
            errors.append("Protein sequence cannot be empty")
            return False, errors
        
        # Check size limit
        if len(sequence) > self.size_limits['protein_sequence']:
            errors.append(f"Protein sequence too large (max {self.size_limits['protein_sequence']} characters)")
        
        # Check format
        if not self.patterns['protein_sequence'].match(sequence):
            errors.append("Protein sequence contains invalid characters")
        
        return len(errors) == 0, errors
    
    def validate_workflow_id(self, workflow_id: str) -> Tuple[bool, List[str]]:
        """Validate workflow ID format."""
        errors = []
        
        if not workflow_id:
            errors.append("Workflow ID cannot be empty")
            return False, errors
        
        if not self.patterns['workflow_id'].match(workflow_id):
            errors.append("Workflow ID contains invalid characters")
        
        if len(workflow_id) > self.size_limits['workflow_id']:
            errors.append(f"Workflow ID too long (max {self.size_limits['workflow_id']} characters)")
        
        return len(errors) == 0, errors
    
    def validate_json_payload(self, payload: Union[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate JSON payload for size and structure.
        
        Args:
            payload: JSON payload to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            if isinstance(payload, str):
                # Check size before parsing
                if len(payload) > self.size_limits['json_payload']:
                    errors.append(f"JSON payload too large (max {self.size_limits['json_payload']} bytes)")
                    return False, errors
                
                # Parse JSON
                parsed_payload = json.loads(payload)
            else:
                parsed_payload = payload
            
            # Check for dangerous keys or values
            if self._contains_dangerous_json_content(parsed_payload):
                errors.append("JSON payload contains potentially dangerous content")
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"JSON validation error: {e}")
        
        return len(errors) == 0, errors
    
    def sanitize_string(self, input_string: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input by removing dangerous characters.
        
        Args:
            input_string: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_string:
            return ""
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_string)
        
        # Remove potentially dangerous HTML/XML tags
        sanitized = re.sub(r'<[^>]*>', '', sanitized)
        
        # Remove SQL injection patterns
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(--|/\*|\*/)',
            r'(\bOR\b.*=.*\bOR\b)',
            r'(\bAND\b.*=.*\bAND\b)',
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Truncate if necessary
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    def _contains_suspicious_patterns(self, sequence: str) -> bool:
        """Check for suspicious patterns in biological sequences."""
        # Check for extremely repetitive patterns
        if len(set(sequence.replace(' ', '').replace('\n', '').replace('\r', ''))) < 2:
            return True
        
        # Check for non-biological patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, sequence, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_dangerous_json_content(self, data: Any, depth: int = 0) -> bool:
        """Recursively check JSON data for dangerous content."""
        if depth > 10:  # Prevent deep recursion
            return True
        
        if isinstance(data, dict):
            # Check for dangerous keys
            dangerous_keys = ['__proto__', 'constructor', 'prototype', 'eval', 'function']
            if any(key in dangerous_keys for key in data.keys()):
                return True
            
            # Recursively check values
            return any(self._contains_dangerous_json_content(value, depth + 1) for value in data.values())
        
        elif isinstance(data, list):
            # Check list length
            if len(data) > 10000:  # Prevent large arrays
                return True
            
            # Recursively check items
            return any(self._contains_dangerous_json_content(item, depth + 1) for item in data)
        
        elif isinstance(data, str):
            # Check for dangerous string patterns
            dangerous_patterns = [
                r'<script',
                r'javascript:',
                r'data:',
                r'eval\s*\(',
                r'Function\s*\(',
                r'setTimeout\s*\(',
                r'setInterval\s*\(',
            ]
            
            return any(re.search(pattern, data, re.IGNORECASE) for pattern in dangerous_patterns)
        
        return False


class OutputSanitizer:
    """Sanitizes output data to prevent information leakage."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Define sensitive patterns to redact
        self.sensitive_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]'),
            (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_REDACTED]'),
            (r'(?i)(password|pwd|secret|key|token)[\s]*[:=][\s]*[^\s\n\r]+', r'\1: [REDACTED]'),
        ]
    
    def sanitize_output(self, data: Any, security_level: SecurityLevel = SecurityLevel.INTERNAL) -> Any:
        """
        Sanitize output data based on security level.
        
        Args:
            data: Data to sanitize
            security_level: Security level for output
            
        Returns:
            Sanitized data
        """
        if security_level == SecurityLevel.PUBLIC:
            return self._sanitize_for_public(data)
        elif security_level == SecurityLevel.INTERNAL:
            return self._sanitize_for_internal(data)
        elif security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
            return self._sanitize_for_confidential(data)
        
        return data
    
    def _sanitize_for_public(self, data: Any) -> Any:
        """Sanitize data for public consumption."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Remove sensitive keys
                if key.lower() in ['api_key', 'secret', 'password', 'token', 'credentials']:
                    continue
                sanitized[key] = self._sanitize_for_public(value)
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize_for_public(item) for item in data]
        
        elif isinstance(data, str):
            return self._redact_sensitive_info(data)
        
        return data
    
    def _sanitize_for_internal(self, data: Any) -> Any:
        """Sanitize data for internal use."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Redact API keys and secrets but keep structure
                if key.lower() in ['api_key', 'secret', 'password', 'token']:
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._sanitize_for_internal(value)
            return sanitized
        
        elif isinstance(data, list):
            return [self._sanitize_for_internal(item) for item in data]
        
        elif isinstance(data, str):
            return self._redact_sensitive_info(data)
        
        return data
    
    def _sanitize_for_confidential(self, data: Any) -> Any:
        """Minimal sanitization for confidential data."""
        if isinstance(data, dict):
            return {key: self._sanitize_for_confidential(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_for_confidential(item) for item in data]
        elif isinstance(data, str):
            # Only redact the most sensitive patterns
            for pattern, replacement in self.sensitive_patterns[:2]:  # Only email and SSN
                data = re.sub(pattern, replacement, data)
        
        return data
    
    def _redact_sensitive_info(self, text: str) -> str:
        """Redact sensitive information from text."""
        for pattern, replacement in self.sensitive_patterns:
            text = re.sub(pattern, replacement, text)
        return text


class AuditLogger:
    """Handles audit logging for compliance and security monitoring."""
    
    def __init__(self, log_to_cloudwatch: bool = True):
        """
        Initialize audit logger.
        
        Args:
            log_to_cloudwatch: Whether to send logs to CloudWatch
        """
        self.logger = get_logger('biomerkin.audit')
        self.log_to_cloudwatch = log_to_cloudwatch
        
        if log_to_cloudwatch:
            try:
                self.cloudwatch_client = boto3.client('logs')
                self.log_group_name = '/biomerkin/audit'
                self.log_stream_name = f"audit-{datetime.now().strftime('%Y-%m-%d')}"
                self._ensure_log_stream_exists()
            except Exception as e:
                self.logger.warning(f"Could not initialize CloudWatch logging: {e}")
                self.log_to_cloudwatch = False
    
    def _ensure_log_stream_exists(self):
        """Ensure CloudWatch log stream exists."""
        try:
            # Create log group if it doesn't exist
            try:
                self.cloudwatch_client.create_log_group(logGroupName=self.log_group_name)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
            
            # Create log stream if it doesn't exist
            try:
                self.cloudwatch_client.create_log_stream(
                    logGroupName=self.log_group_name,
                    logStreamName=self.log_stream_name
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise
                    
        except Exception as e:
            self.logger.warning(f"Could not create CloudWatch log stream: {e}")
    
    def log_event(self, event: AuditEvent):
        """
        Log an audit event.
        
        Args:
            event: Audit event to log
        """
        # Create log entry
        log_entry = {
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type.value,
            'user_id': event.user_id,
            'session_id': event.session_id,
            'resource': event.resource,
            'action': event.action,
            'result': event.result,
            'details': event.details,
            'ip_address': event.ip_address,
            'user_agent': event.user_agent,
            'workflow_id': event.workflow_id,
            'security_level': event.security_level.value
        }
        
        # Log locally
        self.logger.info(f"AUDIT: {json.dumps(log_entry)}")
        
        # Log to CloudWatch if enabled
        if self.log_to_cloudwatch:
            try:
                self._send_to_cloudwatch(log_entry)
            except Exception as e:
                self.logger.error(f"Failed to send audit log to CloudWatch: {e}")
    
    def _send_to_cloudwatch(self, log_entry: Dict[str, Any]):
        """Send log entry to CloudWatch."""
        try:
            self.cloudwatch_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(time.time() * 1000),
                        'message': json.dumps(log_entry)
                    }
                ]
            )
        except Exception as e:
            self.logger.error(f"CloudWatch logging failed: {e}")
    
    def log_data_access(self, resource: str, action: str, user_id: Optional[str] = None,
                       workflow_id: Optional[str] = None, result: str = "success",
                       details: Optional[Dict[str, Any]] = None):
        """Log data access event."""
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            workflow_id=workflow_id
        )
        self.log_event(event)
    
    def log_data_processing(self, resource: str, action: str, user_id: Optional[str] = None,
                          workflow_id: Optional[str] = None, result: str = "success",
                          details: Optional[Dict[str, Any]] = None):
        """Log data processing event."""
        event = AuditEvent(
            event_type=AuditEventType.DATA_PROCESSING,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            resource=resource,
            action=action,
            result=result,
            details=details or {},
            workflow_id=workflow_id
        )
        self.log_event(event)
    
    def log_error(self, resource: str, action: str, error: Exception,
                 user_id: Optional[str] = None, workflow_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """Log error event."""
        error_details = details or {}
        error_details.update({
            'error_type': type(error).__name__,
            'error_message': str(error)
        })
        
        event = AuditEvent(
            event_type=AuditEventType.ERROR_OCCURRED,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=None,
            resource=resource,
            action=action,
            result="failure",
            details=error_details,
            workflow_id=workflow_id
        )
        self.log_event(event)


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


# Convenience functions for common security operations

def encrypt_sensitive_data(data: Any, security_level: SecurityLevel = SecurityLevel.CONFIDENTIAL) -> str:
    """Encrypt sensitive data with appropriate security level."""
    encryption_manager = EncryptionManager()
    return encryption_manager.encrypt_data(data, security_level)


def decrypt_sensitive_data(encrypted_data: str, expected_type: type = str) -> Any:
    """Decrypt sensitive data."""
    encryption_manager = EncryptionManager()
    return encryption_manager.decrypt_data(encrypted_data, expected_type)


def validate_input(data: Any, data_type: str) -> Tuple[bool, List[str]]:
    """Validate input data based on type."""
    validator = InputValidator()
    
    if data_type == 'dna_sequence':
        return validator.validate_dna_sequence(data)
    elif data_type == 'protein_sequence':
        return validator.validate_protein_sequence(data)
    elif data_type == 'workflow_id':
        return validator.validate_workflow_id(data)
    elif data_type == 'json_payload':
        return validator.validate_json_payload(data)
    else:
        return True, []


def sanitize_output(data: Any, security_level: SecurityLevel = SecurityLevel.INTERNAL) -> Any:
    """Sanitize output data for safe consumption."""
    sanitizer = OutputSanitizer()
    return sanitizer.sanitize_output(data, security_level)


def log_audit_event(event_type: AuditEventType, resource: str, action: str,
                   result: str = "success", user_id: Optional[str] = None,
                   workflow_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """Log an audit event."""
    audit_logger = AuditLogger()
    
    event = AuditEvent(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        session_id=None,
        resource=resource,
        action=action,
        result=result,
        details=details or {},
        workflow_id=workflow_id
    )
    
    audit_logger.log_event(event)