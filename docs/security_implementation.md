# Security Implementation Guide

## Overview

The Biomerkin multi-agent system implements comprehensive security and compliance features to protect sensitive genomic and medical data. This document outlines the security architecture, implementation details, and usage guidelines.

## Security Architecture

### Core Security Components

1. **Encryption Manager** (`biomerkin.utils.security.EncryptionManager`)
   - Data-at-rest encryption using AES-256
   - Data-in-transit encryption with TLS
   - AWS KMS integration for key management
   - Automatic key rotation

2. **Input Validator** (`biomerkin.utils.security.InputValidator`)
   - DNA/protein sequence validation
   - XSS and injection attack prevention
   - Size limit enforcement
   - Pattern-based validation

3. **Output Sanitizer** (`biomerkin.utils.security.OutputSanitizer`)
   - PII redaction (emails, SSNs, etc.)
   - Sensitive data removal
   - Security level-based sanitization
   - Nested data structure handling

4. **Audit Logger** (`biomerkin.utils.security.AuditLogger`)
   - Comprehensive audit trail
   - CloudWatch integration
   - Compliance-ready log retention
   - Real-time monitoring

5. **Security Middleware** (`biomerkin.utils.security_middleware`)
   - Decorator-based security integration
   - Operation-level security controls
   - Context-aware security policies
   - Automatic compliance checking

## Security Features

### Data Protection

#### Encryption
- **At Rest**: All sensitive data encrypted using AES-256
- **In Transit**: TLS 1.2+ for all communications
- **Key Management**: AWS KMS with automatic rotation
- **Field-Level**: Selective encryption of sensitive fields

```python
from biomerkin.utils.security import encrypt_sensitive_data, decrypt_sensitive_data

# Encrypt sensitive genomic data
encrypted_sequence = encrypt_sensitive_data(dna_sequence, SecurityLevel.RESTRICTED)

# Decrypt when needed
decrypted_sequence = decrypt_sensitive_data(encrypted_sequence, str)
```

#### Data Classification
- **Public**: Non-sensitive information
- **Internal**: Internal system data
- **Confidential**: Sensitive research data
- **Restricted**: Genomic and medical data

### Access Control

#### IAM Policies
- Least-privilege access principles
- Role-based access control (RBAC)
- Resource-based policies
- MFA requirements for human users

#### Network Security
- VPC security groups
- HTTPS-only communication
- IP allowlisting support
- Secure transport enforcement

### Input Validation

#### Genomic Data Validation
```python
from biomerkin.utils.security import validate_input

# Validate DNA sequence
is_valid, errors = validate_input(dna_sequence, 'dna_sequence')
if not is_valid:
    raise SecurityError(f"Invalid DNA sequence: {errors}")
```

#### Supported Validations
- DNA sequence format (A, T, C, G, N only)
- Protein sequence format (20 amino acids)
- File size limits
- JSON payload validation
- XSS/injection prevention

### Output Sanitization

#### Security Level-Based Sanitization
```python
from biomerkin.utils.security import sanitize_output, SecurityLevel

# Sanitize for public consumption
public_data = sanitize_output(results, SecurityLevel.PUBLIC)

# Sanitize for internal use
internal_data = sanitize_output(results, SecurityLevel.INTERNAL)
```

#### Automatic PII Redaction
- Email addresses → `[EMAIL_REDACTED]`
- SSNs → `[SSN_REDACTED]`
- Credit cards → `[CARD_REDACTED]`
- IP addresses → `[IP_REDACTED]`
- API keys → `[REDACTED]`

### Audit Logging

#### Comprehensive Audit Trail
```python
from biomerkin.utils.security import log_audit_event, AuditEventType

# Log data access
log_audit_event(
    AuditEventType.DATA_ACCESS,
    "genomic_data",
    "sequence_analysis",
    "success",
    user_id="researcher-123",
    workflow_id="workflow-456",
    details={"sequence_length": 1000}
)
```

#### Audit Event Types
- Data access and processing
- Authentication and authorization
- System access and configuration changes
- Error occurrences
- Data export and sharing

## Compliance Framework Support

### HIPAA Compliance
- 7-year audit log retention
- Encryption requirements
- Access controls and authentication
- Consent tracking
- Data integrity and availability

### GDPR Compliance
- Privacy by design
- Data subject rights (access, rectification, erasure)
- Data portability
- Lawful basis for processing
- Data protection impact assessments

### Implementation Example
```python
from biomerkin.utils.security_config import validate_compliance_requirements

# Check compliance requirements
requirements = validate_compliance_requirements('genomic', 'process')
print(f"Compliance requirements: {requirements}")
```

## Security Middleware Integration

### Agent Security Integration
```python
from biomerkin.utils.security_middleware import (
    secure_genomic_operation, validate_genomic_input, 
    encrypt_sensitive_fields, audit_data_access
)

class SecureGenomicsAgent:
    @secure_genomic_operation("dna_analysis")
    @validate_genomic_input
    @encrypt_sensitive_fields("dna_sequence", "mutations")
    @audit_data_access("genomic_data", "analyze")
    def analyze_sequence(self, sequence_file: str):
        # Agent implementation with automatic security
        pass
```

