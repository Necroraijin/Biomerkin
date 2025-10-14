"""
AI Reasoning Agent using Amazon Bedrock AgentCore.
Provides advanced reasoning capabilities for all other agents.
"""

import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.logging_config import get_logger
from ..models.base import WorkflowState


class AIReasoningAgent:
    """
    Advanced AI reasoning agent using Amazon Bedrock AgentCore.
    Provides reasoning capabilities for complex decision-making.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize AI reasoning agent."""
        self.logger = get_logger(__name__)
        self.region = region
        
        # Initialize Bedrock AgentCore client
        try:
            self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
            self.logger.info("Bedrock AgentCore client initialized")
        except Exception as e:
            self.logger.error(f"Error initializing Bedrock AgentCore: {e}")
            self.bedrock_agent = None
            self.bedrock_runtime = None
    
    def reason_about_genomic_data(self, genomic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI reasoning to analyze genomic data and provide insights.
        
        Args:
            genomic_data: Genomic analysis results
            
        Returns:
            AI reasoning insights
        """
        if not self.bedrock_runtime:
            return {"error": "Bedrock not available"}
        
        # Create reasoning prompt
        prompt = f"""
        You are a medical AI expert analyzing genomic data. Please provide reasoning about:
        
        Genomic Data:
        {json.dumps(genomic_data, indent=2)}
        
        Please analyze and provide:
        1. Clinical significance of findings
        2. Potential disease associations
        3. Risk assessment
        4. Recommended next steps
        5. Confidence level in analysis
        
        Format your response as structured JSON.
        """
        
        try:
            response = self._invoke_bedrock_model(prompt)
            return self._parse_reasoning_response(response)
        except Exception as e:
            self.logger.error(f"Error in genomic reasoning: {e}")
            return {"error": str(e)}
    
    def reason_about_protein_function(self, protein_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI reasoning to analyze protein function and structure.
        
        Args:
            protein_data: Protein analysis results
            
        Returns:
            AI reasoning insights
        """
        if not self.bedrock_runtime:
            return {"error": "Bedrock not available"}
        
        prompt = f"""
        You are a protein biology expert. Analyze this protein data:
        
        Protein Data:
        {json.dumps(protein_data, indent=2)}
        
        Provide reasoning about:
        1. Functional implications
        2. Structural significance
        3. Interaction networks
        4. Disease relevance
        5. Therapeutic potential
        
        Format as structured JSON.
        """
        
        try:
            response = self._invoke_bedrock_model(prompt)
            return self._parse_reasoning_response(response)
        except Exception as e:
            self.logger.error(f"Error in protein reasoning: {e}")
            return {"error": str(e)}
    
    def reason_about_drug_candidates(self, drug_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI reasoning to evaluate drug candidates.
        
        Args:
            drug_data: Drug analysis results
            
        Returns:
            AI reasoning insights
        """
        if not self.bedrock_runtime:
            return {"error": "Bedrock not available"}
        
        prompt = f"""
        You are a pharmaceutical expert. Evaluate these drug candidates:
        
        Drug Data:
        {json.dumps(drug_data, indent=2)}
        
        Provide reasoning about:
        1. Efficacy potential
        2. Safety profile
        3. Market viability
        4. Development timeline
        5. Competitive landscape
        
        Format as structured JSON.
        """
        
        try:
            response = self._invoke_bedrock_model(prompt)
            return self._parse_reasoning_response(response)
        except Exception as e:
            self.logger.error(f"Error in drug reasoning: {e}")
            return {"error": str(e)}
    
    def orchestrate_agent_decisions(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """
        Use AI reasoning to orchestrate decisions between agents.
        
        Args:
            workflow_state: Current workflow state
            
        Returns:
            Orchestration decisions
        """
        if not self.bedrock_runtime:
            return {"error": "Bedrock not available"}
        
        prompt = f"""
        You are orchestrating a multi-agent bioinformatics workflow. Current state:
        
        Workflow State:
        {json.dumps(workflow_state.to_dict(), indent=2)}
        
        Decide:
        1. Which agent should run next
        2. What parameters to use
        3. How to handle any errors
        4. When to stop the workflow
        5. Priority of different analyses
        
        Format as structured JSON with clear decisions.
        """
        
        try:
            response = self._invoke_bedrock_model(prompt)
            return self._parse_reasoning_response(response)
        except Exception as e:
            self.logger.error(f"Error in orchestration reasoning: {e}")
            return {"error": str(e)}
    
    def _invoke_bedrock_model(self, prompt: str, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0") -> str:
        """Invoke Bedrock model with reasoning prompt."""
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,  # Low temperature for consistent reasoning
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body.get('content', [{}])[0].get('text', '')
            
        except Exception as e:
            self.logger.error(f"Error invoking Bedrock model: {e}")
            raise
    
    def _parse_reasoning_response(self, response: str) -> Dict[str, Any]:
        """Parse AI reasoning response into structured format."""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            elif "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback to text response
                return {
                    "reasoning": response,
                    "timestamp": datetime.now().isoformat(),
                    "format": "text"
                }
        except json.JSONDecodeError:
            return {
                "reasoning": response,
                "timestamp": datetime.now().isoformat(),
                "format": "text",
                "parse_error": "Could not parse as JSON"
            }

