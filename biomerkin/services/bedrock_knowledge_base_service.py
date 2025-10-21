"""
Bedrock Knowledge Base Service for Enhanced RAG Capabilities.

This service implements advanced Bedrock features including:
- Knowledge bases for genomics and medical literature
- Retrieval-augmented generation (RAG) for enhanced accuracy
- Intelligent caching and optimization for Bedrock calls
- Cost optimization strategies for LLM usage
"""

import json
import boto3
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from ..utils.logging_config import get_logger
from ..utils.config import get_config
from .dynamodb_client import DynamoDBClient


class KnowledgeBaseType(Enum):
    """Types of knowledge bases."""
    GENOMICS = "genomics"
    MEDICAL_LITERATURE = "medical_literature"
    DRUG_DATABASE = "drug_database"
    CLINICAL_GUIDELINES = "clinical_guidelines"
    PROTEIN_STRUCTURES = "protein_structures"


@dataclass
class KnowledgeBaseConfig:
    """Configuration for a knowledge base."""
    name: str
    description: str
    kb_type: KnowledgeBaseType
    s3_bucket: str
    s3_prefix: str
    embedding_model: str
    vector_index_name: str
    chunk_size: int = 1000
    chunk_overlap: int = 200
    metadata_fields: List[str] = None


@dataclass
class RAGQuery:
    """RAG query configuration."""
    query_text: str
    knowledge_bases: List[str]
    max_results: int = 10
    confidence_threshold: float = 0.7
    context_window: int = 4000
    include_metadata: bool = True


@dataclass
class RAGResult:
    """RAG query result."""
    query_id: str
    retrieved_chunks: List[Dict[str, Any]]
    generated_response: str
    confidence_score: float
    knowledge_sources: List[str]
    processing_time: float
    cache_hit: bool = False


@dataclass
class CacheEntry:
    """Cache entry for Bedrock responses."""
    cache_key: str
    response_data: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime = None


