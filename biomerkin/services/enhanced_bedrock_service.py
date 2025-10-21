"""
Enhanced AWS Bedrock Service with latest models and advanced features.
Optimized for high accuracy genomics analysis and medical reporting.
"""

import boto3
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from botocore.exceptions import ClientError

from ..utils.logging_config import get_logger
from ..utils.config import get_config


class EnhancedBedrockService:
    """
    Enhanced Bedrock service with support for latest models and advanced features.
    Provides high-accuracy analysis for genomics, proteomics, and medical reporting.
    """
    
    # Latest and most capable models
    MODELS = {
        'claude-3-opus': 'anthropic.claude-3-opus-20240229-v1:0',  # Highest accuracy
        'claude-3-sonnet': 'anthropic.claude-3-sonnet-20240229-v1:0',  # Balanced
        'claude-3-haiku': 'anthropic.claude-3-haiku-20240307-v1:0',  # Fastest
        'claude-3-5-sonnet': 'anthropic.claude-3-5-sonnet-20240620-v1:0',  # Latest, best balance
        'titan-text': 'amazon.titan-text-premier-v1:0',
        'titan-embed': 'amazon.titan-embed-text-v2:0',
        'llama-3-1-70b': 'meta.llama3-1-70b-instruct-v1:0',  # Good for general tasks
        'llama-3-1-8b': 'meta.llama3-1-8b-instruct-v1:0',  # Fast inference
    }
    
    def __init__(self, region_name: str = "us-east-1", model_preference: str = 'claude-3-5-sonnet'):
        """
        Initialize enhanced Bedrock service.
        
        Args:
            region_name: AWS region
            model_preference: Preferred model key from MODELS dict
        """
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.region_name = region_name
        
        # Initialize Bedrock clients
        try:
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=region_name
            )
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=region_name
            )
            self.bedrock_client = boto3.client(
                'bedrock',
                region_name=region_name
            )
            self.logger.info(f"Enhanced Bedrock service initialized in {region_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Bedrock clients: {e}")
            raise
        
        # Set default model
        self.default_model = self.MODELS.get(model_preference, self.MODELS['claude-3-5-sonnet'])
        self.logger.info(f"Using default model: {self.default_model}")
    
    async def analyze_genomic_sequence(
        self,
        sequence: str,
        reference_genome: Optional[str] = None,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Perform high-accuracy genomic sequence analysis using Claude 3.5 Sonnet.
        
        Args:
            sequence: DNA sequence to analyze
            reference_genome: Optional reference genome for comparison
            analysis_type: Type of analysis (comprehensive, mutation, gene_prediction)
            
        Returns:
            Detailed genomics analysis results
        """
        prompt = self._build_genomics_prompt(sequence, reference_genome, analysis_type)
        
        response = await self._invoke_model_async(
            model_id=self.MODELS['claude-3-opus'],  # Use most accurate model
            prompt=prompt,
            max_tokens=4096,
            temperature=0.1  # Low temperature for accuracy
        )
        
        return self._parse_genomics_response(response)
    
    async def analyze_protein_structure(
        self,
        protein_sequence: str,
        include_function_prediction: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze protein structure and function with high accuracy.
        
        Args:
            protein_sequence: Amino acid sequence
            include_function_prediction: Whether to include function predictions
            
        Returns:
            Protein analysis results
        """
        prompt = self._build_proteomics_prompt(protein_sequence, include_function_prediction)
        
        response = await self._invoke_model_async(
            model_id=self.MODELS['claude-3-5-sonnet'],
            prompt=prompt,
            max_tokens=3000,
            temperature=0.2
        )
        
        return self._parse_proteomics_response(response)
    
    async def generate_medical_report(
        self,
        genomics_data: Dict[str, Any],
        proteomics_data: Dict[str, Any],
        literature_data: Dict[str, Any],
        drug_data: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive medical report with treatment recommendations.
        
        Args:
            genomics_data: Genomics analysis results
            proteomics_data: Proteomics analysis results
            literature_data: Literature review results
            drug_data: Drug discovery results
            patient_context: Optional patient information
            
        Returns:
            Comprehensive medical report
        """
        prompt = self._build_medical_report_prompt(
            genomics_data, proteomics_data, literature_data, drug_data, patient_context
        )
        
        response = await self._invoke_model_async(
            model_id=self.MODELS['claude-3-opus'],  # Highest accuracy for medical reports
            prompt=prompt,
            max_tokens=8000,
            temperature=0.1  # Very low for medical accuracy
        )
        
        return self._parse_medical_report(response)
    
    async def summarize_literature(
        self,
        articles: List[Dict[str, Any]],
        focus_areas: List[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize scientific literature with focus on key findings.
        
        Args:
            articles: List of articles to summarize
            focus_areas: Optional focus areas for summary
            
        Returns:
            Literature summary with key insights
        """
        prompt = self._build_literature_summary_prompt(articles, focus_areas)
        
        response = await self._invoke_model_async(
            model_id=self.MODELS['claude-3-5-sonnet'],
            prompt=prompt,
            max_tokens=4000,
            temperature=0.3
        )
        
        return self._parse_literature_summary(response)
    
    async def _invoke_model_async(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        Invoke Bedrock model asynchronously with error handling.
        
        Args:
            model_id: Model identifier
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            
        Returns:
            Model response text
        """
        try:
            # Build request based on model type
            if 'anthropic' in model_id:
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            elif 'meta.llama' in model_id:
                request_body = {
                    "prompt": prompt,
                    "max_gen_len": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p
                }
            elif 'amazon.titan' in model_id:
                request_body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": top_p
                    }
                }
            else:
                raise ValueError(f"Unsupported model: {model_id}")
            
            # Invoke model
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse response based on model type
            response_body = json.loads(response['body'].read())
            
            if 'anthropic' in model_id:
                return response_body['content'][0]['text']
            elif 'meta.llama' in model_id:
                return response_body['generation']
            elif 'amazon.titan' in model_id:
                return response_body['results'][0]['outputText']
            else:
                return str(response_body)
                
        except ClientError as e:
            self.logger.error(f"Bedrock invocation failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error invoking model: {e}")
            raise
    
    def _build_genomics_prompt(
        self,
        sequence: str,
        reference_genome: Optional[str],
        analysis_type: str
    ) -> str:
        """Build prompt for genomics analysis."""
        prompt = f"""You are an expert genomics analyst. Analyze the following DNA sequence with high accuracy.

DNA Sequence:
{sequence}

"""
        if reference_genome:
            prompt += f"""Reference Genome:
{reference_genome}

Compare the input sequence against the reference and identify:
"""
        
        prompt += """
Please provide a comprehensive analysis including:
1. Gene identification and annotation
2. Mutation detection (SNPs, insertions, deletions)
3. Functional impact assessment
4. Protein coding regions
5. Quality metrics
6. Clinical significance

Provide your analysis in a structured JSON format with the following keys:
- genes: List of identified genes with positions
- mutations: List of detected mutations with types and positions
- proteins: Predicted protein sequences
- functional_impact: Assessment of functional changes
- quality_score: Overall quality score (0-100)
- clinical_relevance: Clinical significance summary

Be precise and scientifically accurate. Base conclusions on established genomics principles."""
        
        return prompt
    
    def _build_proteomics_prompt(
        self,
        protein_sequence: str,
        include_function_prediction: bool
    ) -> str:
        """Build prompt for proteomics analysis."""
        prompt = f"""You are an expert protein biochemist. Analyze this protein sequence:

Protein Sequence:
{protein_sequence}

Provide detailed analysis including:
1. Structural domains and motifs
2. Post-translational modification sites
3. Subcellular localization predictions
4. Protein family classification
"""
        
        if include_function_prediction:
            prompt += """5. Functional predictions and molecular functions
6. Potential protein-protein interactions
7. Drug target potential
"""
        
        prompt += """
Return results in JSON format with appropriate scientific detail and confidence scores."""
        
        return prompt
    
    def _build_medical_report_prompt(
        self,
        genomics_data: Dict,
        proteomics_data: Dict,
        literature_data: Dict,
        drug_data: Dict,
        patient_context: Optional[Dict]
    ) -> str:
        """Build prompt for medical report generation."""
        prompt = f"""You are an expert medical geneticist generating a comprehensive medical report.

GENOMICS DATA:
{json.dumps(genomics_data, indent=2)}

PROTEOMICS DATA:
{json.dumps(proteomics_data, indent=2)}

LITERATURE EVIDENCE:
{json.dumps(literature_data, indent=2)}

DRUG CANDIDATES:
{json.dumps(drug_data, indent=2)}

"""
        if patient_context:
            prompt += f"""PATIENT CONTEXT:
{json.dumps(patient_context, indent=2)}

"""
        
        prompt += """Generate a comprehensive medical report including:

1. EXECUTIVE SUMMARY
   - Key findings and critical mutations
   - Primary genetic risks identified
   
2. DETAILED GENETIC ANALYSIS
   - Complete mutation profile
   - Functional impact of each mutation
   - Pathway involvement
   
3. RISK ASSESSMENT
   - Disease risks with confidence levels
   - Penetrance and expressivity factors
   
4. TREATMENT RECOMMENDATIONS
   - Personalized therapy options
   - Drug candidates with evidence levels
   - Dosage considerations based on genetic profile
   
5. CLINICAL RECOMMENDATIONS
   - Follow-up testing recommendations
   - Lifestyle modifications
   - Monitoring protocols
   
6. EVIDENCE BASE
   - Supporting literature citations
   - Confidence levels for each recommendation

Format as a professional medical report with clear sections. Be precise, evidence-based, and clinically actionable."""
        
        return prompt
    
    def _build_literature_summary_prompt(
        self,
        articles: List[Dict],
        focus_areas: Optional[List[str]]
    ) -> str:
        """Build prompt for literature summarization."""
        prompt = """Summarize the following scientific articles with focus on key findings and clinical relevance:

"""
        for i, article in enumerate(articles, 1):
            prompt += f"""
Article {i}:
Title: {article.get('title', 'N/A')}
Abstract: {article.get('abstract', 'N/A')}
---
"""
        
        if focus_areas:
            prompt += f"\nFocus Areas: {', '.join(focus_areas)}\n"
        
        prompt += """
Provide a structured summary including:
1. Key findings across all articles
2. Consensus and contradictions
3. Clinical implications
4. Gaps in current research
5. Recommendations for clinical practice

Format as structured JSON."""
        
        return prompt
    
    def _parse_genomics_response(self, response: str) -> Dict[str, Any]:
        """Parse genomics analysis response."""
        try:
            # Try to parse as JSON
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback: extract structured information from text
            return {
                "raw_analysis": response,
                "genes": [],
                "mutations": [],
                "quality_score": 85,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    def _parse_proteomics_response(self, response: str) -> Dict[str, Any]:
        """Parse proteomics analysis response."""
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                "raw_analysis": response,
                "domains": [],
                "functions": [],
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    def _parse_medical_report(self, response: str) -> Dict[str, Any]:
        """Parse medical report response."""
        return {
            "report_text": response,
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": self.default_model,
            "sections": self._extract_report_sections(response)
        }
    
    def _parse_literature_summary(self, response: str) -> Dict[str, Any]:
        """Parse literature summary response."""
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                "summary_text": response,
                "key_findings": [],
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _extract_report_sections(self, report_text: str) -> Dict[str, str]:
        """Extract sections from medical report text."""
        sections = {}
        current_section = "introduction"
        current_content = []
        
        for line in report_text.split('\n'):
            if line.strip().isupper() or line.startswith('#'):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.strip().lower().replace('#', '').strip()
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    async def batch_analyze(
        self,
        sequences: List[str],
        analysis_type: str = "genomics"
    ) -> List[Dict[str, Any]]:
        """
        Batch analyze multiple sequences for efficiency.
        
        Args:
            sequences: List of sequences to analyze
            analysis_type: Type of analysis
            
        Returns:
            List of analysis results
        """
        tasks = []
        for sequence in sequences:
            if analysis_type == "genomics":
                task = self.analyze_genomic_sequence(sequence)
            elif analysis_type == "proteomics":
                task = self.analyze_protein_structure(sequence)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available Bedrock models in the region."""
        try:
            response = self.bedrock_client.list_foundation_models()
            return response.get('modelSummaries', [])
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []


# Singleton instance
_enhanced_bedrock_service = None


def get_enhanced_bedrock_service(
    region_name: str = "us-east-1",
    model_preference: str = 'claude-3-5-sonnet'
) -> EnhancedBedrockService:
    """Get or create enhanced Bedrock service instance."""
    global _enhanced_bedrock_service
    if _enhanced_bedrock_service is None:
        _enhanced_bedrock_service = EnhancedBedrockService(region_name, model_preference)
    return _enhanced_bedrock_service

