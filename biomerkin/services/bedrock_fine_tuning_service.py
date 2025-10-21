"""
Bedrock Model Fine-tuning Service for Bioinformatics Domain.

This service implements custom model fine-tuning capabilities for:
- Domain-specific bioinformatics terminology and concepts
- Improved accuracy for genomics and medical analysis
- Specialized reasoning for clinical decision-making
- Cost-effective model optimization
"""

import json
import boto3
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import asyncio

from ..utils.logging_config import get_logger
from ..utils.config import get_config
from .dynamodb_client import DynamoDBClient


class FineTuningJobStatus(Enum):
    """Fine-tuning job status."""
    SUBMITTED = "Submitted"
    IN_PROGRESS = "InProgress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    STOPPED = "Stopped"


class ModelType(Enum):
    """Types of models for fine-tuning."""
    GENOMICS_ANALYSIS = "genomics_analysis"
    MEDICAL_REASONING = "medical_reasoning"
    LITERATURE_SUMMARIZATION = "literature_summarization"
    DRUG_DISCOVERY = "drug_discovery"
    CLINICAL_DECISION = "clinical_decision"


@dataclass
class FineTuningConfig:
    """Configuration for model fine-tuning."""
    model_name: str
    base_model_id: str
    model_type: ModelType
    training_data_s3_uri: str
    validation_data_s3_uri: Optional[str]
    hyperparameters: Dict[str, Any]
    training_epochs: int = 3
    learning_rate: float = 0.0001
    batch_size: int = 4
    max_sequence_length: int = 4096


@dataclass
class TrainingDataset:
    """Training dataset for fine-tuning."""
    dataset_id: str
    name: str
    description: str
    model_type: ModelType
    s3_uri: str
    sample_count: int
    validation_split: float = 0.2
    data_format: str = "jsonl"
    created_at: datetime = None


@dataclass
class FineTuningJob:
    """Fine-tuning job details."""
    job_id: str
    job_name: str
    model_name: str
    base_model_id: str
    status: FineTuningJobStatus
    training_data_uri: str
    validation_data_uri: Optional[str]
    hyperparameters: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    training_metrics: Dict[str, Any] = None
    validation_metrics: Dict[str, Any] = None
    custom_model_arn: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ModelEvaluation:
    """Model evaluation results."""
    model_arn: str
    evaluation_id: str
    test_dataset_uri: str
    metrics: Dict[str, float]
    sample_predictions: List[Dict[str, Any]]
    evaluation_time: float
    created_at: datetime


