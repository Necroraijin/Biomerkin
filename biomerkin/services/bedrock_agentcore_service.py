"""
Amazon Bedrock AgentCore Integration Service.
Provides advanced agent orchestration and reasoning capabilities.
"""

import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.logging_config import get_logger
from ..models.base import WorkflowState


class BedrockAgentCoreService:
    """
    Service for integrating with Amazon Bedrock AgentCore.
    Provides advanced agent orchestration and reasoning.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize Bedrock AgentCore service."""
        self.logger = get_logger(__name__)
        self.region = region
        
        try:
            self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
            self.logger.info("Bedrock AgentCore service initialized")
        except Exception as e:
            self.logger.error(f"Error initializing Bedrock AgentCore: {e}")
            self.bedrock_agent = None
            self.bedrock_runtime = None
    
    def create_agent(self, agent_name: str, description: str) -> Optional[str]:
        """
        Create a new Bedrock agent.
        
        Args:
            agent_name: Name of the agent
            description: Description of the agent
            
        Returns:
            Agent ID if successful, None otherwise
        """
        if not self.bedrock_agent:
            return None
        
        try:
            response = self.bedrock_agent.create_agent(
                agentName=agent_name,
                description=description,
                foundationModel="anthropic.claude-3-sonnet-20240229-v1:0",
                instruction="You are a specialized bioinformatics AI agent. Provide accurate, evidence-based analysis while maintaining medical safety standards."
            )
            
            agent_id = response['agent']['agentId']
            self.logger.info(f"Created Bedrock agent: {agent_id}")
            return agent_id
            
        except Exception as e:
            self.logger.error(f"Error creating Bedrock agent: {e}")
            return None
    
    def create_agent_alias(self, agent_id: str, alias_name: str) -> Optional[str]:
        """
        Create an alias for the agent.
        
        Args:
            agent_id: ID of the agent
            alias_name: Name for the alias
            
        Returns:
            Alias ID if successful, None otherwise
        """
        if not self.bedrock_agent:
            return None
        
        try:
            response = self.bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description=f"Alias for {alias_name}"
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            self.logger.info(f"Created agent alias: {alias_id}")
            return alias_id
            
        except Exception as e:
            self.logger.error(f"Error creating agent alias: {e}")
            return None
    
    def invoke_agent(self, agent_id: str, alias_id: str, session_id: str, 
                    input_text: str, session_state: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Invoke a Bedrock agent.
        
        Args:
            agent_id: ID of the agent
            alias_id: ID of the agent alias
            session_id: Session identifier
            input_text: Input text for the agent
            session_state: Optional session state
            
        Returns:
            Agent response
        """
        if not self.bedrock_runtime:
            return {"error": "Bedrock runtime not available"}
        
        try:
            request_body = {
                "inputText": input_text,
                "sessionId": session_id
            }
            
            if session_state:
                request_body["sessionState"] = session_state
            
            response = self.bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=session_id,
                inputText=input_text,
                sessionState=session_state or {}
            )
            
            # Read the response stream
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            return {
                "response": response_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error invoking Bedrock agent: {e}")
            return {"error": str(e)}
    
    def orchestrate_multi_agent_workflow(self, workflow_state: WorkflowState) -> Dict[str, Any]:
        """
        Use Bedrock AgentCore to orchestrate multi-agent workflow.
        
        Args:
            workflow_state: Current workflow state
            
        Returns:
            Orchestration results
        """
        if not self.bedrock_runtime:
            return {"error": "Bedrock runtime not available"}
        
        # Create orchestration prompt
        orchestration_prompt = f"""
        You are orchestrating a multi-agent bioinformatics workflow. Current state:
        
        Workflow ID: {workflow_state.workflow_id}
        Status: {workflow_state.status}
        Current Agent: {workflow_state.current_agent}
        Progress: {workflow_state.progress_percentage}%
        
        Available Agents:
        1. GenomicsAgent - DNA sequence analysis
        2. ProteomicsAgent - Protein structure analysis
        3. LiteratureAgent - Scientific literature research
        4. DrugAgent - Drug discovery and clinical trials
        5. DecisionAgent - Medical report generation
        
        Input Data: {json.dumps(workflow_state.input_data, indent=2)}
        Results So Far: {json.dumps(workflow_state.results, indent=2)}
        Errors: {workflow_state.errors}
        
        Decide:
        1. Which agent should run next (or if workflow is complete)
        2. What parameters to pass to the next agent
        3. How to handle any errors
        4. Priority of different analyses
        5. When to stop the workflow
        
        Respond with a JSON object containing your decisions.
        """
        
        try:
            # Use Claude for orchestration reasoning
            response = self._invoke_claude_for_reasoning(orchestration_prompt)
            return self._parse_orchestration_response(response)
            
        except Exception as e:
            self.logger.error(f"Error in multi-agent orchestration: {e}")
            return {"error": str(e)}
    
    def _invoke_claude_for_reasoning(self, prompt: str) -> str:
        """Invoke Claude for reasoning tasks."""
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
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body.get('content', [{}])[0].get('text', '')
            
        except Exception as e:
            self.logger.error(f"Error invoking Claude for reasoning: {e}")
            raise
    
    def _parse_orchestration_response(self, response: str) -> Dict[str, Any]:
        """Parse orchestration response from Claude."""
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
                # Fallback response
                return {
                    "next_agent": "decision",
                    "reasoning": response,
                    "parameters": {},
                    "workflow_complete": True
                }
        except json.JSONDecodeError:
            return {
                "next_agent": "decision",
                "reasoning": response,
                "parameters": {},
                "workflow_complete": True,
                "parse_error": "Could not parse orchestration response"
            }
    
    def create_knowledge_base(self, knowledge_base_name: str, 
                            data_source_config: Dict[str, Any]) -> Optional[str]:
        """
        Create a knowledge base for the agent.
        
        Args:
            knowledge_base_name: Name of the knowledge base
            data_source_config: Configuration for data sources
            
        Returns:
            Knowledge base ID if successful, None otherwise
        """
        if not self.bedrock_agent:
            return None
        
        try:
            response = self.bedrock_agent.create_knowledge_base(
                name=knowledge_base_name,
                description=f"Knowledge base for {knowledge_base_name}",
                roleArn="arn:aws:iam::account:role/BedrockKnowledgeBaseRole",  # Update with actual role
                knowledgeBaseConfiguration={
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
                    }
                },
                storageConfiguration={
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": "arn:aws:aoss:us-east-1:account:collection/collection-name",  # Update with actual collection
                        "vectorIndexName": "biomerkin-index",
                        "fieldMapping": {
                            "vectorField": "vector",
                            "textField": "text",
                            "metadataField": "metadata"
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            self.logger.info(f"Created knowledge base: {kb_id}")
            return kb_id
            
        except Exception as e:
            self.logger.error(f"Error creating knowledge base: {e}")
            return None


# Global service instance
bedrock_agentcore_service = BedrockAgentCoreService()

