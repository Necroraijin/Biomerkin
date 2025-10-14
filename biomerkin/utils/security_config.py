"""
Security configuration and compliance settings for the Biomerkin system.

This module provides centralized security configuration management,
compliance validation, and security policy enforcement.
"""

import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from enum import Enum
import json
from pathlib import Path

from .logging_config import get_logger


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    HIPAA = "hipaa"
    GDPR = "gdpr"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    NIST = "nist"


class EncryptionStandard(Enum):
    """Supported encryption standards."""
    AES256 = "aes256"
    AES256_GCM = "aes256_gcm"
    RSA2048 = "rsa2048"
    RSA4096 = "rsa4096"


@dataclass
class EncryptionConfig:
    """Configuration for encryption settings."""
    data_at_rest_standard: EncryptionStandard = EncryptionStandard.AES256
    data_in_transit_standard: EncryptionStandard = EncryptionStandard.AES256_GCM
    key_rotation_days: int = 90
    use_kms: bool = True
    kms_key_id: Optional[str] = None
    enforce_encryption: bool = True


@dataclass
class AccessControlConfig:
    """Configuration for access control settings."""
    require_mfa: bool = False  # For human users
    session_timeout_minutes: int = 60
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30
    require_secure_transport: bool = True
    allowed_ip_ranges: List[str] = None
    
    def __post_init__(self):
        if self.allowed_ip_ranges is None:
            self.allowed_ip_ranges = []


@dataclass
class AuditConfig:
    """Configuration for audit logging settings."""
    enable_audit_logging: bool = True
    log_data_access: bool = True
    log_data_processing: bool = True
    log_authentication: bool = True
    log_errors: bool = True
    retention_days: int = 2555  # 7 years for compliance
    enable_cloudwatch: bool = True
    enable_cloudtrail: bool = True
    log_level: str = "INFO"


@dataclass
class DataClassificationConfig:
    """Configuration for data classification and handling."""
    default_classification: str = "confidential"
    genomic_data_classification: str = "restricted"
    medical_data_classification: str = "restricted"
    research_data_classification: str = "confidential"
    system_data_classification: str = "internal"
    public_data_classification: str = "public"


@dataclass
class ComplianceConfig:
    """Configuration for compliance requirements."""
    frameworks: List[ComplianceFramework] = None
    data_residency_regions: List[str] = None
    data_retention_days: int = 2555  # 7 years default
    require_consent_tracking: bool = True
    enable_right_to_erasure: bool = True
    enable_data_portability: bool = True
    
    def __post_init__(self):
        if self.frameworks is None:
            self.frameworks = [ComplianceFramework.HIPAA]
        if self.data_residency_regions is None:
            self.data_residency_regions = ["us-east-1", "us-west-2"]


@dataclass
class SecurityConfig:
    """Main security configuration class."""
    encryption: EncryptionConfig
    access_control: AccessControlConfig
    audit: AuditConfig
    data_classification: DataClassificationConfig
    compliance: ComplianceConfig
    environment: str = "development"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'encryption': asdict(self.encryption),
            'access_control': asdict(self.access_control),
            'audit': asdict(self.audit),
            'data_classification': asdict(self.data_classification),
            'compliance': {
                'frameworks': [f.value for f in self.compliance.frameworks],
                'data_residency_regions': self.compliance.data_residency_regions,
                'data_retention_days': self.compliance.data_retention_days,
                'require_consent_tracking': self.compliance.require_consent_tracking,
                'enable_right_to_erasure': self.compliance.enable_right_to_erasure,
                'enable_data_portability': self.compliance.enable_data_portability
            },
            'environment': self.environment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityConfig':
        """Create from dictionary."""
        encryption_data = data.get('encryption', {})
        encryption_config = EncryptionConfig(
            data_at_rest_standard=EncryptionStandard(encryption_data.get('data_at_rest_standard', 'aes256')),
            data_in_transit_standard=EncryptionStandard(encryption_data.get('data_in_transit_standard', 'aes256_gcm')),
            key_rotation_days=encryption_data.get('key_rotation_days', 90),
            use_kms=encryption_data.get('use_kms', True),
            kms_key_id=encryption_data.get('kms_key_id'),
            enforce_encryption=encryption_data.get('enforce_encryption', True)
        )
        
        access_data = data.get('access_control', {})
        access_config = AccessControlConfig(
            require_mfa=access_data.get('require_mfa', False),
            session_timeout_minutes=access_data.get('session_timeout_minutes', 60),
            max_failed_attempts=access_data.get('max_failed_attempts', 5),
            lockout_duration_minutes=access_data.get('lockout_duration_minutes', 30),
            require_secure_transport=access_data.get('require_secure_transport', True),
            allowed_ip_ranges=access_data.get('allowed_ip_ranges', [])
        )
        
        audit_data = data.get('audit', {})
        audit_config = AuditConfig(
            enable_audit_logging=audit_data.get('enable_audit_logging', True),
            log_data_access=audit_data.get('log_data_access', True),
            log_data_processing=audit_data.get('log_data_processing', True),
            log_authentication=audit_data.get('log_authentication', True),
            log_errors=audit_data.get('log_errors', True),
            retention_days=audit_data.get('retention_days', 2555),
            enable_cloudwatch=audit_data.get('enable_cloudwatch', True),
            enable_cloudtrail=audit_data.get('enable_cloudtrail', True),
            log_level=audit_data.get('log_level', 'INFO')
        )
        
        classification_data = data.get('data_classification', {})
        classification_config = DataClassificationConfig(
            default_classification=classification_data.get('default_classification', 'confidential'),
            genomic_data_classification=classification_data.get('genomic_data_classification', 'restricted'),
            medical_data_classification=classification_data.get('medical_data_classification', 'restricted'),
            research_data_classification=classification_data.get('research_data_classification', 'confidential'),
            system_data_classification=classification_data.get('system_data_classification', 'internal'),
            public_data_classification=classification_data.get('public_data_classification', 'public')
        )
        
        compliance_data = data.get('compliance', {})
        frameworks = [ComplianceFramework(f) for f in compliance_data.get('frameworks', ['hipaa'])]
        compliance_config = ComplianceConfig(
            frameworks=frameworks,
            data_residency_regions=compliance_data.get('data_residency_regions', ['us-east-1', 'us-west-2']),
            data_retention_days=compliance_data.get('data_retention_days', 2555),
            require_consent_tracking=compliance_data.get('require_consent_tracking', True),
            enable_right_to_erasure=compliance_data.get('enable_right_to_erasure', True),
            enable_data_portability=compliance_data.get('enable_data_portability', True)
        )
        
        return cls(
            encryption=encryption_config,
            access_control=access_config,
            audit=audit_config,
            data_classification=classification_config,
            compliance=compliance_config,
            environment=data.get('environment', 'development')
        )


