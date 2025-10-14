"""
Security and compliance tests for the Biomerkin multi-agent system.

This module tests encryption, input validation, output sanitization,
audit logging, and vulnerability assessments.
"""

import json
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from pathlib import Path

from biomerkin.utils.security import (
    EncryptionManager, InputValidator, OutputSanitizer, AuditLogger,
    SecurityLevel, AuditEventType, AuditEvent, SecurityError,
    encrypt_sensitive_data, decrypt_sensitive_data, validate_input,
    sanitize_output, log_audit_event
)
from biomerkin.utils.security_config import (
    SecurityConfig, EncryptionConfig, AccessControlConfig, AuditConfig,
    DataClassificationConfig, ComplianceConfig, SecurityConfigManager,
    ComplianceFramework, EncryptionStandard, get_security_config,
    validate_compliance_requirements
)


class TestEncryptionManager:
    """Test encryption and decryption functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.encryption_manager = EncryptionManager()
    
    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption."""
        test_data = "sensitive genomic data"
        
        # Encrypt data
        encrypted = self.encryption_manager.encrypt_data(test_data)
        assert encrypted != test_data
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = self.encryption_manager.decrypt_data(encrypted, str)
        assert decrypted == test_data
    
    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        test_data = {
            "patient_id": "12345",
            "dna_sequence": "ATCGATCG",
            "mutations": ["A123T", "G456C"]
        }
        
        # Encrypt data
        encrypted = self.encryption_manager.encrypt_data(test_data)
        assert encrypted != json.dumps(test_data)
        
        # Decrypt data
        decrypted = self.encryption_manager.decrypt_data(encrypted, dict)
        assert decrypted == test_data
    
    def test_encrypt_decrypt_bytes(self):
        """Test bytes encryption and decryption."""
        test_data = b"binary genomic data"
        
        # Encrypt data
        encrypted = self.encryption_manager.encrypt_data(test_data)
        assert isinstance(encrypted, str)
        
        # Decrypt data
        decrypted = self.encryption_manager.decrypt_data(encrypted, bytes)
        assert decrypted == test_data
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = self.encryption_manager.generate_secure_token()
        token2 = self.encryption_manager.generate_secure_token()
        
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2
        assert isinstance(token1, str)
        assert isinstance(token2, str)
    
    def test_hash_data(self):
        """Test data hashing with salt."""
        test_data = "password123"
        
        # Hash data
        hash_value, salt = self.encryption_manager.hash_data(test_data)
        assert isinstance(hash_value, str)
        assert isinstance(salt, str)
        assert len(hash_value) > 0
        assert len(salt) > 0
        
        # Verify hash
        assert self.encryption_manager.verify_hash(test_data, hash_value, salt)
        assert not self.encryption_manager.verify_hash("wrong_password", hash_value, salt)
    
    def test_encryption_with_security_levels(self):
        """Test encryption with different security levels."""
        test_data = "confidential medical data"
        
        # Test different security levels
        for level in SecurityLevel:
            encrypted = self.encryption_manager.encrypt_data(test_data, level)
            decrypted = self.encryption_manager.decrypt_data(encrypted, str)
            assert decrypted == test_data
    
    @patch('boto3.client')
    def test_kms_encryption(self, mock_boto_client):
        """Test KMS encryption functionality."""
        # Mock KMS client
        mock_kms = Mock()
        mock_boto_client.return_value = mock_kms
        mock_kms.encrypt.return_value = {
            'CiphertextBlob': b'encrypted_data'
        }
        mock_kms.decrypt.return_value = {
            'Plaintext': b'test data'
        }
        
        # Create encryption manager with KMS
        encryption_manager = EncryptionManager(kms_key_id='test-key-id')
        
        # Test encryption
        test_data = "test data"
        encrypted = encryption_manager.encrypt_data(test_data, SecurityLevel.RESTRICTED)
        assert encrypted.startswith('kms:')
        
        # Test decryption
        decrypted = encryption_manager.decrypt_data(encrypted, str)
        assert decrypted == test_data


