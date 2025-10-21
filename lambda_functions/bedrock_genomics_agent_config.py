"""
Bedrock Agent Configuration for Autonomous GenomicsAgent.
This module contains the configuration and setup for the GenomicsAgent Bedrock Agent
with enhanced autonomous capabilities and LLM reasoning.
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class GenomicsBedrockAgentConfig:
    """Configuration class for GenomicsAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the configuration."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        
    def get_agent_instruction(self) -> str:
        """
        Get the comprehensive instruction for the autonomous GenomicsAgent.
        
        This instruction defines the agent's autonomous capabilities, reasoning approach,
        and integration with external APIs for genomics analysis.
        """
        return """
        You are an autonomous AI agent specialized in genomics analysis and clinical interpretation.
        
        ## Core Capabilities
        
        You are an expert genomics analyst with the following autonomous capabilities:
        
        1. **DNA Sequence Analysis**: Autonomously analyze DNA sequences to identify genes, variants, and mutations
        2. **Clinical Interpretation**: Apply ACMG/AMP guidelines with reasoning to classify variant significance
        3. **Autonomous Decision Making**: Make clinical decisions based on genomics evidence and patient context
        4. **LLM Reasoning**: Use advanced reasoning to integrate multiple data sources and provide insights
        5. **External API Integration**: Seamlessly integrate with Biopython, PDB, and clinical databases
        
        ## Autonomous Reasoning Framework
        
        When analyzing genomics data, you should:
        
        1. **Initial Assessment**: Evaluate sequence quality, length, and characteristics
        2. **Gene Identification**: Use Biopython integration to identify genes with confidence scoring
        3. **Variant Analysis**: Detect and classify variants using ACMG guidelines with reasoning
        4. **Clinical Significance**: Assess clinical significance with evidence-based reasoning
        5. **Treatment Implications**: Autonomously determine therapeutic relevance and actionability
        6. **Risk Assessment**: Perform comprehensive risk assessment with patient context integration
        7. **Recommendations**: Generate autonomous recommendations for clinical action
        
        ## Decision-Making Process
        
        For each analysis, you should:
        
        - **Reason Step-by-Step**: Provide clear reasoning for each decision
        - **Cite Evidence**: Reference specific evidence sources and databases
        - **Assess Confidence**: Provide confidence scores for your assessments
        - **Consider Context**: Integrate patient context, family history, and clinical presentation
        - **Prioritize Findings**: Autonomously prioritize findings by clinical significance
        - **Recommend Actions**: Suggest specific clinical actions and follow-up steps
        
        ## Integration Capabilities
        
        You can autonomously:
        
        - **Execute Biopython Analysis**: Parse sequences, identify genes, translate proteins
        - **Apply Clinical Guidelines**: Use ACMG/AMP criteria with reasoning
        - **Query Databases**: Access population genetics and clinical significance databases
        - **Generate Reports**: Create comprehensive medical-style reports with reasoning
        - **Make Treatment Recommendations**: Suggest targeted therapies and interventions
        
        ## Clinical Reasoning Standards
        
        Always follow these standards:
        
        1. **Evidence-Based**: Base all decisions on scientific evidence and clinical guidelines
        2. **Transparent Reasoning**: Explain your reasoning process clearly
        3. **Risk-Benefit Analysis**: Consider risks and benefits of recommendations
        4. **Patient-Centered**: Focus on patient benefit and clinical actionability
        5. **Uncertainty Acknowledgment**: Clearly state limitations and uncertainties
        6. **Continuous Learning**: Adapt recommendations based on new evidence
        
        ## Output Format
        
        Provide structured outputs with:
        
        - **Executive Summary**: Key findings and recommendations
        - **Detailed Analysis**: Step-by-step reasoning and evidence
        - **Clinical Significance**: ACMG classification with rationale
        - **Autonomous Insights**: AI-generated insights and patterns
        - **Action Items**: Specific recommendations for clinical team
        - **Follow-up Plan**: Monitoring and re-evaluation recommendations
        
        ## Autonomous Capabilities Demonstration
        
        For the AWS hackathon, specifically demonstrate:
        
        1. **Autonomous AI Agent**: Independent decision-making without human intervention
        2. **LLM Reasoning**: Advanced reasoning capabilities with step-by-step logic
        3. **External API Integration**: Seamless integration with bioinformatics tools
        4. **Multi-Agent Coordination**: Coordination with other specialized agents
        5. **Clinical Decision Making**: Real-world clinical decision support
        
        Remember: You are an autonomous agent capable of independent analysis and decision-making.
        Always provide reasoning for your decisions and demonstrate your autonomous capabilities.
        """
    
    def get_genomics_api_schema(self) -> Dict[str, Any]:
        """
        Get the comprehensive API schema for genomics analysis functions.
        
        This schema defines all the autonomous genomics analysis capabilities
        available to the Bedrock Agent.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Autonomous Genomics Analysis API",
                "version": "2.0.0",
                "description": "Comprehensive API for autonomous genomics analysis with LLM reasoning"
            },
            "paths": {
                "/analyze-sequence": {
                    "post": {
                        "summary": "Comprehensive autonomous DNA sequence analysis",
                        "description": "Performs complete genomics analysis including gene identification, variant detection, clinical interpretation, and autonomous reasoning",
                        "operationId": "analyzeSequence",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sequence": {
                                                "type": "string",
                                                "description": "DNA sequence to analyze (FASTA format or raw sequence)"
                                            },
                                            "reference_genome": {
                                                "type": "string",
                                                "description": "Reference genome version (e.g., GRCh38, GRCh37)",
                                                "default": "GRCh38"
                                            },
                                            "patient_context": {
                                                "type": "object",
                                                "description": "Patient clinical context for interpretation",
                                                "properties": {
                                                    "age": {"type": "integer"},
                                                    "gender": {"type": "string"},
                                                    "family_history": {"type": "string"},
                                                    "clinical_presentation": {"type": "string"},
                                                    "ethnicity": {"type": "string"}
                                                }
                                            },
                                            "analysis_parameters": {
                                                "type": "object",
                                                "description": "Analysis parameters and preferences",
                                                "properties": {
                                                    "include_uncertain_variants": {"type": "boolean", "default": True},
                                                    "minimum_confidence": {"type": "number", "default": 0.5},
                                                    "focus_areas": {"type": "array", "items": {"type": "string"}}
                                                }
                                            }
                                        },
                                        "required": ["sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive genomics analysis results with autonomous reasoning",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "analysis_type": {"type": "string"},
                                                "genes": {"type": "array"},
                                                "variants": {"type": "array"},
                                                "protein_sequences": {"type": "array"},
                                                "autonomous_reasoning": {"type": "object"},
                                                "clinical_decisions": {"type": "object"},
                                                "autonomous_next_steps": {"type": "object"},
                                                "llm_insights": {"type": "object"},
                                                "clinical_significance": {"type": "object"},
                                                "risk_assessment": {"type": "object"},
                                                "treatment_implications": {"type": "object"},
                                                "confidence_scores": {"type": "object"},
                                                "autonomous_capabilities": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/interpret-variant": {
                    "post": {
                        "summary": "Autonomous variant interpretation with ACMG guidelines",
                        "description": "Provides comprehensive clinical interpretation of genetic variants using ACMG/AMP guidelines with autonomous reasoning",
                        "operationId": "interpretVariant",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "variant": {
                                                "type": "string",
                                                "description": "Variant in HGVS format (e.g., c.1234G>A, p.Arg123His)"
                                            },
                                            "gene": {
                                                "type": "string",
                                                "description": "Gene symbol (e.g., BRCA1, TP53)"
                                            },
                                            "patient_context": {
                                                "type": "object",
                                                "description": "Patient clinical context",
                                                "properties": {
                                                    "family_history": {"type": "string"},
                                                    "clinical_presentation": {"type": "string"},
                                                    "age": {"type": "integer"},
                                                    "ethnicity": {"type": "string"}
                                                }
                                            },
                                            "additional_evidence": {
                                                "type": "object",
                                                "description": "Additional evidence for interpretation",
                                                "properties": {
                                                    "functional_studies": {"type": "array"},
                                                    "segregation_data": {"type": "string"},
                                                    "population_data": {"type": "object"}
                                                }
                                            }
                                        },
                                        "required": ["variant", "gene"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive variant interpretation with autonomous reasoning",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "variant": {"type": "string"},
                                                "gene": {"type": "string"},
                                                "classification": {"type": "string"},
                                                "clinical_significance": {"type": "string"},
                                                "evidence_summary": {"type": "array"},
                                                "acmg_criteria": {"type": "array"},
                                                "confidence_level": {"type": "number"},
                                                "autonomous_reasoning": {"type": "object"},
                                                "recommendations": {"type": "array"},
                                                "follow_up_actions": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/identify-genes": {
                    "post": {
                        "summary": "Autonomous gene identification and functional annotation",
                        "description": "Identifies genes in DNA sequences with autonomous functional annotation and clinical relevance assessment",
                        "operationId": "identifyGenes",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sequence": {
                                                "type": "string",
                                                "description": "DNA sequence for gene identification"
                                            },
                                            "analysis_context": {
                                                "type": "object",
                                                "description": "Context for gene analysis",
                                                "properties": {
                                                    "organism": {"type": "string", "default": "human"},
                                                    "tissue_type": {"type": "string"},
                                                    "disease_context": {"type": "string"}
                                                }
                                            },
                                            "annotation_level": {
                                                "type": "string",
                                                "enum": ["basic", "comprehensive", "clinical"],
                                                "default": "comprehensive"
                                            }
                                        },
                                        "required": ["sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Gene identification results with autonomous annotations",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "genes_identified": {"type": "integer"},
                                                "genes": {"type": "array"},
                                                "autonomous_analysis": {"type": "object"},
                                                "clinical_prioritization": {"type": "object"},
                                                "functional_predictions": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "autonomous_recommendations": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/detect-mutations": {
                    "post": {
                        "summary": "Autonomous mutation detection and clinical interpretation",
                        "description": "Detects mutations by sequence comparison with autonomous clinical interpretation and therapeutic assessment",
                        "operationId": "detectMutations",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sequence": {
                                                "type": "string",
                                                "description": "Query DNA sequence"
                                            },
                                            "reference_sequence": {
                                                "type": "string",
                                                "description": "Reference sequence for comparison"
                                            },
                                            "patient_context": {
                                                "type": "object",
                                                "description": "Patient clinical context for interpretation"
                                            },
                                            "analysis_parameters": {
                                                "type": "object",
                                                "description": "Mutation detection parameters",
                                                "properties": {
                                                    "sensitivity_level": {"type": "string", "enum": ["high", "medium", "low"]},
                                                    "include_synonymous": {"type": "boolean", "default": False},
                                                    "minimum_frequency": {"type": "number", "default": 0.01}
                                                }
                                            }
                                        },
                                        "required": ["sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Mutation detection results with autonomous clinical interpretation",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "mutations_detected": {"type": "integer"},
                                                "mutations": {"type": "array"},
                                                "autonomous_analysis": {"type": "object"},
                                                "clinical_interpretation": {"type": "object"},
                                                "therapeutic_implications": {"type": "object"},
                                                "population_analysis": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "autonomous_recommendations": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def get_agent_configuration(self, lambda_arn: str, role_arn: str) -> Dict[str, Any]:
        """
        Get the complete Bedrock Agent configuration for GenomicsAgent.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            role_arn: ARN of the IAM role for the agent
            
        Returns:
            Complete agent configuration dictionary
        """
        return {
            'agentName': 'BiomerkinAutonomousGenomicsAgent',
            'description': 'Autonomous AI agent for comprehensive genomics analysis with LLM reasoning and clinical decision-making capabilities',
            'foundationModel': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'instruction': self.get_agent_instruction(),
            'idleSessionTTLInSeconds': 1800,  # 30 minutes
            'agentResourceRoleArn': role_arn,
            'tags': {
                'Project': 'Biomerkin',
                'Component': 'GenomicsAgent',
                'Version': '2.0',
                'Hackathon': 'AWS-Agent-Hackathon',
                'Capabilities': 'Autonomous-LLM-Reasoning'
            }
        }
    
    def get_action_group_configuration(self, lambda_arn: str) -> Dict[str, Any]:
        """
        Get the action group configuration for genomics functions.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            
        Returns:
            Action group configuration dictionary
        """
        return {
            'actionGroupName': 'AutonomousGenomicsAnalysis',
            'description': 'Comprehensive autonomous genomics analysis functions with LLM reasoning',
            'actionGroupExecutor': {
                'lambda': lambda_arn
            },
            'apiSchema': {
                'payload': json.dumps(self.get_genomics_api_schema())
            }
        }
    
    def create_agent_with_action_group(self, lambda_arn: str, role_arn: str) -> Dict[str, str]:
        """
        Create the complete Bedrock Agent with action group for GenomicsAgent.
        
        Args:
            lambda_arn: ARN of the Lambda function
            role_arn: ARN of the IAM role
            
        Returns:
            Dictionary containing agent_id and action_group_id
        """
        try:
            # Create the agent
            agent_config = self.get_agent_configuration(lambda_arn, role_arn)
            agent_response = self.bedrock_client.create_agent(**agent_config)
            agent_id = agent_response['agent']['agentId']
            
            logger.info(f"Created Bedrock Agent for GenomicsAgent: {agent_id}")
            
            # Wait for agent to be ready
            self._wait_for_agent_ready(agent_id)
            
            # Create action group
            action_group_config = self.get_action_group_configuration(lambda_arn)
            action_group_response = self.bedrock_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                **action_group_config
            )
            action_group_id = action_group_response['agentActionGroup']['actionGroupId']
            
            logger.info(f"Created action group for GenomicsAgent: {action_group_id}")
            
            # Prepare the agent
            self.bedrock_client.prepare_agent(agentId=agent_id)
            logger.info(f"Prepared GenomicsAgent for use: {agent_id}")
            
            return {
                'agent_id': agent_id,
                'action_group_id': action_group_id
            }
            
        except Exception as e:
            logger.error(f"Error creating GenomicsAgent Bedrock Agent: {str(e)}")
            raise
    
    def _wait_for_agent_ready(self, agent_id: str, max_wait_time: int = 300):
        """Wait for agent to be in a ready state."""
        import time
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                response = self.bedrock_client.get_agent(agentId=agent_id)
                agent_status = response['agent']['agentStatus']
                
                if agent_status in ['PREPARED', 'FAILED', 'VERSIONED']:
                    logger.info(f"GenomicsAgent {agent_id} is ready with status: {agent_status}")
                    return
                elif agent_status in ['CREATING', 'PREPARING', 'UPDATING']:
                    logger.info(f"GenomicsAgent {agent_id} status: {agent_status}, waiting...")
                    time.sleep(10)
                else:
                    logger.warning(f"Unknown agent status: {agent_status}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Error checking agent status: {str(e)}")
                time.sleep(10)
        
        raise TimeoutError(f"GenomicsAgent {agent_id} did not become ready within {max_wait_time} seconds")


def create_genomics_bedrock_agent(lambda_arn: str, role_arn: str, region: str = 'us-east-1') -> Dict[str, str]:
    """
    Convenience function to create a GenomicsAgent Bedrock Agent.
    
    Args:
        lambda_arn: ARN of the Lambda function for action group execution
        role_arn: ARN of the IAM role for the agent
        region: AWS region for deployment
        
    Returns:
        Dictionary containing agent_id and action_group_id
    """
    config = GenomicsBedrockAgentConfig(region=region)
    return config.create_agent_with_action_group(lambda_arn, role_arn)


# Example usage and testing functions
def test_genomics_agent_configuration():
    """Test the GenomicsAgent configuration."""
    config = GenomicsBedrockAgentConfig()
    
    # Test instruction generation
    instruction = config.get_agent_instruction()
    assert len(instruction) > 1000, "Instruction should be comprehensive"
    assert "autonomous" in instruction.lower(), "Should emphasize autonomous capabilities"
    
    # Test API schema
    schema = config.get_genomics_api_schema()
    assert "paths" in schema, "Schema should have API paths"
    assert len(schema["paths"]) >= 4, "Should have at least 4 API endpoints"
    
    # Test agent configuration
    agent_config = config.get_agent_configuration("test-lambda-arn", "test-role-arn")
    assert agent_config["agentName"] == "BiomerkinAutonomousGenomicsAgent"
    assert "autonomous" in agent_config["description"].lower()
    
    print("✅ GenomicsAgent configuration tests passed!")


if __name__ == "__main__":
    test_genomics_agent_configuration()

def lambda_handler(event, context):
    """
    Lambda handler for Bedrock Agent configuration.
    This function returns the agent configuration for deployment.
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Bedrock Agent configuration',
            'config': get_agent_config()
        })
    }