class BedrockFineTuningService:
    """
    Service for fine-tuning Bedrock models for bioinformatics applications.
    
    Provides capabilities for:
    - Creating domain-specific training datasets
    - Fine-tuning models for genomics and medical analysis
    - Evaluating model performance
    - Managing custom model deployments
    """
    
    def __init__(self, mock_mode: bool = False):
        """Initialize the Bedrock Fine-tuning Service."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.mock_mode = mock_mode
        
        if not mock_mode:
            # Initialize AWS clients
            self.bedrock_client = boto3.client('bedrock', region_name=self.config.aws.region)
            self.bedrock_runtime_client = boto3.client('bedrock-runtime', region_name=self.config.aws.region)
            self.s3_client = boto3.client('s3', region_name=self.config.aws.region)
            self.dynamodb_client = DynamoDBClient()
        
        # Fine-tuning configuration
        self.training_datasets: Dict[str, TrainingDataset] = {}
        self.active_jobs: Dict[str, FineTuningJob] = {}
        self.custom_models: Dict[str, str] = {}  # model_name -> model_arn
        
        # Default model configurations
        self.base_models = {
            ModelType.GENOMICS_ANALYSIS: "anthropic.claude-3-haiku-20240307-v1:0",
            ModelType.MEDICAL_REASONING: "anthropic.claude-3-sonnet-20240229-v1:0",
            ModelType.LITERATURE_SUMMARIZATION: "anthropic.claude-3-haiku-20240307-v1:0",
            ModelType.DRUG_DISCOVERY: "anthropic.claude-3-sonnet-20240229-v1:0",
            ModelType.CLINICAL_DECISION: "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        
        # Training data bucket
        self.training_bucket = f"biomerkin-model-training-{self.config.aws.region}"
        
        # Initialize default training datasets
        self._initialize_training_datasets()
    
    def _initialize_training_datasets(self):
        """Initialize default training datasets for bioinformatics domains."""
        
        # Genomics analysis dataset
        self.training_datasets['genomics_analysis'] = TrainingDataset(
            dataset_id="genomics_analysis_v1",
            name="Genomics Analysis Training Dataset",
            description="Training data for genomics sequence analysis and variant interpretation",
            model_type=ModelType.GENOMICS_ANALYSIS,
            s3_uri=f"s3://{self.training_bucket}/genomics/training_data.jsonl",
            sample_count=5000,
            validation_split=0.2,
            created_at=datetime.now()
        )
        
        # Medical reasoning dataset
        self.training_datasets['medical_reasoning'] = TrainingDataset(
            dataset_id="medical_reasoning_v1",
            name="Medical Reasoning Training Dataset",
            description="Training data for clinical reasoning and medical decision-making",
            model_type=ModelType.MEDICAL_REASONING,
            s3_uri=f"s3://{self.training_bucket}/medical/training_data.jsonl",
            sample_count=8000,
            validation_split=0.2,
            created_at=datetime.now()
        )
        
        # Literature summarization dataset
        self.training_datasets['literature_summarization'] = TrainingDataset(
            dataset_id="literature_summarization_v1",
            name="Literature Summarization Training Dataset",
            description="Training data for scientific literature summarization",
            model_type=ModelType.LITERATURE_SUMMARIZATION,
            s3_uri=f"s3://{self.training_bucket}/literature/training_data.jsonl",
            sample_count=6000,
            validation_split=0.2,
            created_at=datetime.now()
        )
    
    async def create_training_dataset(self, 
                                    dataset_config: TrainingDataset,
                                    source_data: List[Dict[str, Any]]) -> str:
        """
        Create a training dataset for model fine-tuning.
        
        Args:
            dataset_config: Dataset configuration
            source_data: Training examples in the required format
            
        Returns:
            Dataset ID
        """
        try:
            self.logger.info(f"Creating training dataset: {dataset_config.name}")
            
            # Validate training data format
            validated_data = self._validate_training_data(source_data, dataset_config.model_type)
            
            # Split into training and validation sets
            train_data, val_data = self._split_training_data(validated_data, dataset_config.validation_split)
            
            # Upload training data to S3
            train_s3_uri = await self._upload_training_data(
                train_data, f"{dataset_config.dataset_id}/train.jsonl"
            )
            
            val_s3_uri = await self._upload_training_data(
                val_data, f"{dataset_config.dataset_id}/validation.jsonl"
            )
            
            # Update dataset configuration
            dataset_config.s3_uri = train_s3_uri
            dataset_config.sample_count = len(train_data)
            dataset_config.created_at = datetime.now()
            
            # Store dataset metadata
            self.training_datasets[dataset_config.dataset_id] = dataset_config
            
            # Save to DynamoDB
            await self._save_dataset_metadata(dataset_config, val_s3_uri)
            
            self.logger.info(f"Created training dataset {dataset_config.dataset_id} with {len(train_data)} samples")
            return dataset_config.dataset_id
            
        except Exception as e:
            self.logger.error(f"Error creating training dataset: {str(e)}")
            raise
    
    def _validate_training_data(self, data: List[Dict[str, Any]], model_type: ModelType) -> List[Dict[str, Any]]:
        """Validate and format training data for the specific model type."""
        validated_data = []
        
        for i, example in enumerate(data):
            try:
                # Validate required fields
                if 'input' not in example or 'output' not in example:
                    self.logger.warning(f"Skipping example {i}: missing input or output")
                    continue
                
                # Format for Claude fine-tuning
                formatted_example = {
                    "messages": [
                        {
                            "role": "user",
                            "content": example['input']
                        },
                        {
                            "role": "assistant",
                            "content": example['output']
                        }
                    ]
                }
                
                # Add model-specific metadata
                if model_type == ModelType.GENOMICS_ANALYSIS:
                    formatted_example['metadata'] = {
                        'domain': 'genomics',
                        'task_type': example.get('task_type', 'sequence_analysis')
                    }
                elif model_type == ModelType.MEDICAL_REASONING:
                    formatted_example['metadata'] = {
                        'domain': 'medical',
                        'reasoning_type': example.get('reasoning_type', 'clinical_decision')
                    }
                
                validated_data.append(formatted_example)
                
            except Exception as e:
                self.logger.warning(f"Error validating example {i}: {str(e)}")
                continue
        
        self.logger.info(f"Validated {len(validated_data)} training examples")
        return validated_data
    
    def _split_training_data(self, data: List[Dict[str, Any]], validation_split: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split data into training and validation sets."""
        import random
        
        # Shuffle data
        shuffled_data = data.copy()
        random.shuffle(shuffled_data)
        
        # Calculate split point
        val_size = int(len(shuffled_data) * validation_split)
        
        validation_data = shuffled_data[:val_size]
        training_data = shuffled_data[val_size:]
        
        return training_data, validation_data
    
    async def _upload_training_data(self, data: List[Dict[str, Any]], s3_key: str) -> str:
        """Upload training data to S3."""
        if self.mock_mode:
            return f"s3://{self.training_bucket}/{s3_key}"
        
        try:
            # Ensure bucket exists
            await self._ensure_training_bucket_exists()
            
            # Convert to JSONL format
            jsonl_content = "\n".join(json.dumps(example) for example in data)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.training_bucket,
                Key=s3_key,
                Body=jsonl_content.encode('utf-8'),
                ContentType='application/jsonl'
            )
            
            s3_uri = f"s3://{self.training_bucket}/{s3_key}"
            self.logger.info(f"Uploaded training data to {s3_uri}")
            return s3_uri
            
        except Exception as e:
            self.logger.error(f"Error uploading training data: {str(e)}")
            raise
    
    async def start_fine_tuning_job(self, 
                                  job_name: str,
                                  model_name: str,
                                  dataset_id: str,
                                  fine_tuning_config: FineTuningConfig) -> str:
        """
        Start a model fine-tuning job.
        
        Args:
            job_name: Name for the fine-tuning job
            model_name: Name for the resulting custom model
            dataset_id: ID of the training dataset
            fine_tuning_config: Fine-tuning configuration
            
        Returns:
            Fine-tuning job ID
        """
        if self.mock_mode:
            job_id = f"mock_job_{uuid.uuid4().hex[:8]}"
            
            # Create mock job
            mock_job = FineTuningJob(
                job_id=job_id,
                job_name=job_name,
                model_name=model_name,
                base_model_id=fine_tuning_config.base_model_id,
                status=FineTuningJobStatus.IN_PROGRESS,
                training_data_uri=fine_tuning_config.training_data_s3_uri,
                validation_data_uri=fine_tuning_config.validation_data_s3_uri,
                hyperparameters=fine_tuning_config.hyperparameters,
                created_at=datetime.now()
            )
            
            self.active_jobs[job_id] = mock_job
            return job_id
        
        try:
            self.logger.info(f"Starting fine-tuning job: {job_name}")
            
            # Get dataset configuration
            dataset = self.training_datasets.get(dataset_id)
            if not dataset:
                raise ValueError(f"Dataset {dataset_id} not found")
            
            # Create fine-tuning job
            response = self.bedrock_client.create_model_customization_job(
                jobName=job_name,
                customModelName=model_name,
                roleArn=self._get_fine_tuning_role_arn(),
                baseModelIdentifier=fine_tuning_config.base_model_id,
                trainingDataConfig={
                    's3Uri': fine_tuning_config.training_data_s3_uri
                },
                validationDataConfig={
                    's3Uri': fine_tuning_config.validation_data_s3_uri
                } if fine_tuning_config.validation_data_s3_uri else None,
                hyperParameters={
                    'epochCount': str(fine_tuning_config.training_epochs),
                    'batchSize': str(fine_tuning_config.batch_size),
                    'learningRate': str(fine_tuning_config.learning_rate)
                }
            )
            
            job_id = response['jobArn'].split('/')[-1]
            
            # Create job tracking object
            job = FineTuningJob(
                job_id=job_id,
                job_name=job_name,
                model_name=model_name,
                base_model_id=fine_tuning_config.base_model_id,
                status=FineTuningJobStatus.SUBMITTED,
                training_data_uri=fine_tuning_config.training_data_s3_uri,
                validation_data_uri=fine_tuning_config.validation_data_s3_uri,
                hyperparameters=fine_tuning_config.hyperparameters,
                created_at=datetime.now()
            )
            
            self.active_jobs[job_id] = job
            
            # Save job metadata
            await self._save_job_metadata(job)
            
            self.logger.info(f"Started fine-tuning job {job_id}")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Error starting fine-tuning job: {str(e)}")
            raise
    
    async def monitor_fine_tuning_job(self, job_id: str) -> FineTuningJob:
        """
        Monitor the status of a fine-tuning job.
        
        Args:
            job_id: Fine-tuning job ID
            
        Returns:
            Updated job status
        """
        if self.mock_mode:
            job = self.active_jobs.get(job_id)
            if job:
                # Simulate job progression
                if job.status == FineTuningJobStatus.IN_PROGRESS:
                    job.status = FineTuningJobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    job.custom_model_arn = f"arn:aws:bedrock:us-east-1:123456789012:custom-model/{job.model_name}"
                    job.training_metrics = {
                        'final_loss': 0.245,
                        'perplexity': 1.87,
                        'accuracy': 0.923
                    }
            return job
        
        try:
            job = self.active_jobs.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Get job status from Bedrock
            response = self.bedrock_client.get_model_customization_job(
                jobIdentifier=job_id
            )
            
            # Update job status
            job.status = FineTuningJobStatus(response['status'])
            
            if response.get('trainingMetrics'):
                job.training_metrics = response['trainingMetrics']
            
            if response.get('validationMetrics'):
                job.validation_metrics = response['validationMetrics']
            
            if job.status == FineTuningJobStatus.COMPLETED:
                job.completed_at = datetime.now()
                job.custom_model_arn = response.get('outputModelArn')
                
                # Register the custom model
                if job.custom_model_arn:
                    self.custom_models[job.model_name] = job.custom_model_arn
            
            elif job.status == FineTuningJobStatus.FAILED:
                job.error_message = response.get('failureMessage', 'Unknown error')
            
            # Update job metadata
            await self._save_job_metadata(job)
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error monitoring fine-tuning job {job_id}: {str(e)}")
            raise
    
    async def evaluate_custom_model(self, 
                                  model_arn: str,
                                  test_dataset_uri: str,
                                  evaluation_name: str) -> ModelEvaluation:
        """
        Evaluate a custom model's performance.
        
        Args:
            model_arn: ARN of the custom model
            test_dataset_uri: S3 URI of test dataset
            evaluation_name: Name for the evaluation
            
        Returns:
            Model evaluation results
        """
        evaluation_id = f"eval_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            self.logger.info(f"Evaluating custom model: {model_arn}")
            
            if self.mock_mode:
                # Return mock evaluation results
                return ModelEvaluation(
                    model_arn=model_arn,
                    evaluation_id=evaluation_id,
                    test_dataset_uri=test_dataset_uri,
                    metrics={
                        'accuracy': 0.923,
                        'precision': 0.915,
                        'recall': 0.931,
                        'f1_score': 0.923,
                        'perplexity': 1.87,
                        'bleu_score': 0.845
                    },
                    sample_predictions=[
                        {
                            'input': 'Analyze this DNA sequence: ATCGATCG...',
                            'expected': 'This sequence contains a BRCA1 variant...',
                            'predicted': 'This sequence shows a BRCA1 pathogenic variant...',
                            'score': 0.92
                        }
                    ],
                    evaluation_time=45.2,
                    created_at=datetime.now()
                )
            
            # Load test dataset
            test_data = await self._load_test_dataset(test_dataset_uri)
            
            # Run evaluation
            evaluation_results = await self._run_model_evaluation(model_arn, test_data)
            
            # Calculate metrics
            metrics = self._calculate_evaluation_metrics(evaluation_results)
            
            # Create evaluation object
            evaluation = ModelEvaluation(
                model_arn=model_arn,
                evaluation_id=evaluation_id,
                test_dataset_uri=test_dataset_uri,
                metrics=metrics,
                sample_predictions=evaluation_results[:10],  # First 10 predictions
                evaluation_time=time.time() - start_time,
                created_at=datetime.now()
            )
            
            # Save evaluation results
            await self._save_evaluation_results(evaluation)
            
            self.logger.info(f"Model evaluation completed: {evaluation_id}")
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating model: {str(e)}")
            raise
    
    async def _run_model_evaluation(self, model_arn: str, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run model evaluation on test data."""
        evaluation_results = []
        
        for example in test_data:
            try:
                # Generate prediction using custom model
                prediction = await self._generate_prediction(model_arn, example['input'])
                
                result = {
                    'input': example['input'],
                    'expected': example['output'],
                    'predicted': prediction,
                    'score': self._calculate_similarity_score(example['output'], prediction)
                }
                
                evaluation_results.append(result)
                
            except Exception as e:
                self.logger.warning(f"Error evaluating example: {str(e)}")
                continue
        
        return evaluation_results
    
    async def _generate_prediction(self, model_arn: str, input_text: str) -> str:
        """Generate prediction using custom model."""
        try:
            response = self.bedrock_runtime_client.invoke_model(
                modelId=model_arn,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": input_text
                        }
                    ],
                    "temperature": 0.1
                })
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            self.logger.error(f"Error generating prediction: {str(e)}")
            return ""
    
    def _calculate_similarity_score(self, expected: str, predicted: str) -> float:
        """Calculate similarity score between expected and predicted outputs."""
        # Simple similarity calculation (could be enhanced with more sophisticated metrics)
        from difflib import SequenceMatcher
        
        similarity = SequenceMatcher(None, expected.lower(), predicted.lower()).ratio()
        return round(similarity, 3)
    
    def _calculate_evaluation_metrics(self, evaluation_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate evaluation metrics from results."""
        if not evaluation_results:
            return {}
        
        scores = [result['score'] for result in evaluation_results]
        
        metrics = {
            'accuracy': sum(1 for score in scores if score > 0.8) / len(scores),
            'average_similarity': sum(scores) / len(scores),
            'median_similarity': sorted(scores)[len(scores) // 2],
            'min_similarity': min(scores),
            'max_similarity': max(scores)
        }
        
        return {k: round(v, 3) for k, v in metrics.items()}
    
    async def deploy_custom_model(self, model_arn: str, deployment_name: str) -> Dict[str, Any]:
        """
        Deploy a custom model for inference.
        
        Args:
            model_arn: ARN of the custom model
            deployment_name: Name for the deployment
            
        Returns:
            Deployment details
        """
        try:
            self.logger.info(f"Deploying custom model: {model_arn}")
            
            if self.mock_mode:
                return {
                    'deployment_id': f"deploy_{uuid.uuid4().hex[:8]}",
                    'model_arn': model_arn,
                    'deployment_name': deployment_name,
                    'status': 'ACTIVE',
                    'endpoint_url': f"https://bedrock-runtime.{self.config.aws.region}.amazonaws.com/model/{model_arn}/invoke",
                    'created_at': datetime.now().isoformat()
                }
            
            # In a real implementation, this would create a model endpoint
            # For Bedrock, custom models are automatically available for inference
            deployment_info = {
                'deployment_id': f"bedrock_{uuid.uuid4().hex[:8]}",
                'model_arn': model_arn,
                'deployment_name': deployment_name,
                'status': 'ACTIVE',
                'endpoint_url': f"https://bedrock-runtime.{self.config.aws.region}.amazonaws.com/model/{model_arn}/invoke",
                'created_at': datetime.now().isoformat()
            }
            
            # Register deployment
            await self._save_deployment_info(deployment_info)
            
            self.logger.info(f"Custom model deployed: {deployment_name}")
            return deployment_info
            
        except Exception as e:
            self.logger.error(f"Error deploying custom model: {str(e)}")
            raise
    
    async def optimize_model_costs(self, model_type: ModelType) -> Dict[str, Any]:
        """
        Optimize costs for model usage and fine-tuning.
        
        Args:
            model_type: Type of model to optimize
            
        Returns:
            Cost optimization recommendations
        """
        try:
            self.logger.info(f"Optimizing costs for model type: {model_type.value}")
            
            # Analyze current usage patterns
            usage_analysis = await self._analyze_model_usage(model_type)
            
            # Generate cost optimization recommendations
            recommendations = self._generate_cost_recommendations(usage_analysis)
            
            # Calculate potential savings
            potential_savings = self._calculate_potential_savings(usage_analysis, recommendations)
            
            optimization_results = {
                'model_type': model_type.value,
                'current_usage': usage_analysis,
                'recommendations': recommendations,
                'potential_savings': potential_savings,
                'optimization_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Cost optimization completed for {model_type.value}")
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Error optimizing model costs: {str(e)}")
            raise
    
    async def _analyze_model_usage(self, model_type: ModelType) -> Dict[str, Any]:
        """Analyze current model usage patterns."""
        # Mock usage analysis - in real implementation, this would query CloudWatch metrics
        return {
            'daily_invocations': 1250,
            'average_tokens_per_request': 850,
            'peak_usage_hours': [9, 10, 14, 15, 16],
            'cost_per_day_usd': 15.75,
            'monthly_projection_usd': 472.50,
            'cache_hit_rate': 0.35,
            'error_rate': 0.02
        }
    
    def _generate_cost_recommendations(self, usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Cache optimization
        if usage_analysis['cache_hit_rate'] < 0.5:
            recommendations.append({
                'type': 'caching',
                'description': 'Implement intelligent caching for repeated queries',
                'potential_savings_percent': 25,
                'implementation_effort': 'medium'
            })
        
        # Model size optimization
        if usage_analysis['average_tokens_per_request'] < 500:
            recommendations.append({
                'type': 'model_size',
                'description': 'Use smaller, more efficient model for simple queries',
                'potential_savings_percent': 40,
                'implementation_effort': 'low'
            })
        
        # Batch processing
        recommendations.append({
            'type': 'batch_processing',
            'description': 'Implement batch processing for similar queries',
            'potential_savings_percent': 15,
            'implementation_effort': 'medium'
        })
        
        # Request optimization
        recommendations.append({
            'type': 'request_optimization',
            'description': 'Optimize prompts to reduce token usage',
            'potential_savings_percent': 20,
            'implementation_effort': 'low'
        })
        
        return recommendations
    
    def _calculate_potential_savings(self, usage_analysis: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate potential cost savings from recommendations."""
        current_monthly_cost = usage_analysis['monthly_projection_usd']
        
        total_savings_percent = sum(rec['potential_savings_percent'] for rec in recommendations)
        # Cap total savings at 70% to be realistic
        total_savings_percent = min(total_savings_percent, 70)
        
        monthly_savings = current_monthly_cost * (total_savings_percent / 100)
        annual_savings = monthly_savings * 12
        
        return {
            'current_monthly_cost_usd': current_monthly_cost,
            'potential_monthly_savings_usd': round(monthly_savings, 2),
            'potential_annual_savings_usd': round(annual_savings, 2),
            'total_savings_percent': total_savings_percent,
            'roi_months': 2.5  # Estimated months to recoup optimization investment
        }
    
    # Helper methods for data management
    async def _ensure_training_bucket_exists(self):
        """Ensure S3 bucket exists for training data."""
        try:
            self.s3_client.head_bucket(Bucket=self.training_bucket)
        except:
            self.s3_client.create_bucket(
                Bucket=self.training_bucket,
                CreateBucketConfiguration={'LocationConstraint': self.config.aws.region}
            )
            self.logger.info(f"Created training bucket: {self.training_bucket}")
    
    async def _save_dataset_metadata(self, dataset: TrainingDataset, validation_uri: str):
        """Save dataset metadata to DynamoDB."""
        if self.mock_mode:
            return
        
        try:
            item = asdict(dataset)
            item['validation_data_uri'] = validation_uri
            item['created_at'] = dataset.created_at.isoformat()
            
            self.dynamodb_client.put_item(
                table_name="biomerkin_training_datasets",
                item=item
            )
        except Exception as e:
            self.logger.warning(f"Error saving dataset metadata: {str(e)}")
    
    async def _save_job_metadata(self, job: FineTuningJob):
        """Save job metadata to DynamoDB."""
        if self.mock_mode:
            return
        
        try:
            item = asdict(job)
            item['created_at'] = job.created_at.isoformat()
            if job.started_at:
                item['started_at'] = job.started_at.isoformat()
            if job.completed_at:
                item['completed_at'] = job.completed_at.isoformat()
            
            self.dynamodb_client.put_item(
                table_name="biomerkin_fine_tuning_jobs",
                item=item
            )
        except Exception as e:
            self.logger.warning(f"Error saving job metadata: {str(e)}")
    
    async def _save_evaluation_results(self, evaluation: ModelEvaluation):
        """Save evaluation results to DynamoDB."""
        if self.mock_mode:
            return
        
        try:
            item = asdict(evaluation)
            item['created_at'] = evaluation.created_at.isoformat()
            
            self.dynamodb_client.put_item(
                table_name="biomerkin_model_evaluations",
                item=item
            )
        except Exception as e:
            self.logger.warning(f"Error saving evaluation results: {str(e)}")
    
    async def _save_deployment_info(self, deployment_info: Dict[str, Any]):
        """Save deployment information."""
        if self.mock_mode:
            return
        
        try:
            self.dynamodb_client.put_item(
                table_name="biomerkin_model_deployments",
                item=deployment_info
            )
        except Exception as e:
            self.logger.warning(f"Error saving deployment info: {str(e)}")
    
    async def _load_test_dataset(self, test_dataset_uri: str) -> List[Dict[str, Any]]:
        """Load test dataset from S3."""
        if self.mock_mode:
            return [
                {'input': 'Test input 1', 'output': 'Expected output 1'},
                {'input': 'Test input 2', 'output': 'Expected output 2'}
            ]
        
        # Implementation would load actual data from S3
        return []
    
    def _get_fine_tuning_role_arn(self) -> str:
        """Get IAM role ARN for fine-tuning."""
        return f"arn:aws:iam::{self._get_account_id()}:role/BiomerkinFineTuningRole"
    
    def _get_account_id(self) -> str:
        """Get AWS account ID."""
        return boto3.client('sts').get_caller_identity()['Account']
    
    def _generate_cost_recommendations(self, usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""
        recommendations = []
        
        # Cache optimization
        if usage_analysis['cache_hit_rate'] < 0.5:
            recommendations.append({
                'type': 'caching',
                'description': 'Implement intelligent caching for repeated queries',
                'potential_savings_percent': 25,
                'implementation_effort': 'medium'
            })
        
        # Model size optimization
        if usage_analysis['average_tokens_per_request'] < 500:
            recommendations.append({
                'type': 'model_size',
                'description': 'Use smaller, more efficient model for simple queries',
                'potential_savings_percent': 40,
                'implementation_effort': 'low'
            })
        
        # Batch processing
        recommendations.append({
            'type': 'batch_processing',
            'description': 'Implement batch processing for similar requests',
            'potential_savings_percent': 20,
            'implementation_effort': 'medium'
        })
        
        # Fine-tuning optimization
        if usage_analysis['error_rate'] > 0.05:
            recommendations.append({
                'type': 'fine_tuning',
                'description': 'Fine-tune models for domain-specific accuracy',
                'potential_savings_percent': 15,
                'implementation_effort': 'high'
            })
        
        return recommendations
    
    def _calculate_potential_savings(self, usage_analysis: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate potential cost savings from recommendations."""
        total_savings_percent = sum(rec['potential_savings_percent'] for rec in recommendations)
        current_monthly_cost = usage_analysis['monthly_projection_usd']
        
        return {
            'total_savings_percent': min(total_savings_percent, 60),  # Cap at 60%
            'monthly_savings_usd': current_monthly_cost * (total_savings_percent / 100),
            'annual_savings_usd': current_monthly_cost * 12 * (total_savings_percent / 100)
        }
    
    async def _ensure_training_bucket_exists(self):
        """Ensure the training data S3 bucket exists."""
        if self.mock_mode:
            return
            
        try:
            self.s3_client.head_bucket(Bucket=self.training_bucket)
        except:
            # Create bucket if it doesn't exist
            self.s3_client.create_bucket(
                Bucket=self.training_bucket,
                CreateBucketConfiguration={
                    'LocationConstraint': self.config.aws.region
                } if self.config.aws.region != 'us-east-1' else {}
            )
            
            # Set bucket policy for training access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                        "Action": ["s3:GetObject", "s3:ListBucket"],
                        "Resource": [
                            f"arn:aws:s3:::{self.training_bucket}",
                            f"arn:aws:s3:::{self.training_bucket}/*"
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=self.training_bucket,
                Policy=json.dumps(bucket_policy)
            )
    
    async def create_bioinformatics_training_data(self) -> Dict[str, str]:
        """
        Create comprehensive training datasets for bioinformatics fine-tuning.
        
        Returns:
            Dictionary mapping dataset types to their IDs
        """
        try:
            self.logger.info("Creating bioinformatics training datasets")
            
            dataset_ids = {}
            
            # Genomics analysis training data
            genomics_data = self._generate_genomics_training_data()
            genomics_dataset = TrainingDataset(
                dataset_id="genomics_analysis_comprehensive",
                name="Comprehensive Genomics Analysis Dataset",
                description="Training data for genomics sequence analysis, variant interpretation, and clinical significance",
                model_type=ModelType.GENOMICS_ANALYSIS,
                s3_uri="",  # Will be set during creation
                sample_count=len(genomics_data)
            )
            
            genomics_id = await self.create_training_dataset(genomics_dataset, genomics_data)
            dataset_ids['genomics'] = genomics_id
            
            # Medical reasoning training data
            medical_data = self._generate_medical_reasoning_data()
            medical_dataset = TrainingDataset(
                dataset_id="medical_reasoning_comprehensive",
                name="Medical Reasoning and Decision Making Dataset",
                description="Training data for clinical reasoning, diagnosis, and treatment recommendations",
                model_type=ModelType.MEDICAL_REASONING,
                s3_uri="",
                sample_count=len(medical_data)
            )
            
            medical_id = await self.create_training_dataset(medical_dataset, medical_data)
            dataset_ids['medical'] = medical_id
            
            # Literature summarization training data
            literature_data = self._generate_literature_training_data()
            literature_dataset = TrainingDataset(
                dataset_id="literature_summarization_comprehensive",
                name="Scientific Literature Summarization Dataset",
                description="Training data for summarizing scientific papers and extracting key findings",
                model_type=ModelType.LITERATURE_SUMMARIZATION,
                s3_uri="",
                sample_count=len(literature_data)
            )
            
            literature_id = await self.create_training_dataset(literature_dataset, literature_data)
            dataset_ids['literature'] = literature_id
            
            self.logger.info(f"Created {len(dataset_ids)} training datasets")
            return dataset_ids
            
        except Exception as e:
            self.logger.error(f"Error creating bioinformatics training data: {str(e)}")
            raise
    
    def _generate_genomics_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for genomics analysis."""
        return [
            {
                'input': 'Analyze this DNA sequence for potential pathogenic variants: ATGCGATCGATCGTAGCTAGC...',
                'output': 'This DNA sequence analysis reveals several key findings:\n\n1. Gene Identification: The sequence contains portions of the BRCA1 gene\n2. Variant Detection: A missense variant c.5266dupC (p.Gln1756Profs) was identified\n3. Clinical Significance: This variant is classified as pathogenic according to ACMG guidelines\n4. Functional Impact: The frameshift mutation leads to premature protein truncation\n5. Clinical Recommendations: Genetic counseling and enhanced screening protocols are recommended'
            },
            {
                'input': 'What is the clinical significance of the TP53 variant c.524G>A (p.Arg175His)?',
                'output': 'The TP53 variant c.524G>A (p.Arg175His) has the following clinical significance:\n\n1. Classification: Pathogenic (Class 5)\n2. Functional Impact: This missense variant affects the DNA-binding domain of p53\n3. Cancer Risk: Associated with Li-Fraumeni syndrome and increased cancer susceptibility\n4. Inheritance: Autosomal dominant pattern\n5. Clinical Management: Enhanced surveillance including MRI screening and genetic counseling for family members\n6. Penetrance: High penetrance with >90% lifetime cancer risk'
            },
            {
                'input': 'Interpret the genomic findings for a patient with multiple variants in cancer susceptibility genes.',
                'output': 'Comprehensive genomic interpretation requires systematic analysis:\n\n1. Variant Classification: Each variant must be classified using ACMG/AMP guidelines\n2. Gene Function Assessment: Evaluate the biological role of affected genes\n3. Clinical Correlation: Consider patient phenotype and family history\n4. Risk Assessment: Calculate cumulative cancer risks\n5. Management Recommendations: Develop personalized screening and prevention strategies\n6. Family Implications: Assess cascade testing needs for relatives\n7. Therapeutic Implications: Consider targeted therapy options based on molecular findings'
            }
        ]
    
    def _generate_medical_reasoning_data(self) -> List[Dict[str, Any]]:
        """Generate training data for medical reasoning."""
        return [
            {
                'input': 'A 45-year-old woman presents with a family history of breast and ovarian cancer. Her genetic test shows a BRCA1 pathogenic variant. What are the clinical recommendations?',
                'output': 'For a 45-year-old woman with a BRCA1 pathogenic variant, evidence-based recommendations include:\n\n1. Breast Cancer Screening:\n   - Annual breast MRI starting at age 25-30\n   - Annual mammography starting at age 30\n   - Clinical breast exams every 6 months\n\n2. Risk-Reducing Options:\n   - Consider prophylactic mastectomy (reduces risk by 90-95%)\n   - Discuss timing based on personal preferences and family planning\n\n3. Ovarian Cancer Management:\n   - Risk-reducing salpingo-oophorectomy by age 35-40\n   - Consider completion of childbearing before surgery\n\n4. Additional Considerations:\n   - Genetic counseling for family members\n   - Discuss reproductive options if planning pregnancy\n   - Consider chemoprevention options\n   - Psychological support and counseling'
            },
            {
                'input': 'How should treatment decisions be made for a patient with multiple genetic variants of uncertain significance?',
                'output': 'Managing patients with variants of uncertain significance (VUS) requires careful clinical reasoning:\n\n1. Risk Assessment:\n   - VUS should not be used for clinical decision-making\n   - Focus on established risk factors and family history\n   - Consider population-based screening guidelines\n\n2. Clinical Management:\n   - Follow standard screening protocols for the general population\n   - Consider enhanced screening only if strong family history warrants it\n   - Avoid unnecessary interventions based on VUS alone\n\n3. Ongoing Monitoring:\n   - Periodic reclassification of variants as new evidence emerges\n   - Stay updated with variant databases and literature\n   - Consider functional studies if clinically relevant\n\n4. Patient Communication:\n   - Clearly explain the uncertainty associated with VUS\n   - Discuss the possibility of reclassification\n   - Provide appropriate genetic counseling\n   - Document discussions thoroughly'
            }
        ]
    
    def _generate_literature_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for literature summarization."""
        return [
            {
                'input': 'Summarize the key findings from recent research on CRISPR gene editing for treating genetic diseases.',
                'output': 'Recent CRISPR research for genetic diseases shows significant progress:\n\n**Key Advances:**\n1. Base Editing: Improved precision with reduced off-target effects\n2. Prime Editing: Enhanced accuracy for small insertions and deletions\n3. In Vivo Applications: Successful trials in liver, eye, and muscle tissues\n\n**Clinical Applications:**\n- Sickle Cell Disease: CTX001 therapy showing promising results\n- Beta-Thalassemia: Sustained hemoglobin production in clinical trials\n- Leber Congenital Amaurosis: Direct retinal injection trials ongoing\n\n**Safety Considerations:**\n- Improved delivery methods reducing immunogenicity\n- Better off-target detection and mitigation strategies\n- Long-term monitoring protocols established\n\n**Future Directions:**\n- Expansion to more complex genetic disorders\n- Development of tissue-specific delivery systems\n- Integration with other therapeutic modalities'
            },
            {
                'input': 'What does current literature say about the effectiveness of liquid biopsies for cancer detection?',
                'output': 'Current literature demonstrates significant potential for liquid biopsies:\n\n**Detection Capabilities:**\n- Circulating tumor DNA (ctDNA) detection sensitivity: 70-90% for advanced cancers\n- Early-stage detection improving with enhanced sequencing technologies\n- Multi-cancer detection panels showing promise in screening studies\n\n**Clinical Applications:**\n- Treatment Monitoring: Real-time assessment of therapy response\n- Resistance Detection: Early identification of acquired mutations\n- Minimal Residual Disease: Post-treatment monitoring for recurrence\n\n**Advantages Over Tissue Biopsy:**\n- Non-invasive sampling\n- Ability to capture tumor heterogeneity\n- Serial monitoring capability\n- Access to difficult-to-biopsy locations\n\n**Current Limitations:**\n- Lower sensitivity for early-stage cancers\n- Standardization challenges across platforms\n- Cost considerations for routine screening\n\n**Regulatory Status:**\n- FDA-approved tests for specific indications\n- Ongoing validation studies for screening applications'
            }
        ]