class TestInputValidator:
    """Test input validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    def test_validate_dna_sequence_valid(self):
        """Test validation of valid DNA sequences."""
        valid_sequences = [
            "ATCGATCGATCG",
            "atcgatcgatcg",
            "ATCG-ATCG-ATCG",
            "ATCG ATCG ATCG",
            "ATCGATCGNNNN",
            "ATCG\nATCG\nATCG"
        ]
        
        for sequence in valid_sequences:
            is_valid, errors = self.validator.validate_dna_sequence(sequence)
            assert is_valid, f"Sequence should be valid: {sequence}, errors: {errors}"
            assert len(errors) == 0
    
    def test_validate_dna_sequence_invalid(self):
        """Test validation of invalid DNA sequences."""
        invalid_sequences = [
            "",  # Empty
            "ATCGXYZ",  # Invalid characters
            "ATCG<script>alert('xss')</script>",  # XSS attempt
            "A" * 20_000_000,  # Too large
        ]
        
        for sequence in invalid_sequences:
            is_valid, errors = self.validator.validate_dna_sequence(sequence)
            assert not is_valid, f"Sequence should be invalid: {sequence[:50]}..."
            assert len(errors) > 0
    
    def test_validate_protein_sequence_valid(self):
        """Test validation of valid protein sequences."""
        valid_sequences = [
            "ACDEFGHIKLMNPQRSTVWY",
            "acdefghiklmnpqrstvwy",
            "ACDE-FGHI-KLMN",
            "ACDE FGHI KLMN"
        ]
        
        for sequence in valid_sequences:
            is_valid, errors = self.validator.validate_protein_sequence(sequence)
            assert is_valid, f"Sequence should be valid: {sequence}, errors: {errors}"
            assert len(errors) == 0
    
    def test_validate_protein_sequence_invalid(self):
        """Test validation of invalid protein sequences."""
        invalid_sequences = [
            "",  # Empty
            "ACDEXYZ",  # Invalid characters
            "ACDE<script>",  # XSS attempt
            "A" * 2_000_000,  # Too large
        ]
        
        for sequence in invalid_sequences:
            is_valid, errors = self.validator.validate_protein_sequence(sequence)
            assert not is_valid, f"Sequence should be invalid: {sequence[:50]}..."
            assert len(errors) > 0
    
    def test_validate_workflow_id(self):
        """Test workflow ID validation."""
        valid_ids = [
            "workflow-123",
            "WORKFLOW_456",
            "workflow123456789",
            "a1b2c3d4e5f6g7h8"
        ]
        
        invalid_ids = [
            "",  # Empty
            "workflow@123",  # Invalid characters
            "a" * 100,  # Too long
            "workflow<script>",  # XSS attempt
        ]
        
        for workflow_id in valid_ids:
            is_valid, errors = self.validator.validate_workflow_id(workflow_id)
            assert is_valid, f"ID should be valid: {workflow_id}, errors: {errors}"
        
        for workflow_id in invalid_ids:
            is_valid, errors = self.validator.validate_workflow_id(workflow_id)
            assert not is_valid, f"ID should be invalid: {workflow_id}"
    
    def test_validate_json_payload(self):
        """Test JSON payload validation."""
        valid_payloads = [
            '{"key": "value"}',
            {"key": "value", "number": 123},
            '{"nested": {"key": "value"}}'
        ]
        
        invalid_payloads = [
            '{"key": "value"',  # Invalid JSON
            {"__proto__": "dangerous"},  # Dangerous key
            '{"key": "<script>alert(\'xss\')</script>"}',  # XSS attempt
            "x" * 100_000_000,  # Too large
        ]
        
        for payload in valid_payloads:
            is_valid, errors = self.validator.validate_json_payload(payload)
            assert is_valid, f"Payload should be valid: {payload}, errors: {errors}"
        
        for payload in invalid_payloads:
            is_valid, errors = self.validator.validate_json_payload(payload)
            assert not is_valid, f"Payload should be invalid: {str(payload)[:50]}..."
    
    def test_sanitize_string(self):
        """Test string sanitization."""
        test_cases = [
            ("normal string", "normal string"),
            ("string with <script>alert('xss')</script>", "string with alert('xss')"),
            ("string with\x00null\x01bytes", "string withnullbytes"),
            ("SELECT * FROM users WHERE id=1", " *  users WHERE id=1"),
            ("string -- comment", "string  comment"),
        ]
        
        for input_str, expected in test_cases:
            sanitized = self.validator.sanitize_string(input_str)
            assert expected in sanitized or sanitized == expected, f"Input: {input_str}, Expected: {expected}, Got: {sanitized}"


class TestOutputSanitizer:
    """Test output sanitization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = OutputSanitizer()
    
    def test_sanitize_for_public(self):
        """Test sanitization for public consumption."""
        test_data = {
            "public_info": "This is public",
            "api_key": "secret-key-123",
            "password": "secret-password",
            "user_email": "user@example.com",
            "results": ["result1", "result2"]
        }
        
        sanitized = self.sanitizer.sanitize_output(test_data, SecurityLevel.PUBLIC)
        
        # Sensitive keys should be removed
        assert "api_key" not in sanitized
        assert "password" not in sanitized
        
        # Public info should remain
        assert sanitized["public_info"] == "This is public"
        assert sanitized["results"] == ["result1", "result2"]
        
        # Email should be redacted
        assert "[EMAIL_REDACTED]" in sanitized["user_email"]
    
    def test_sanitize_for_internal(self):
        """Test sanitization for internal use."""
        test_data = {
            "internal_info": "This is internal",
            "api_key": "secret-key-123",
            "user_email": "user@example.com"
        }
        
        sanitized = self.sanitizer.sanitize_output(test_data, SecurityLevel.INTERNAL)
        
        # Sensitive keys should be redacted but structure preserved
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["internal_info"] == "This is internal"
        assert "[EMAIL_REDACTED]" in sanitized["user_email"]
    
    def test_sanitize_nested_data(self):
        """Test sanitization of nested data structures."""
        test_data = {
            "level1": {
                "level2": {
                    "secret": "top-secret",
                    "public": "public info"
                },
                "api_key": "secret-key"
            },
            "list_data": [
                {"password": "secret"},
                {"public": "info"}
            ]
        }
        
        sanitized = self.sanitizer.sanitize_output(test_data, SecurityLevel.PUBLIC)
        
        # Check nested sanitization
        assert "secret" not in sanitized["level1"]["level2"]
        assert "api_key" not in sanitized["level1"]
        assert sanitized["level1"]["level2"]["public"] == "public info"
        
        # Check list sanitization
        assert "password" not in sanitized["list_data"][0]
        assert sanitized["list_data"][1]["public"] == "info"