class SecurityConfigManager:
    """Manages security configuration loading and validation."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize security configuration manager."""
        self.logger = get_logger(__name__)
        self.config_file = config_file or self._get_default_config_path()
        self._config: Optional[SecurityConfig] = None
    
    def _get_default_config_path(self) -> str:
        """Get default security configuration file path."""
        # Check for environment variable first
        if 'BIOMERKIN_SECURITY_CONFIG' in os.environ:
            return os.environ['BIOMERKIN_SECURITY_CONFIG']
        
        # Check for config file in current directory
        current_dir_config = Path('./biomerkin_security_config.json')
        if current_dir_config.exists():
            return str(current_dir_config)
        
        # Check for config file in .biomerkin directory
        biomerkin_dir = Path.home() / '.biomerkin'
        biomerkin_config = biomerkin_dir / 'security_config.json'
        if biomerkin_config.exists():
            return str(biomerkin_config)
        
        # Default path
        return str(Path('./biomerkin_security_config.json'))
    
    def load_config(self) -> SecurityConfig:
        """Load security configuration from file and environment variables."""
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config_data = self._get_default_config_data()
        
        # Load from file if it exists
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    config_data.update(file_config)
            except Exception as e:
                self.logger.warning(f"Could not load security config from {config_path}: {e}")
        
        # Override with environment variables
        config_data = self._load_from_environment(config_data)
        
        # Create configuration object
        self._config = SecurityConfig.from_dict(config_data)
        
        # Validate configuration
        validation_errors = self.validate_config(self._config)
        if validation_errors:
            self.logger.warning(f"Security configuration validation issues: {validation_errors}")
        
        return self._config
    
    def _get_default_config_data(self) -> Dict[str, Any]:
        """Get default security configuration data."""
        default_config = SecurityConfig(
            encryption=EncryptionConfig(),
            access_control=AccessControlConfig(),
            audit=AuditConfig(),
            data_classification=DataClassificationConfig(),
            compliance=ComplianceConfig()
        )
        return default_config.to_dict()
    
    def _load_from_environment(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration values from environment variables."""
        # Encryption settings
        encryption = config_data.get('encryption', {})
        encryption['use_kms'] = os.getenv('BIOMERKIN_USE_KMS', str(encryption.get('use_kms', True))).lower() == 'true'
        encryption['kms_key_id'] = os.getenv('BIOMERKIN_KMS_KEY_ID', encryption.get('kms_key_id'))
        encryption['enforce_encryption'] = os.getenv('BIOMERKIN_ENFORCE_ENCRYPTION', str(encryption.get('enforce_encryption', True))).lower() == 'true'
        
        # Access control settings
        access_control = config_data.get('access_control', {})
        access_control['require_mfa'] = os.getenv('BIOMERKIN_REQUIRE_MFA', str(access_control.get('require_mfa', False))).lower() == 'true'
        access_control['require_secure_transport'] = os.getenv('BIOMERKIN_REQUIRE_HTTPS', str(access_control.get('require_secure_transport', True))).lower() == 'true'
        
        # Audit settings
        audit = config_data.get('audit', {})
        audit['enable_audit_logging'] = os.getenv('BIOMERKIN_ENABLE_AUDIT', str(audit.get('enable_audit_logging', True))).lower() == 'true'
        audit['enable_cloudwatch'] = os.getenv('BIOMERKIN_ENABLE_CLOUDWATCH', str(audit.get('enable_cloudwatch', True))).lower() == 'true'
        audit['enable_cloudtrail'] = os.getenv('BIOMERKIN_ENABLE_CLOUDTRAIL', str(audit.get('enable_cloudtrail', True))).lower() == 'true'
        
        # Compliance settings
        compliance = config_data.get('compliance', {})
        if 'BIOMERKIN_COMPLIANCE_FRAMEWORKS' in os.environ:
            frameworks = os.environ['BIOMERKIN_COMPLIANCE_FRAMEWORKS'].split(',')
            compliance['frameworks'] = [f.strip().lower() for f in frameworks]
        
        if 'BIOMERKIN_DATA_RESIDENCY_REGIONS' in os.environ:
            regions = os.environ['BIOMERKIN_DATA_RESIDENCY_REGIONS'].split(',')
            compliance['data_residency_regions'] = [r.strip() for r in regions]
        
        # Environment
        config_data['environment'] = os.getenv('BIOMERKIN_ENVIRONMENT', config_data.get('environment', 'development'))
        
        # Update nested configs
        config_data['encryption'] = encryption
        config_data['access_control'] = access_control
        config_data['audit'] = audit
        config_data['compliance'] = compliance
        
        return config_data
    
    def validate_config(self, config: SecurityConfig) -> List[str]:
        """Validate security configuration and return list of issues."""
        issues = []
        
        # Validate encryption settings
        if config.environment == 'production':
            if not config.encryption.enforce_encryption:
                issues.append("Encryption enforcement is required in production")
            
            if not config.encryption.use_kms:
                issues.append("KMS usage is recommended in production")
            
            if config.encryption.key_rotation_days > 365:
                issues.append("Key rotation period should be less than 365 days in production")
        
        # Validate access control
        if config.environment == 'production' and not config.access_control.require_secure_transport:
            issues.append("Secure transport (HTTPS) is required in production")
        
        # Validate audit settings
        if config.environment == 'production':
            if not config.audit.enable_audit_logging:
                issues.append("Audit logging is required in production")
            
            if not config.audit.enable_cloudtrail:
                issues.append("CloudTrail is recommended in production")
        
        # Validate compliance settings
        if ComplianceFramework.HIPAA in config.compliance.frameworks:
            if config.audit.retention_days < 2555:  # 7 years
                issues.append("HIPAA requires minimum 7-year audit log retention")
            
            if not config.compliance.require_consent_tracking:
                issues.append("HIPAA requires consent tracking")
        
        if ComplianceFramework.GDPR in config.compliance.frameworks:
            if not config.compliance.enable_right_to_erasure:
                issues.append("GDPR requires right to erasure capability")
            
            if not config.compliance.enable_data_portability:
                issues.append("GDPR requires data portability capability")
        
        return issues
    
    def save_config(self, config: SecurityConfig) -> None:
        """Save security configuration to file."""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        # Set restrictive permissions
        config_path.chmod(0o600)
        
        self._config = config
    
    def get_config(self) -> SecurityConfig:
        """Get current security configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config


# Global security configuration manager instance
security_config_manager = SecurityConfigManager()


def get_security_config() -> SecurityConfig:
    """Get the global security configuration instance."""
    return security_config_manager.get_config()


def create_sample_security_config(file_path: str = './biomerkin_security_config.json') -> None:
    """Create a sample security configuration file."""
    sample_config = SecurityConfig(
        encryption=EncryptionConfig(),
        access_control=AccessControlConfig(),
        audit=AuditConfig(),
        data_classification=DataClassificationConfig(),
        compliance=ComplianceConfig()
    )
    
    config_path = Path(file_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(sample_config.to_dict(), f, indent=2)
    
    # Set restrictive permissions
    config_path.chmod(0o600)
    
    print(f"Sample security configuration created at: {file_path}")
    print("Please review and update the configuration according to your security requirements.")


def validate_compliance_requirements(data_type: str, operation: str) -> List[str]:
    """
    Validate compliance requirements for specific data operations.
    
    Args:
        data_type: Type of data being processed
        operation: Operation being performed
        
    Returns:
        List of compliance requirements that must be met
    """
    config = get_security_config()
    requirements = []
    
    # HIPAA requirements
    if ComplianceFramework.HIPAA in config.compliance.frameworks:
        if data_type in ['genomic', 'medical', 'patient']:
            requirements.extend([
                "Encrypt data at rest and in transit",
                "Log all access and processing activities",
                "Implement access controls and authentication",
                "Ensure data integrity and availability"
            ])
            
            if operation in ['export', 'share', 'transmit']:
                requirements.append("Obtain patient consent for data sharing")
    
    # GDPR requirements
    if ComplianceFramework.GDPR in config.compliance.frameworks:
        if data_type in ['personal', 'genomic', 'medical']:
            requirements.extend([
                "Implement privacy by design",
                "Enable data subject rights (access, rectification, erasure)",
                "Conduct data protection impact assessment if required",
                "Ensure lawful basis for processing"
            ])
            
            if operation == 'cross_border_transfer':
                requirements.append("Ensure adequate protection for international transfers")
    
    return requirements