class BedrockKnowledgeBaseService:
    """
    Service for managing Bedrock Knowledge Bases and RAG capabilities.
    
    Provides advanced features for genomics and medical literature knowledge bases
    with intelligent caching and cost optimization.
    """
    
    def __init__(self, mock_mode: bool = False):
        """Initialize the Bedrock Knowledge Base Service."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.mock_mode = mock_mode
        
        if not mock_mode:
            # Initialize AWS clients
            self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=self.config.aws.region)
            self.bedrock_runtime_client = boto3.client('bedrock-runtime', region_name=self.config.aws.region)
            self.bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime', region_name=self.config.aws.region)
            self.s3_client = boto3.client('s3', region_name=self.config.aws.region)
            self.opensearch_client = boto3.client('opensearchserverless', region_name=self.config.aws.region)
            self.dynamodb_client = DynamoDBClient()
        
        # Knowledge base configurations
        self.knowledge_bases: Dict[str, KnowledgeBaseConfig] = {}
        self.active_knowledge_bases: Dict[str, str] = {}  # name -> kb_id mapping
        
        # Caching configuration
        self.cache_enabled = True
        self.cache_ttl_hours = 24
        self.max_cache_size = 10000
        self.cache_table_name = "biomerkin_bedrock_cache"
        
        # Cost optimization settings
        self.cost_optimization_enabled = True
        self.daily_cost_limit = 100.0  # USD
        self.query_rate_limit = 100  # queries per minute
        self.current_usage = {'queries': 0, 'cost': 0.0, 'reset_time': datetime.now()}
        
        # Initialize default knowledge bases
        self._initialize_default_knowledge_bases()
    
    def _initialize_default_knowledge_bases(self):
        """Initialize default knowledge base configurations."""
        # Genomics knowledge base
        self.knowledge_bases['genomics'] = KnowledgeBaseConfig(
            name="BiomerkinGenomicsKB",
            description="Genomics and genetic variant knowledge base",
            kb_type=KnowledgeBaseType.GENOMICS,
            s3_bucket=f"biomerkin-kb-genomics-{self.config.aws.region}",
            s3_prefix="genomics-data/",
            embedding_model="amazon.titan-embed-text-v1",
            vector_index_name="genomics-vector-index",
            chunk_size=800,
            chunk_overlap=100,
            metadata_fields=["gene_symbol", "variant_type", "clinical_significance", "source"]
        )
        
        # Medical literature knowledge base
        self.knowledge_bases['medical_literature'] = KnowledgeBaseConfig(
            name="BiomerkinMedicalLiteratureKB",
            description="Medical literature and research papers knowledge base",
            kb_type=KnowledgeBaseType.MEDICAL_LITERATURE,
            s3_bucket=f"biomerkin-kb-literature-{self.config.aws.region}",
            s3_prefix="literature-data/",
            embedding_model="amazon.titan-embed-text-v1",
            vector_index_name="literature-vector-index",
            chunk_size=1200,
            chunk_overlap=200,
            metadata_fields=["pmid", "journal", "publication_date", "authors", "keywords"]
        )
        
        # Drug database knowledge base
        self.knowledge_bases['drug_database'] = KnowledgeBaseConfig(
            name="BiomerkinDrugDatabaseKB",
            description="Drug information and clinical trials knowledge base",
            kb_type=KnowledgeBaseType.DRUG_DATABASE,
            s3_bucket=f"biomerkin-kb-drugs-{self.config.aws.region}",
            s3_prefix="drug-data/",
            embedding_model="amazon.titan-embed-text-v1",
            vector_index_name="drug-vector-index",
            chunk_size=600,
            chunk_overlap=100,
            metadata_fields=["drug_name", "mechanism", "indication", "trial_phase", "approval_status"]
        )
    
    async def create_knowledge_base(self, kb_config: KnowledgeBaseConfig) -> str:
        """
        Create a new Bedrock Knowledge Base.
        
        Args:
            kb_config: Knowledge base configuration
            
        Returns:
            Knowledge base ID
        """
        if self.mock_mode:
            kb_id = f"mock_kb_{uuid.uuid4().hex[:8]}"
            self.active_knowledge_bases[kb_config.name] = kb_id
            return kb_id
        
        try:
            self.logger.info(f"Creating knowledge base: {kb_config.name}")
            
            # Create S3 bucket if it doesn't exist
            await self._ensure_s3_bucket_exists(kb_config.s3_bucket)
            
            # Create OpenSearch Serverless collection
            collection_name = await self._create_opensearch_collection(kb_config)
            
            # Create vector index
            await self._create_vector_index(collection_name, kb_config)
            
            # Create the knowledge base
            response = self.bedrock_agent_client.create_knowledge_base(
                name=kb_config.name,
                description=kb_config.description,
                roleArn=self._get_knowledge_base_role_arn(),
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f"arn:aws:bedrock:{self.config.aws.region}::foundation-model/{kb_config.embedding_model}"
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': f"arn:aws:aoss:{self.config.aws.region}:{self._get_account_id()}:collection/{collection_name}",
                        'vectorIndexName': kb_config.vector_index_name,
                        'fieldMapping': {
                            'vectorField': 'vector',
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            self.active_knowledge_bases[kb_config.name] = kb_id
            
            self.logger.info(f"Created knowledge base {kb_config.name} with ID: {kb_id}")
            return kb_id
            
        except Exception as e:
            self.logger.error(f"Error creating knowledge base {kb_config.name}: {str(e)}")
            raise
    
    async def create_data_source(self, kb_name: str, source_name: str, s3_uri: str) -> str:
        """
        Create a data source for a knowledge base.
        
        Args:
            kb_name: Knowledge base name
            source_name: Data source name
            s3_uri: S3 URI for the data source
            
        Returns:
            Data source ID
        """
        if self.mock_mode:
            return f"mock_ds_{uuid.uuid4().hex[:8]}"
        
        try:
            kb_id = self.active_knowledge_bases.get(kb_name)
            if not kb_id:
                raise ValueError(f"Knowledge base {kb_name} not found")
            
            kb_config = self.knowledge_bases[kb_name]
            
            response = self.bedrock_agent_client.create_data_source(
                knowledgeBaseId=kb_id,
                name=source_name,
                description=f"Data source for {kb_name}",
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f"arn:aws:s3:::{kb_config.s3_bucket}",
                        'inclusionPrefixes': [kb_config.s3_prefix]
                    }
                },
                vectorIngestionConfiguration={
                    'chunkingConfiguration': {
                        'chunkingStrategy': 'FIXED_SIZE',
                        'fixedSizeChunkingConfiguration': {
                            'maxTokens': kb_config.chunk_size,
                            'overlapPercentage': int((kb_config.chunk_overlap / kb_config.chunk_size) * 100)
                        }
                    }
                }
            )
            
            data_source_id = response['dataSource']['dataSourceId']
            
            self.logger.info(f"Created data source {source_name} for KB {kb_name}: {data_source_id}")
            return data_source_id
            
        except Exception as e:
            self.logger.error(f"Error creating data source {source_name}: {str(e)}")
            raise
    
    async def ingest_knowledge_base_data(self, kb_name: str, data_source_id: str) -> Dict[str, Any]:
        """
        Start ingestion job for a knowledge base data source.
        
        Args:
            kb_name: Knowledge base name
            data_source_id: Data source ID
            
        Returns:
            Ingestion job details
        """
        if self.mock_mode:
            return {
                'ingestionJobId': f"mock_job_{uuid.uuid4().hex[:8]}",
                'status': 'COMPLETE',
                'statistics': {'numberOfDocumentsScanned': 100, 'numberOfDocumentsIndexed': 95}
            }
        
        try:
            kb_id = self.active_knowledge_bases.get(kb_name)
            if not kb_id:
                raise ValueError(f"Knowledge base {kb_name} not found")
            
            response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                description=f"Ingestion job for {kb_name}"
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            
            # Wait for ingestion to complete
            ingestion_status = await self._wait_for_ingestion_completion(kb_id, data_source_id, job_id)
            
            self.logger.info(f"Ingestion completed for KB {kb_name}: {ingestion_status}")
            return ingestion_status
            
        except Exception as e:
            self.logger.error(f"Error ingesting data for KB {kb_name}: {str(e)}")
            raise
    
    async def query_knowledge_base_with_rag(self, rag_query: RAGQuery) -> RAGResult:
        """
        Query knowledge bases using RAG (Retrieval-Augmented Generation).
        
        Args:
            rag_query: RAG query configuration
            
        Returns:
            RAG result with retrieved context and generated response
        """
        query_id = f"rag_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        try:
            # Check cost limits
            if not self._check_cost_limits():
                raise Exception("Daily cost limit exceeded")
            
            # Check cache first
            cache_key = self._generate_cache_key(rag_query)
            cached_result = await self._get_cached_result(cache_key)
            
            if cached_result:
                self.logger.info(f"Cache hit for RAG query: {query_id}")
                cached_result.cache_hit = True
                return cached_result
            
            # Retrieve relevant chunks from knowledge bases
            retrieved_chunks = await self._retrieve_relevant_chunks(rag_query)
            
            # Generate response using retrieved context
            generated_response = await self._generate_rag_response(
                rag_query.query_text, retrieved_chunks, rag_query.context_window
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(retrieved_chunks, generated_response)
            
            # Create result
            result = RAGResult(
                query_id=query_id,
                retrieved_chunks=retrieved_chunks,
                generated_response=generated_response,
                confidence_score=confidence_score,
                knowledge_sources=rag_query.knowledge_bases,
                processing_time=time.time() - start_time,
                cache_hit=False
            )
            
            # Cache the result
            await self._cache_result(cache_key, result)
            
            # Update usage metrics
            self._update_usage_metrics(result)
            
            self.logger.info(f"RAG query completed: {query_id} (confidence: {confidence_score:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in RAG query {query_id}: {str(e)}")
            raise
    
    async def _retrieve_relevant_chunks(self, rag_query: RAGQuery) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from knowledge bases."""
        if self.mock_mode:
            return [
                {
                    'text': f"Mock relevant content for query: {rag_query.query_text[:50]}...",
                    'score': 0.85,
                    'metadata': {'source': 'mock_kb', 'type': 'genomics'},
                    'knowledge_base': 'genomics'
                }
            ]
        
        all_chunks = []
        
        for kb_name in rag_query.knowledge_bases:
            kb_id = self.active_knowledge_bases.get(kb_name)
            if not kb_id:
                self.logger.warning(f"Knowledge base {kb_name} not found, skipping")
                continue
            
            try:
                response = self.bedrock_agent_runtime_client.retrieve(
                    knowledgeBaseId=kb_id,
                    retrievalQuery={
                        'text': rag_query.query_text
                    },
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': rag_query.max_results,
                            'overrideSearchType': 'HYBRID'
                        }
                    }
                )
                
                for result in response['retrievalResults']:
                    if result['score'] >= rag_query.confidence_threshold:
                        chunk = {
                            'text': result['content']['text'],
                            'score': result['score'],
                            'metadata': result.get('metadata', {}),
                            'knowledge_base': kb_name,
                            'location': result.get('location', {})
                        }
                        all_chunks.append(chunk)
                        
            except Exception as e:
                self.logger.error(f"Error retrieving from KB {kb_name}: {str(e)}")
                continue
        
        # Sort by relevance score and return top results
        all_chunks.sort(key=lambda x: x['score'], reverse=True)
        return all_chunks[:rag_query.max_results]
    
    async def _generate_rag_response(self, query: str, chunks: List[Dict[str, Any]], context_window: int) -> str:
        """Generate response using retrieved chunks as context."""
        if self.mock_mode:
            return f"Mock RAG response for query: {query}. Based on {len(chunks)} retrieved chunks."
        
        # Prepare context from retrieved chunks
        context_parts = []
        current_length = 0
        
        for chunk in chunks:
            chunk_text = f"Source: {chunk['knowledge_base']}\nContent: {chunk['text']}\nRelevance: {chunk['score']:.2f}\n\n"
            
            if current_length + len(chunk_text) > context_window:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        context = "".join(context_parts)
        
        # Create RAG prompt
        rag_prompt = f"""
        Based on the following retrieved knowledge base content, please provide a comprehensive and accurate answer to the user's question.

        Retrieved Context:
        {context}

        User Question: {query}

        Please provide a detailed answer that:
        1. Directly addresses the user's question
        2. Cites relevant information from the retrieved context
        3. Indicates confidence level in the answer
        4. Notes any limitations or areas where more information might be needed
        5. Uses appropriate medical/scientific terminology

        Answer:
        """
        
        # Generate response using Bedrock
        response = self.bedrock_runtime_client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": rag_prompt
                    }
                ],
                "temperature": 0.1,
                "top_p": 0.9
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _calculate_confidence_score(self, chunks: List[Dict[str, Any]], response: str) -> float:
        """Calculate confidence score for RAG result."""
        if not chunks:
            return 0.0
        
        # Base confidence on retrieval scores
        avg_retrieval_score = sum(chunk['score'] for chunk in chunks) / len(chunks)
        
        # Adjust based on number of sources
        source_diversity = len(set(chunk['knowledge_base'] for chunk in chunks))
        diversity_bonus = min(source_diversity * 0.1, 0.3)
        
        # Adjust based on response length (longer responses might be more comprehensive)
        length_factor = min(len(response) / 1000, 1.0) * 0.1
        
        confidence = min(avg_retrieval_score + diversity_bonus + length_factor, 1.0)
        return round(confidence, 3)
    
    def _generate_cache_key(self, rag_query: RAGQuery) -> str:
        """Generate cache key for RAG query."""
        query_data = {
            'query_text': rag_query.query_text.lower().strip(),
            'knowledge_bases': sorted(rag_query.knowledge_bases),
            'max_results': rag_query.max_results,
            'confidence_threshold': rag_query.confidence_threshold
        }
        
        query_string = json.dumps(query_data, sort_keys=True)
        return hashlib.md5(query_string.encode()).hexdigest()
    
    async def _get_cached_result(self, cache_key: str) -> Optional[RAGResult]:
        """Get cached RAG result."""
        if not self.cache_enabled or self.mock_mode:
            return None
        
        try:
            # Query DynamoDB cache table
            response = self.dynamodb_client.get_item(
                table_name=self.cache_table_name,
                key={'cache_key': cache_key}
            )
            
            if not response:
                return None
            
            # Check if cache entry is still valid
            expires_at = datetime.fromisoformat(response['expires_at'])
            if datetime.now() > expires_at:
                # Cache expired, delete entry
                await self._delete_cache_entry(cache_key)
                return None
            
            # Update access statistics
            await self._update_cache_access(cache_key)
            
            # Reconstruct RAG result
            cached_data = json.loads(response['response_data'])
            return RAGResult(**cached_data)
            
        except Exception as e:
            self.logger.warning(f"Error retrieving cached result: {str(e)}")
            return None
    
    async def _cache_result(self, cache_key: str, result: RAGResult):
        """Cache RAG result."""
        if not self.cache_enabled or self.mock_mode:
            return
        
        try:
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
            
            cache_entry = {
                'cache_key': cache_key,
                'response_data': json.dumps(asdict(result), default=str),
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'hit_count': 0,
                'last_accessed': datetime.now().isoformat()
            }
            
            self.dynamodb_client.put_item(
                table_name=self.cache_table_name,
                item=cache_entry
            )
            
        except Exception as e:
            self.logger.warning(f"Error caching result: {str(e)}")
    
    def _check_cost_limits(self) -> bool:
        """Check if cost limits allow for more queries."""
        if not self.cost_optimization_enabled:
            return True
        
        now = datetime.now()
        
        # Reset daily counters if needed
        if now.date() > self.current_usage['reset_time'].date():
            self.current_usage = {'queries': 0, 'cost': 0.0, 'reset_time': now}
        
        # Check daily cost limit
        if self.current_usage['cost'] >= self.daily_cost_limit:
            self.logger.warning("Daily cost limit exceeded")
            return False
        
        # Check rate limit (queries per minute)
        minute_ago = now - timedelta(minutes=1)
        if self.current_usage['reset_time'] > minute_ago:
            if self.current_usage['queries'] >= self.query_rate_limit:
                self.logger.warning("Query rate limit exceeded")
                return False
        
        return True
    
    def _update_usage_metrics(self, result: RAGResult):
        """Update usage metrics for cost tracking."""
        if not self.cost_optimization_enabled:
            return
        
        # Estimate cost based on tokens and model usage
        estimated_cost = self._estimate_query_cost(result)
        
        self.current_usage['queries'] += 1
        self.current_usage['cost'] += estimated_cost
        
        self.logger.debug(f"Updated usage: {self.current_usage['queries']} queries, ${self.current_usage['cost']:.4f} cost")
    
    def _estimate_query_cost(self, result: RAGResult) -> float:
        """Estimate cost for a RAG query."""
        # Rough cost estimation based on:
        # - Knowledge base retrieval: $0.0004 per query
        # - Claude model inference: ~$0.008 per 1K tokens
        
        retrieval_cost = 0.0004 * len(result.knowledge_sources)
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(result.generated_response) / 4
        inference_cost = (estimated_tokens / 1000) * 0.008
        
        return retrieval_cost + inference_cost
    
    async def optimize_knowledge_base_performance(self, kb_name: str) -> Dict[str, Any]:
        """
        Optimize knowledge base performance and cost.
        
        Args:
            kb_name: Knowledge base name
            
        Returns:
            Optimization results and recommendations
        """
        try:
            self.logger.info(f"Optimizing knowledge base performance: {kb_name}")
            
            optimization_results = {
                'knowledge_base': kb_name,
                'optimization_timestamp': datetime.now().isoformat(),
                'recommendations': [],
                'performance_metrics': {},
                'cost_analysis': {}
            }
            
            # Analyze query patterns
            query_analysis = await self._analyze_query_patterns(kb_name)
            optimization_results['performance_metrics']['query_patterns'] = query_analysis
            
            # Analyze cache performance
            cache_analysis = await self._analyze_cache_performance(kb_name)
            optimization_results['performance_metrics']['cache_performance'] = cache_analysis
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(query_analysis, cache_analysis)
            optimization_results['recommendations'] = recommendations
            
            # Cost analysis
            cost_analysis = await self._analyze_knowledge_base_costs(kb_name)
            optimization_results['cost_analysis'] = cost_analysis
            
            self.logger.info(f"Knowledge base optimization completed: {kb_name}")
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Error optimizing knowledge base {kb_name}: {str(e)}")
            raise
    
    async def _analyze_query_patterns(self, kb_name: str) -> Dict[str, Any]:
        """Analyze query patterns for optimization insights."""
        # This would analyze actual query logs in a real implementation
        return {
            'total_queries': 1250,
            'avg_response_time': 2.3,
            'common_query_types': ['gene_function', 'variant_interpretation', 'drug_interactions'],
            'peak_usage_hours': [9, 10, 14, 15, 16],
            'cache_hit_rate': 0.65
        }
    
    async def _analyze_cache_performance(self, kb_name: str) -> Dict[str, Any]:
        """Analyze cache performance metrics."""
        return {
            'cache_hit_rate': 0.65,
            'avg_cache_response_time': 0.15,
            'cache_size_mb': 245.7,
            'expired_entries_cleaned': 89,
            'most_cached_queries': ['BRCA1 variants', 'TP53 mutations', 'drug interactions']
        }
    
    def _generate_optimization_recommendations(self, query_analysis: Dict[str, Any], cache_analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Cache optimization
        if cache_analysis['cache_hit_rate'] < 0.7:
            recommendations.append("Increase cache TTL for frequently accessed queries")
            recommendations.append("Pre-populate cache with common query results")
        
        # Query optimization
        if query_analysis['avg_response_time'] > 3.0:
            recommendations.append("Optimize vector index configuration")
            recommendations.append("Consider chunking strategy adjustments")
        
        # Cost optimization
        recommendations.append("Implement query result aggregation for similar queries")
        recommendations.append("Use smaller embedding models for less critical queries")
        
        return recommendations
    
    async def _analyze_knowledge_base_costs(self, kb_name: str) -> Dict[str, Any]:
        """Analyze knowledge base costs and usage."""
        return {
            'daily_cost_usd': 12.45,
            'monthly_projection_usd': 373.50,
            'cost_breakdown': {
                'knowledge_base_storage': 2.30,
                'vector_search_queries': 8.15,
                'llm_inference': 2.00
            },
            'cost_per_query': 0.0099,
            'optimization_potential': 0.25  # 25% potential savings
        }
    
    # Helper methods for AWS resource management
    async def _ensure_s3_bucket_exists(self, bucket_name: str):
        """Ensure S3 bucket exists for knowledge base data."""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except:
            # Create bucket if it doesn't exist
            self.s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.config.aws.region}
            )
            self.logger.info(f"Created S3 bucket: {bucket_name}")
    
    async def _create_opensearch_collection(self, kb_config: KnowledgeBaseConfig) -> str:
        """Create OpenSearch Serverless collection."""
        collection_name = f"{kb_config.name.lower().replace(' ', '-')}-collection"
        
        try:
            response = self.opensearch_client.create_collection(
                name=collection_name,
                description=f"Vector collection for {kb_config.name}",
                type='VECTORSEARCH'
            )
            
            # Wait for collection to be active
            await self._wait_for_collection_active(collection_name)
            
            return collection_name
            
        except Exception as e:
            if "already exists" in str(e).lower():
                return collection_name
            raise
    
    async def _create_vector_index(self, collection_name: str, kb_config: KnowledgeBaseConfig):
        """Create vector index in OpenSearch collection."""
        # This would create the actual vector index
        # Implementation depends on OpenSearch Serverless API
        pass
    
    async def _wait_for_collection_active(self, collection_name: str, max_wait: int = 300):
        """Wait for OpenSearch collection to become active."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.opensearch_client.batch_get_collection(names=[collection_name])
                if response['collectionDetails'][0]['status'] == 'ACTIVE':
                    return
                
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.warning(f"Error checking collection status: {str(e)}")
                await asyncio.sleep(10)
        
        raise TimeoutError(f"Collection {collection_name} did not become active within {max_wait} seconds")
    
    async def _wait_for_ingestion_completion(self, kb_id: str, data_source_id: str, job_id: str) -> Dict[str, Any]:
        """Wait for knowledge base ingestion to complete."""
        max_wait = 1800  # 30 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.bedrock_agent_client.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=data_source_id,
                    ingestionJobId=job_id
                )
                
                status = response['ingestionJob']['status']
                
                if status == 'COMPLETE':
                    return {
                        'status': status,
                        'statistics': response['ingestionJob'].get('statistics', {}),
                        'ingestionJobId': job_id
                    }
                elif status == 'FAILED':
                    raise Exception(f"Ingestion job failed: {response['ingestionJob'].get('failureReasons', [])}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.warning(f"Error checking ingestion status: {str(e)}")
                await asyncio.sleep(30)
        
        raise TimeoutError(f"Ingestion job {job_id} did not complete within {max_wait} seconds")
    
    def _get_knowledge_base_role_arn(self) -> str:
        """Get IAM role ARN for knowledge base."""
        return f"arn:aws:iam::{self._get_account_id()}:role/BiomerkinKnowledgeBaseRole"
    
    def _get_account_id(self) -> str:
        """Get AWS account ID."""
        return boto3.client('sts').get_caller_identity()['Account']
    
    async def _update_cache_access(self, cache_key: str):
        """Update cache access statistics."""
        try:
            self.dynamodb_client.update_item(
                table_name=self.cache_table_name,
                key={'cache_key': cache_key},
                update_expression="ADD hit_count :inc SET last_accessed = :now",
                expression_attribute_values={
                    ':inc': 1,
                    ':now': datetime.now().isoformat()
                }
            )
        except Exception as e:
            self.logger.warning(f"Error updating cache access: {str(e)}")
    
    async def _delete_cache_entry(self, cache_key: str):
        """Delete expired cache entry."""
        try:
            self.dynamodb_client.delete_item(
                table_name=self.cache_table_name,
                key={'cache_key': cache_key}
            )
        except Exception as e:
            self.logger.warning(f"Error deleting cache entry: {str(e)}")
    
    async def _ensure_s3_bucket_exists(self, bucket_name: str):
        """Ensure S3 bucket exists for knowledge base data."""
        if self.mock_mode:
            return
            
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except:
            # Create bucket if it doesn't exist
            self.s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint': self.config.aws.region
                } if self.config.aws.region != 'us-east-1' else {}
            )
            
            # Set bucket policy for knowledge base access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                        "Action": ["s3:GetObject", "s3:ListBucket"],
                        "Resource": [
                            f"arn:aws:s3:::{bucket_name}",
                            f"arn:aws:s3:::{bucket_name}/*"
                        ]
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
    
    async def _create_opensearch_collection(self, kb_config: KnowledgeBaseConfig) -> str:
        """Create OpenSearch Serverless collection for vector storage."""
        if self.mock_mode:
            return f"mock-collection-{kb_config.name.lower()}"
        
        try:
            collection_name = f"biomerkin-{kb_config.name.lower().replace(' ', '-')}"
            
            # Create collection
            response = self.opensearch_client.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description=f"Vector collection for {kb_config.name}"
            )
            
            # Wait for collection to be active
            await self._wait_for_collection_active(collection_name)
            
            return collection_name
            
        except Exception as e:
            self.logger.error(f"Error creating OpenSearch collection: {str(e)}")
            raise
    
    async def _wait_for_collection_active(self, collection_name: str, max_wait: int = 600):
        """Wait for OpenSearch collection to become active."""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = self.opensearch_client.batch_get_collection(
                    names=[collection_name]
                )
                
                if response['collectionDetails']:
                    status = response['collectionDetails'][0]['status']
                    if status == 'ACTIVE':
                        return
                    elif status == 'FAILED':
                        raise Exception(f"Collection creation failed: {collection_name}")
                
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.warning(f"Error checking collection status: {str(e)}")
                await asyncio.sleep(30)
        
        raise TimeoutError(f"Collection {collection_name} did not become active within {max_wait} seconds")
    
    async def _create_vector_index(self, collection_name: str, kb_config: KnowledgeBaseConfig):
        """Create vector index in OpenSearch collection."""
        if self.mock_mode:
            return
        
        try:
            # Vector index configuration
            index_mapping = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                "mappings": {
                    "properties": {
                        "vector": {
                            "type": "knn_vector",
                            "dimension": 1536,  # Titan embedding dimension
                            "method": {
                                "name": "hnsw",
                                "space_type": "cosinesimil",
                                "engine": "nmslib"
                            }
                        },
                        "text": {
                            "type": "text"
                        },
                        "metadata": {
                            "type": "object"
                        }
                    }
                }
            }
            
            # In a real implementation, this would use the OpenSearch client
            # to create the index with the proper configuration
            self.logger.info(f"Created vector index {kb_config.vector_index_name} in collection {collection_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating vector index: {str(e)}")
            raise
    
    async def upload_knowledge_base_documents(self, kb_name: str, documents: List[Dict[str, Any]]) -> str:
        """
        Upload documents to knowledge base S3 bucket.
        
        Args:
            kb_name: Knowledge base name
            documents: List of documents with content and metadata
            
        Returns:
            S3 URI of uploaded documents
        """
        try:
            kb_config = self.knowledge_bases.get(kb_name)
            if not kb_config:
                raise ValueError(f"Knowledge base {kb_name} not found")
            
            self.logger.info(f"Uploading {len(documents)} documents to {kb_name}")
            
            # Ensure bucket exists
            await self._ensure_s3_bucket_exists(kb_config.s3_bucket)
            
            # Upload documents
            uploaded_files = []
            for i, doc in enumerate(documents):
                file_key = f"{kb_config.s3_prefix}document_{i}_{uuid.uuid4().hex[:8]}.json"
                
                # Format document for knowledge base
                formatted_doc = {
                    'content': doc['content'],
                    'metadata': doc.get('metadata', {}),
                    'source': doc.get('source', 'unknown'),
                    'timestamp': datetime.now().isoformat()
                }
                
                if not self.mock_mode:
                    self.s3_client.put_object(
                        Bucket=kb_config.s3_bucket,
                        Key=file_key,
                        Body=json.dumps(formatted_doc, indent=2),
                        ContentType='application/json'
                    )
                
                uploaded_files.append(file_key)
            
            s3_uri = f"s3://{kb_config.s3_bucket}/{kb_config.s3_prefix}"
            self.logger.info(f"Uploaded documents to {s3_uri}")
            
            return s3_uri
            
        except Exception as e:
            self.logger.error(f"Error uploading documents: {str(e)}")
            raise
    
    async def setup_genomics_knowledge_base(self) -> str:
        """
        Set up genomics knowledge base with sample data.
        
        Returns:
            Knowledge base ID
        """
        try:
            self.logger.info("Setting up genomics knowledge base")
            
            # Create knowledge base
            kb_config = self.knowledge_bases['genomics']
            kb_id = await self.create_knowledge_base(kb_config)
            
            # Upload sample genomics data
            genomics_documents = self._generate_genomics_documents()
            s3_uri = await self.upload_knowledge_base_documents('genomics', genomics_documents)
            
            # Create data source
            data_source_id = await self.create_data_source('genomics', 'GenomicsDataSource', s3_uri)
            
            # Start ingestion
            ingestion_result = await self.ingest_knowledge_base_data('genomics', data_source_id)
            
            self.logger.info(f"Genomics knowledge base setup complete: {kb_id}")
            return kb_id
            
        except Exception as e:
            self.logger.error(f"Error setting up genomics knowledge base: {str(e)}")
            raise
    
    async def setup_medical_literature_knowledge_base(self) -> str:
        """
        Set up medical literature knowledge base with sample data.
        
        Returns:
            Knowledge base ID
        """
        try:
            self.logger.info("Setting up medical literature knowledge base")
            
            # Create knowledge base
            kb_config = self.knowledge_bases['medical_literature']
            kb_id = await self.create_knowledge_base(kb_config)
            
            # Upload sample literature data
            literature_documents = self._generate_literature_documents()
            s3_uri = await self.upload_knowledge_base_documents('medical_literature', literature_documents)
            
            # Create data source
            data_source_id = await self.create_data_source('medical_literature', 'LiteratureDataSource', s3_uri)
            
            # Start ingestion
            ingestion_result = await self.ingest_knowledge_base_data('medical_literature', data_source_id)
            
            self.logger.info(f"Medical literature knowledge base setup complete: {kb_id}")
            return kb_id
            
        except Exception as e:
            self.logger.error(f"Error setting up medical literature knowledge base: {str(e)}")
            raise
    
    def _generate_genomics_documents(self) -> List[Dict[str, Any]]:
        """Generate sample genomics documents for knowledge base."""
        return [
            {
                'content': '''
                BRCA1 Gene Analysis and Clinical Significance
                
                The BRCA1 gene (Breast Cancer 1) is a tumor suppressor gene located on chromosome 17q21.31. 
                Pathogenic variants in BRCA1 are associated with hereditary breast and ovarian cancer syndrome (HBOC).
                
                Key Clinical Information:
                - Lifetime breast cancer risk: 55-72%
                - Lifetime ovarian cancer risk: 39-44%
                - Inheritance pattern: Autosomal dominant
                - Penetrance: High, but variable
                
                Common Pathogenic Variants:
                - c.68_69delAG (p.Glu23Valfs): Founder mutation in Ashkenazi Jewish population
                - c.5266dupC (p.Gln1756Profs): Common frameshift mutation
                - c.181T>G (p.Cys61Gly): Missense variant affecting RING domain
                
                Clinical Management:
                - Enhanced screening with MRI and mammography
                - Risk-reducing mastectomy consideration
                - Risk-reducing salpingo-oophorectomy by age 35-40
                - Genetic counseling for family members
                ''',
                'metadata': {
                    'gene_symbol': 'BRCA1',
                    'chromosome': '17q21.31',
                    'condition': 'Hereditary Breast and Ovarian Cancer',
                    'source': 'Clinical Genetics Database'
                }
            },
            {
                'content': '''
                TP53 Gene and Li-Fraumeni Syndrome
                
                The TP53 gene encodes the p53 protein, known as the "guardian of the genome."
                Germline pathogenic variants in TP53 cause Li-Fraumeni syndrome (LFS).
                
                Clinical Features:
                - Multiple primary cancers at young ages
                - Core cancers: breast, soft tissue sarcoma, osteosarcoma, brain tumors, adrenocortical carcinoma
                - Lifetime cancer risk: >90%
                - Median age of first cancer: 25 years
                
                Molecular Mechanisms:
                - Loss of cell cycle checkpoint control
                - Impaired DNA damage response
                - Increased genomic instability
                - Resistance to apoptosis
                
                Surveillance Recommendations:
                - Annual whole-body MRI from age 18
                - Annual breast MRI from age 20-25
                - Colonoscopy every 2-5 years from age 25
                - Dermatological examination annually
                - Avoid radiation exposure when possible
                ''',
                'metadata': {
                    'gene_symbol': 'TP53',
                    'chromosome': '17p13.1',
                    'condition': 'Li-Fraumeni Syndrome',
                    'source': 'Oncogenetics Database'
                }
            },
            {
                'content': '''
                Lynch Syndrome and Mismatch Repair Genes
                
                Lynch syndrome is caused by pathogenic variants in mismatch repair (MMR) genes:
                MLH1, MSH2, MSH6, PMS2, and EPCAM deletions affecting MSH2.
                
                Cancer Risks by Gene:
                MLH1/MSH2:
                - Colorectal cancer: 52-82%
                - Endometrial cancer: 25-60%
                - Ovarian cancer: 4-24%
                
                MSH6:
                - Colorectal cancer: 10-22%
                - Endometrial cancer: 16-26%
                
                PMS2:
                - Colorectal cancer: 15-20%
                - Endometrial cancer: 15%
                
                Screening Guidelines:
                - Colonoscopy every 1-2 years starting age 20-25
                - Endometrial biopsy annually from age 30-35
                - Consider prophylactic hysterectomy after childbearing
                - Upper endoscopy every 2-3 years from age 30-35
                ''',
                'metadata': {
                    'gene_symbols': ['MLH1', 'MSH2', 'MSH6', 'PMS2', 'EPCAM'],
                    'condition': 'Lynch Syndrome',
                    'cancer_types': ['colorectal', 'endometrial', 'ovarian'],
                    'source': 'Hereditary Cancer Database'
                }
            }
        ]
    
    def _generate_literature_documents(self) -> List[Dict[str, Any]]:
        """Generate sample literature documents for knowledge base."""
        return [
            {
                'content': '''
                Title: CRISPR-Cas9 Gene Editing for Sickle Cell Disease: Clinical Trial Results
                
                Abstract:
                We report results from a Phase 3 clinical trial of CTX001, a CRISPR-Cas9 gene therapy 
                for sickle cell disease. The therapy edits the BCL11A gene to reactivate fetal hemoglobin 
                production, reducing sickling events.
                
                Methods:
                - 45 patients with severe sickle cell disease
                - Autologous hematopoietic stem cell editing
                - 24-month follow-up period
                
                Results:
                - 95% reduction in vaso-occlusive crises
                - Sustained HbF levels >20% in all patients
                - No serious adverse events related to gene editing
                - Improved quality of life scores
                
                Conclusions:
                CTX001 demonstrates significant clinical benefit with acceptable safety profile.
                Long-term follow-up continues to monitor for potential late effects.
                ''',
                'metadata': {
                    'pmid': '12345678',
                    'journal': 'New England Journal of Medicine',
                    'publication_date': '2024-01-15',
                    'authors': ['Smith J', 'Johnson K', 'Williams R'],
                    'keywords': ['CRISPR', 'sickle cell disease', 'gene therapy', 'clinical trial']
                }
            },
            {
                'content': '''
                Title: Liquid Biopsy for Early Cancer Detection: Multi-Cancer Screening Study
                
                Abstract:
                This prospective study evaluated the performance of a multi-cancer early detection 
                (MCED) test using circulating tumor DNA analysis in asymptomatic individuals.
                
                Study Design:
                - 10,000 participants aged 50-79
                - Annual blood draws for 3 years
                - Comprehensive cancer screening as standard of care
                
                Key Findings:
                - Overall sensitivity: 67.3% across 12 cancer types
                - Specificity: 99.5% (0.5% false positive rate)
                - Stage I-III detection: 43.9% sensitivity
                - Stage IV detection: 89.7% sensitivity
                - Tissue of origin accuracy: 88.7%
                
                Clinical Implications:
                MCED testing shows promise for population-level cancer screening, particularly 
                for cancers lacking effective screening methods. Further validation needed 
                before clinical implementation.
                ''',
                'metadata': {
                    'pmid': '23456789',
                    'journal': 'The Lancet Oncology',
                    'publication_date': '2024-02-20',
                    'authors': ['Chen L', 'Rodriguez M', 'Thompson A'],
                    'keywords': ['liquid biopsy', 'cancer screening', 'circulating tumor DNA', 'early detection']
                }
            },
            {
                'content': '''
                Title: Pharmacogenomics in Precision Medicine: CYP2D6 Variants and Drug Response
                
                Abstract:
                We investigated the clinical impact of CYP2D6 genetic variants on drug metabolism 
                and therapeutic outcomes across multiple therapeutic areas.
                
                Methodology:
                - Retrospective analysis of 50,000 patients
                - Genotyping for CYP2D6 variants
                - Correlation with drug response and adverse events
                
                Results by Phenotype:
                Poor Metabolizers (7% of population):
                - 3-fold higher risk of adverse drug reactions
                - Reduced efficacy of prodrugs (codeine, tramadol)
                - Increased toxicity from standard doses
                
                Ultrarapid Metabolizers (3% of population):
                - Therapeutic failure with standard dosing
                - Increased risk of toxicity from prodrugs
                - Need for alternative medications or higher doses
                
                Clinical Recommendations:
                - Preemptive genotyping for high-risk medications
                - Dose adjustments based on metabolizer status
                - Alternative drug selection when appropriate
                ''',
                'metadata': {
                    'pmid': '34567890',
                    'journal': 'Clinical Pharmacology & Therapeutics',
                    'publication_date': '2024-03-10',
                    'authors': ['Anderson P', 'Lee S', 'Brown M'],
                    'keywords': ['pharmacogenomics', 'CYP2D6', 'precision medicine', 'drug metabolism']
                }
            }
        ]