class TestAuditLogger:
    """Test audit logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.audit_logger = AuditLogger(log_to_cloudwatch=False)
    
    def test_log_event(self):
        """Test basic event logging."""
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            session_id="test-session",
            resource="genomic-data",
            action="read",
            result="success",
            details={"file": "test.fasta"}
        )
        
        # Should not raise exception
        self.audit_logger.log_event(event)
    
    def test_log_data_access(self):
        """Test data access logging."""
        self.audit_logger.log_data_access(
            resource="patient-data",
            action="query",
            user_id="researcher-123",
            workflow_id="workflow-456",
            result="success",
            details={"query": "SELECT * FROM patients"}
        )
    
    def test_log_data_processing(self):
        """Test data processing logging."""
        self.audit_logger.log_data_processing(
            resource="dna-sequence",
            action="analyze",
            user_id="scientist-789",
            workflow_id="workflow-123",
            result="success",
            details={"sequence_length": 1000}
        )
    
    def test_log_error(self):
        """Test error logging."""
        test_error = ValueError("Test error message")
        
        self.audit_logger.log_error(
            resource="protein-analysis",
            action="predict_structure",
            error=test_error,
            user_id="user-123",
            workflow_id="workflow-789"
        )
    
    @patch('boto3.client')
    def test_cloudwatch_logging(self, mock_boto_client):
        """Test CloudWatch logging functionality."""
        # Mock CloudWatch client
        mock_cloudwatch = Mock()
        mock_boto_client.return_value = mock_cloudwatch
        
        # Create audit logger with CloudWatch enabled
        audit_logger = AuditLogger(log_to_cloudwatch=True)
        
        # Log an event
        event = AuditEvent(
            event_type=AuditEventType.DATA_ACCESS,
            timestamp=datetime.now(timezone.utc),
            user_id="test-user",
            session_id=None,
            resource="test-resource",
            action="test-action",
            result="success",
            details={}
        )
        
        audit_logger.log_event(event)
        
        # Verify CloudWatch was called
        mock_cloudwatch.put_log_events.assert_called_once()


class TestSecurityConfig:
    """Test security configuration functionality."""
    
    def test_default_config_creation(self):
        """Test creation of default security configuration."""
        config = SecurityConfig(
            encryption=EncryptionConfig(),
            access_control=AccessControlConfig(),
            audit=AuditConfig(),
            data_classification=DataClassificationConfig(),
            compliance=ComplianceConfig()
        )
        
        assert config.encryption.data_at_rest_standard == EncryptionStandard.AES256
        assert config.access_control.require_secure_transport is True
        assert config.audit.enable_audit_logging is True
        assert config.compliance.frameworks == [ComplianceFramework.HIPAA]
    
    def test_config_serialization(self):
        """Test configuration serialization and deserialization."""
        original_config = SecurityConfig(
            encryption=EncryptionConfig(use_kms=True, key_rotation_days=30),
            access_control=AccessControlConfig(require_mfa=True),
            audit=AuditConfig(retention_days=3650),
            data_classification=DataClassificationConfig(),
            compliance=ComplianceConfig(frameworks=[ComplianceFramework.HIPAA, ComplianceFramework.GDPR])
        )
        
        # Serialize to dict
        config_dict = original_config.to_dict()
        
        # Deserialize from dict
        restored_config = SecurityConfig.from_dict(config_dict)
        
        # Verify restoration
        assert restored_config.encryption.use_kms == original_config.encryption.use_kms
        assert restored_config.encryption.key_rotation_days == original_config.encryption.key_rotation_days
        assert restored_config.access_control.require_mfa == original_config.access_control.require_mfa
        assert restored_config.audit.retention_days == original_config.audit.retention_days
        assert restored_config.compliance.frameworks == original_config.compliance.frameworks
    
    def test_config_manager_load_save(self):
        """Test configuration manager load and save functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            # Create config manager
            config_manager = SecurityConfigManager(config_file)
            
            # Create and save config
            test_config = SecurityConfig(
                encryption=EncryptionConfig(use_kms=True),
                access_control=AccessControlConfig(require_mfa=True),
                audit=AuditConfig(enable_cloudtrail=True),
                data_classification=DataClassificationConfig(),
                compliance=ComplianceConfig()
            )
            
            config_manager.save_config(test_config)
            
            # Load config
            loaded_config = config_manager.load_config()
            
            # Verify loaded config
            assert loaded_config.encryption.use_kms is True
            assert loaded_config.access_control.require_mfa is True
            assert loaded_config.audit.enable_cloudtrail is True
            
        finally:
            # Clean up
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    def test_config_validation(self):
        """Test configuration validation."""
        config_manager = SecurityConfigManager()
        
        # Test production config validation
        prod_config = SecurityConfig(
            encryption=EncryptionConfig(enforce_encryption=False),  # Should trigger warning
            access_control=AccessControlConfig(require_secure_transport=False),  # Should trigger warning
            audit=AuditConfig(enable_audit_logging=False),  # Should trigger warning
            data_classification=DataClassificationConfig(),
            compliance=ComplianceConfig(),
            environment="production"
        )
        
        issues = config_manager.validate_config(prod_config)
        assert len(issues) > 0
        assert any("encryption" in issue.lower() for issue in issues)
        assert any("secure transport" in issue.lower() for issue in issues)
        assert any("audit" in issue.lower() for issue in issues)


