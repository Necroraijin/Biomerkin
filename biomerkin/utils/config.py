"""
Configuration management for API keys and AWS settings.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class AWSConfig:
    """AWS configuration settings."""
    region: str = "us-east-1"
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    lambda_timeout: int = 900  # 15 minutes
    lambda_memory: int = 1024  # MB

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AWSConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class APIConfig:
    """External API configuration settings."""
    pubmed_api_key: Optional[str] = None
    pubmed_email: Optional[str] = None  # Required for PubMed API
    drugbank_api_key: Optional[str] = None
    pdb_api_base_url: str = "https://data.rcsb.org/rest/v1"
    clinicaltrials_api_base_url: str = "https://clinicaltrials.gov/api"
    request_timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    dynamodb_table_name: str = "biomerkin-workflows"
    s3_bucket_name: str = "biomerkin-data"
    s3_results_prefix: str = "results/"
    s3_uploads_prefix: str = "uploads/"
    cache_ttl: int = 3600  # 1 hour in seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    enabled: bool = True
    backend_type: str = "dynamodb"  # "dynamodb" or "memory"
    dynamodb_table_name: str = "biomerkin-cache"
    memory_max_size: int = 1000  # Max entries for in-memory cache
    default_ttl_seconds: int = 3600  # 1 hour
    api_response_ttl: int = 3600  # 1 hour
    computation_result_ttl: int = 7200  # 2 hours
    literature_search_ttl: int = 86400  # 24 hours
    protein_structure_ttl: int = 604800  # 1 week
    drug_candidate_ttl: int = 86400  # 24 hours
    genomics_analysis_ttl: int = 3600  # 1 hour
    health_check_interval_minutes: int = 5
    enable_cloudwatch_metrics: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheConfig':
        """Create from dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatabaseConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ProcessingConfig:
    """Processing configuration settings."""
    max_sequence_length: int = 1000000  # 1MB
    max_concurrent_agents: int = 2
    enable_caching: bool = True
    log_level: str = "INFO"
    enable_detailed_logging: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class BiomerkinConfig:
    """Main configuration class for Biomerkin system."""
    aws: AWSConfig
    api: APIConfig
    database: DatabaseConfig
    processing: ProcessingConfig
    cache: CacheConfig
    environment: str = "development"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'aws': self.aws.to_dict(),
            'api': self.api.to_dict(),
            'database': self.database.to_dict(),
            'processing': self.processing.to_dict(),
            'cache': self.cache.to_dict(),
            'environment': self.environment
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiomerkinConfig':
        """Create from dictionary."""
        return cls(
            aws=AWSConfig.from_dict(data.get('aws', {})),
            api=APIConfig.from_dict(data.get('api', {})),
            database=DatabaseConfig.from_dict(data.get('database', {})),
            processing=ProcessingConfig.from_dict(data.get('processing', {})),
            cache=CacheConfig.from_dict(data.get('cache', {})),
            environment=data.get('environment', 'development')
        )


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_file = config_file or self._get_default_config_path()
        self._config: Optional[BiomerkinConfig] = None
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Check for environment variable first
        if 'BIOMERKIN_CONFIG' in os.environ:
            return os.environ['BIOMERKIN_CONFIG']
        
        # Check for config file in current directory
        current_dir_config = Path('./biomerkin_config.json')
        if current_dir_config.exists():
            return str(current_dir_config)
        
        # Check for config file in home directory
        home_config = Path.home() / '.biomerkin' / 'config.json'
        if home_config.exists():
            return str(home_config)
        
        # Default path
        return str(Path('./biomerkin_config.json'))
    
    def load_config(self) -> BiomerkinConfig:
        """Load configuration from file and environment variables."""
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config_data = {}
        
        # Load from file if it exists
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        
        # Override with environment variables
        config_data = self._load_from_environment(config_data)
        
        # Create configuration object
        self._config = BiomerkinConfig.from_dict(config_data)
        
        return self._config
    
    def _load_from_environment(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration values from environment variables."""
        # AWS configuration
        aws_config = config_data.get('aws', {})
        aws_config['region'] = os.getenv('AWS_REGION', aws_config.get('region', 'us-east-1'))
        aws_config['access_key_id'] = os.getenv('AWS_ACCESS_KEY_ID', aws_config.get('access_key_id'))
        aws_config['secret_access_key'] = os.getenv('AWS_SECRET_ACCESS_KEY', aws_config.get('secret_access_key'))
        aws_config['session_token'] = os.getenv('AWS_SESSION_TOKEN', aws_config.get('session_token'))
        aws_config['bedrock_model_id'] = os.getenv('BEDROCK_MODEL_ID', aws_config.get('bedrock_model_id', 'anthropic.claude-3-sonnet-20240229-v1:0'))
        
        # API configuration
        api_config = config_data.get('api', {})
        api_config['pubmed_api_key'] = os.getenv('PUBMED_API_KEY', api_config.get('pubmed_api_key'))
        api_config['pubmed_email'] = os.getenv('PUBMED_EMAIL', api_config.get('pubmed_email'))
        api_config['drugbank_api_key'] = os.getenv('DRUGBANK_API_KEY', api_config.get('drugbank_api_key'))
        
        # Database configuration
        db_config = config_data.get('database', {})
        db_config['dynamodb_table_name'] = os.getenv('DYNAMODB_TABLE_NAME', db_config.get('dynamodb_table_name', 'biomerkin-workflows'))
        db_config['s3_bucket_name'] = os.getenv('S3_BUCKET_NAME', db_config.get('s3_bucket_name', 'biomerkin-data'))
        
        # Cache configuration
        cache_config = config_data.get('cache', {})
        cache_config['enabled'] = os.getenv('CACHE_ENABLED', str(cache_config.get('enabled', True))).lower() == 'true'
        cache_config['backend_type'] = os.getenv('CACHE_BACKEND_TYPE', cache_config.get('backend_type', 'dynamodb'))
        cache_config['dynamodb_table_name'] = os.getenv('CACHE_DYNAMODB_TABLE', cache_config.get('dynamodb_table_name', 'biomerkin-cache'))
        
        # Processing configuration
        proc_config = config_data.get('processing', {})
        proc_config['log_level'] = os.getenv('LOG_LEVEL', proc_config.get('log_level', 'INFO'))
        proc_config['enable_caching'] = os.getenv('ENABLE_CACHING', str(proc_config.get('enable_caching', True))).lower() == 'true'
        
        # Environment
        config_data['environment'] = os.getenv('ENVIRONMENT', config_data.get('environment', 'development'))
        
        # Update config data
        config_data['aws'] = aws_config
        config_data['api'] = api_config
        config_data['database'] = db_config
        config_data['cache'] = cache_config
        config_data['processing'] = proc_config
        
        return config_data
    
    def save_config(self, config: BiomerkinConfig) -> None:
        """Save configuration to file."""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        self._config = config
    
    def validate_config(self, config: BiomerkinConfig) -> list:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required AWS settings for production
        if config.environment == 'production':
            if not config.aws.region:
                issues.append("AWS region is required for production")
        
        # Check API settings
        if not config.api.pubmed_email:
            issues.append("PubMed email is required for API access")
        
        # Check database settings
        if not config.database.dynamodb_table_name:
            issues.append("DynamoDB table name is required")
        
        if not config.database.s3_bucket_name:
            issues.append("S3 bucket name is required")
        
        return issues
    
    def get_config(self) -> BiomerkinConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> BiomerkinConfig:
    """Get the global configuration instance."""
    return config_manager.get_config()


def create_sample_config(file_path: str = './biomerkin_config.json') -> None:
    """Create a sample configuration file."""
    sample_config = BiomerkinConfig(
        aws=AWSConfig(),
        api=APIConfig(),
        database=DatabaseConfig(),
        processing=ProcessingConfig(),
        cache=CacheConfig()
    )
    
    config_path = Path(file_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(sample_config.to_dict(), f, indent=2)
    
    print(f"Sample configuration created at: {file_path}")
    print("Please update the configuration with your API keys and AWS settings.")