### Available Decorators
- `@secure_genomic_operation()` - Full genomic data security
- `@secure_protein_operation()` - Protein data security
- `@secure_medical_operation()` - Medical data security
- `@validate_genomic_input` - Input validation
- `@encrypt_sensitive_fields()` - Field-level encryption
- `@audit_data_access()` - Audit logging
- `@sanitize_medical_output()` - Output sanitization

## AWS Security Infrastructure

### KMS Key Management
- Separate keys for data and audit encryption
- Automatic key rotation
- Cross-service key usage policies
- Hardware security module (HSM) backing

### CloudTrail Audit Logging
- Multi-region trail configuration
- Log file validation
- S3 bucket encryption
- Real-time monitoring

### S3 Security
- Bucket-level encryption
- Public access blocking
- Secure transport enforcement
- Versioning and lifecycle policies

### IAM Security
- Least-privilege policies
- Resource-based access control
- Security boundary policies
- Regular access reviews

## Security Configuration

### Configuration Management
```python
from biomerkin.utils.security_config import get_security_config

# Get current security configuration
config = get_security_config()

# Check encryption settings
if config.encryption.enforce_encryption:
    print("Encryption is enforced")

# Check compliance frameworks
for framework in config.compliance.frameworks:
    print(f"Compliance framework: {framework.value}")
```

### Environment Variables
```bash
# Encryption settings
export BIOMERKIN_USE_KMS=true
export BIOMERKIN_KMS_KEY_ID=alias/biomerkin-data-encryption
export BIOMERKIN_ENFORCE_ENCRYPTION=true

# Access control
export BIOMERKIN_REQUIRE_MFA=true
export BIOMERKIN_REQUIRE_HTTPS=true

# Audit settings
export BIOMERKIN_ENABLE_AUDIT=true
export BIOMERKIN_ENABLE_CLOUDWATCH=true
export BIOMERKIN_ENABLE_CLOUDTRAIL=true

# Compliance
export BIOMERKIN_COMPLIANCE_FRAMEWORKS=hipaa,gdpr
export BIOMERKIN_DATA_RESIDENCY_REGIONS=us-east-1,us-west-2
```

## Security Testing

### Automated Security Tests
```bash
# Run security tests
python -m pytest tests/test_security.py -v

# Run basic security validation
python test_security_basic.py
```

### Vulnerability Assessment
- XSS prevention testing
- SQL injection prevention
- Input validation testing
- Output sanitization verification
- Encryption/decryption validation

### Security Monitoring
- Real-time security alerts
- Anomaly detection
- Access pattern monitoring
- Compliance violation alerts

## Deployment Security

### Infrastructure Deployment
```bash
# Deploy security infrastructure
python deploy/security_deployment.py us-east-1

# Validate security deployment
python -c "from deploy.security_deployment import validate_security_infrastructure; print(validate_security_infrastructure())"
```

### Security Checklist
- [ ] KMS keys created and configured
- [ ] CloudTrail enabled with encryption
- [ ] S3 buckets secured with encryption
- [ ] IAM policies follow least-privilege
- [ ] Security groups restrict access
- [ ] Audit logging configured
- [ ] Compliance frameworks enabled
- [ ] Security tests passing

## Best Practices

### Development
1. Always use security decorators for sensitive operations
2. Validate all inputs before processing
3. Sanitize outputs based on security level
4. Log all data access and processing activities
5. Use encryption for sensitive data storage
6. Follow least-privilege access principles

### Operations
1. Regularly rotate encryption keys
2. Monitor audit logs for anomalies
3. Review access patterns and permissions
4. Update security configurations as needed
5. Conduct regular security assessments
6. Maintain compliance documentation

### Data Handling
1. Classify data according to sensitivity
2. Apply appropriate security controls
3. Obtain consent for genomic data processing
4. Implement data retention policies
5. Enable data subject rights (GDPR)
6. Maintain data lineage and provenance

## Troubleshooting

### Common Issues

#### Encryption Errors
```python
# Check if KMS key is accessible
from biomerkin.utils.security import EncryptionManager
manager = EncryptionManager(kms_key_id='your-key-id')
```

#### Validation Failures
```python
# Debug input validation
from biomerkin.utils.security import InputValidator
validator = InputValidator()
is_valid, errors = validator.validate_dna_sequence(sequence)
print(f"Validation errors: {errors}")
```

#### Audit Logging Issues
```python
# Check CloudWatch connectivity
from biomerkin.utils.security import AuditLogger
logger = AuditLogger(log_to_cloudwatch=True)
```

### Security Incident Response
1. Identify and contain the incident
2. Assess the scope and impact
3. Preserve audit logs and evidence
4. Notify relevant stakeholders
5. Implement remediation measures
6. Document lessons learned

## Security Updates

### Regular Maintenance
- Update cryptographic libraries
- Review and update IAM policies
- Rotate encryption keys
- Update security configurations
- Conduct security assessments

### Monitoring and Alerting
- Set up CloudWatch alarms
- Monitor audit logs
- Track compliance metrics
- Alert on security violations
- Regular security reviews

## Contact and Support

For security-related questions or incidents:
- Review this documentation
- Check the security test suite
- Consult the audit logs
- Follow incident response procedures
- Contact the security team

---

**Note**: This security implementation follows industry best practices and compliance requirements. Regular reviews and updates are essential to maintain security posture.