class TestComplianceValidation:
    """Test compliance validation functionality."""
    
    def test_hipaa_requirements(self):
        """Test HIPAA compliance requirements."""
        requirements = validate_compliance_requirements('genomic', 'process')
        
        assert len(requirements) > 0
        assert any('encrypt' in req.lower() for req in requirements)
        assert any('log' in req.lower() for req in requirements)
        assert any('access control' in req.lower() for req in requirements)
    
    def test_gdpr_requirements(self):
        """Test GDPR compliance requirements."""
        # Mock GDPR framework in config
        with patch('biomerkin.utils.security_config.get_security_config') as mock_config:
            mock_security_config = Mock()
            mock_security_config.compliance.frameworks = [ComplianceFramework.GDPR]
            mock_config.return_value = mock_security_config
            
            requirements = validate_compliance_requirements('personal', 'process')
            
            assert len(requirements) > 0
            assert any('privacy by design' in req.lower() for req in requirements)
            assert any('data subject rights' in req.lower() for req in requirements)


class TestSecurityIntegration:
    """Test integration of security components."""
    
    def test_end_to_end_data_protection(self):
        """Test end-to-end data protection workflow."""
        # 1. Validate input
        dna_sequence = "ATCGATCGATCG"
        is_valid, errors = validate_input(dna_sequence, 'dna_sequence')
        assert is_valid
        assert len(errors) == 0
        
        # 2. Encrypt sensitive data
        encrypted_data = encrypt_sensitive_data(dna_sequence, SecurityLevel.CONFIDENTIAL)
        assert encrypted_data != dna_sequence
        
        # 3. Decrypt data
        decrypted_data = decrypt_sensitive_data(encrypted_data, str)
        assert decrypted_data == dna_sequence
        
        # 4. Sanitize output
        output_data = {
            "sequence": decrypted_data,
            "api_key": "secret-123",
            "results": ["gene1", "gene2"]
        }
        sanitized_output = sanitize_output(output_data, SecurityLevel.INTERNAL)
        assert sanitized_output["sequence"] == dna_sequence
        assert sanitized_output["api_key"] == "[REDACTED]"
        assert sanitized_output["results"] == ["gene1", "gene2"]
        
        # 5. Log audit event
        log_audit_event(
            AuditEventType.DATA_PROCESSING,
            "genomic-analysis",
            "sequence-analysis",
            "success",
            "user-123",
            "workflow-456",
            {"sequence_length": len(dna_sequence)}
        )
    
    def test_security_error_handling(self):
        """Test security error handling."""
        encryption_manager = EncryptionManager()
        
        # Test invalid decryption
        with pytest.raises(SecurityError):
            encryption_manager.decrypt_data("invalid-encrypted-data", str)
    
    def test_vulnerability_assessment(self):
        """Test basic vulnerability assessment."""
        validator = InputValidator()
        
        # Test XSS attempts
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "onload=alert('xss')",
        ]
        
        for attempt in xss_attempts:
            is_valid, errors = validator.validate_dna_sequence(attempt)
            assert not is_valid, f"XSS attempt should be rejected: {attempt}"
        
        # Test SQL injection attempts
        sql_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker'); --",
        ]
        
        for attempt in sql_attempts:
            sanitized = validator.sanitize_string(attempt)
            assert "DROP" not in sanitized.upper()
            assert "UNION" not in sanitized.upper()
            assert "INSERT" not in sanitized.upper()
    
    def test_data_classification_enforcement(self):
        """Test data classification enforcement."""
        sanitizer = OutputSanitizer()
        
        # Test different classification levels
        sensitive_data = {
            "patient_id": "12345",
            "ssn": "123-45-6789",
            "email": "patient@example.com",
            "dna_sequence": "ATCGATCG",
            "diagnosis": "genetic disorder"
        }
        
        # Public sanitization should remove most sensitive data
        public_output = sanitizer.sanitize_output(sensitive_data, SecurityLevel.PUBLIC)
        assert "[SSN_REDACTED]" in public_output["ssn"]
        assert "[EMAIL_REDACTED]" in public_output["email"]
        
        # Internal sanitization should preserve more data
        internal_output = sanitizer.sanitize_output(sensitive_data, SecurityLevel.INTERNAL)
        assert "[SSN_REDACTED]" in internal_output["ssn"]
        assert "[EMAIL_REDACTED]" in internal_output["email"]
        assert internal_output["dna_sequence"] == "ATCGATCG"
        
        # Confidential sanitization should preserve most data
        confidential_output = sanitizer.sanitize_output(sensitive_data, SecurityLevel.CONFIDENTIAL)
        assert "[SSN_REDACTED]" in confidential_output["ssn"]  # Still redact SSN
        assert confidential_output["dna_sequence"] == "ATCGATCG"
        assert confidential_output["diagnosis"] == "genetic disorder"


if __name__ == "__main__":
    pytest.main([__file__])