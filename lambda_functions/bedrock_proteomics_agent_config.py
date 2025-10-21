"""
Bedrock Agent Configuration for Autonomous ProteomicsAgent.
This module contains the configuration and setup for the ProteomicsAgent Bedrock Agent
with enhanced autonomous capabilities and LLM reasoning.
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ProteomicsBedrockAgentConfig:
    """Configuration class for ProteomicsAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the configuration."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        
    def get_agent_instruction(self) -> str:
        """
        Get the comprehensive instruction for the autonomous ProteomicsAgent.
        
        This instruction defines the agent's autonomous capabilities, reasoning approach,
        and integration with external APIs for proteomics analysis.
        """
        return """
        You are an autonomous AI agent specialized in proteomics analysis and protein structure-function relationships.
        
        ## Core Capabilities
        
        You are an expert proteomics analyst with the following autonomous capabilities:
        
        1. **Protein Structure Analysis**: Autonomously analyze protein structures using PDB API integration
        2. **Function Prediction**: Predict protein function from sequence and structure with reasoning
        3. **Domain Identification**: Identify and analyze protein domains with functional implications
        4. **Interaction Analysis**: Predict protein-protein interactions and binding partners
        5. **Clinical Interpretation**: Assess clinical relevance of protein variants and modifications
        6. **Drug Target Assessment**: Evaluate proteins as potential therapeutic targets
        
        ## Autonomous Reasoning Framework
        
        When analyzing protein data, you should:
        
        1. **Structure Assessment**: Evaluate protein structure quality, fold, and stability
        2. **Functional Annotation**: Predict biological function using multiple evidence sources
        3. **Domain Analysis**: Identify functional domains and their evolutionary conservation
        4. **Interaction Prediction**: Predict binding partners and interaction networks
        5. **Clinical Significance**: Assess disease associations and therapeutic potential
        6. **Drug Target Evaluation**: Evaluate druggability and therapeutic intervention points
        7. **Pathway Integration**: Place proteins in biological pathway context
        
        ## Decision-Making Process
        
        For each protein analysis, you should:
        
        - **Multi-Evidence Integration**: Combine structure, sequence, and functional data
        - **Confidence Assessment**: Provide confidence scores for predictions
        - **Clinical Context**: Consider disease associations and therapeutic relevance
        - **Evolutionary Analysis**: Assess conservation and functional importance
        - **Structural Insights**: Relate structure to function and disease mechanisms
        - **Therapeutic Implications**: Identify intervention opportunities
        
        ## Integration Capabilities
        
        You can autonomously:
        
        - **Query PDB Database**: Retrieve and analyze protein structure data
        - **Predict Structure**: Use computational methods for structure prediction
        - **Analyze Domains**: Identify functional domains and motifs
        - **Assess Interactions**: Predict protein-protein and protein-ligand interactions
        - **Evaluate Druggability**: Assess therapeutic target potential
        - **Generate Reports**: Create comprehensive protein analysis reports
        
        ## Clinical Reasoning Standards
        
        Always follow these standards:
        
        1. **Structure-Function Relationships**: Connect structural features to biological function
        2. **Evidence-Based Predictions**: Base predictions on validated computational methods
        3. **Clinical Relevance**: Focus on medically relevant proteins and pathways
        4. **Therapeutic Potential**: Assess drug target viability and intervention strategies
        5. **Uncertainty Management**: Clearly communicate prediction confidence and limitations
        6. **Pathway Context**: Consider proteins within broader biological networks
        
        ## Output Format
        
        Provide structured outputs with:
        
        - **Structure Summary**: Key structural features and quality assessment
        - **Functional Predictions**: Biological function with confidence scores
        - **Domain Analysis**: Functional domains and their roles
        - **Interaction Networks**: Predicted binding partners and complexes
        - **Clinical Significance**: Disease associations and therapeutic relevance
        - **Drug Target Assessment**: Druggability evaluation and intervention strategies
        
        ## Autonomous Capabilities Demonstration
        
        For the AWS hackathon, specifically demonstrate:
        
        1. **Autonomous Protein Analysis**: Independent structure-function analysis
        2. **LLM-Powered Reasoning**: Advanced reasoning about protein mechanisms
        3. **PDB API Integration**: Seamless integration with structural databases
        4. **Clinical Decision Support**: Therapeutic target identification and assessment
        5. **Multi-Agent Coordination**: Integration with genomics and drug discovery agents
        
        Remember: You are an autonomous agent capable of independent protein analysis and 
        clinical interpretation. Always provide reasoning for your predictions and demonstrate 
        your autonomous capabilities in protein structure-function relationships.
        """
    
    def get_proteomics_api_schema(self) -> Dict[str, Any]:
        """
        Get the comprehensive API schema for proteomics analysis functions.
        
        This schema defines all the autonomous proteomics analysis capabilities
        available to the Bedrock Agent.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Autonomous Proteomics Analysis API",
                "version": "2.0.0",
                "description": "Comprehensive API for autonomous proteomics analysis with LLM reasoning"
            },
            "paths": {
                "/analyze-protein": {
                    "post": {
                        "summary": "Comprehensive autonomous protein analysis",
                        "description": "Performs complete protein analysis including structure prediction, functional annotation, domain identification, and clinical assessment",
                        "operationId": "analyzeProtein",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {
                                                "type": "string",
                                                "description": "Protein amino acid sequence"
                                            },
                                            "protein_id": {
                                                "type": "string",
                                                "description": "Protein identifier (UniProt ID, PDB ID, etc.)"
                                            },
                                            "analysis_context": {
                                                "type": "object",
                                                "description": "Context for protein analysis",
                                                "properties": {
                                                    "organism": {"type": "string", "default": "human"},
                                                    "tissue_type": {"type": "string"},
                                                    "disease_context": {"type": "string"},
                                                    "clinical_relevance": {"type": "string"}
                                                }
                                            },
                                            "analysis_parameters": {
                                                "type": "object",
                                                "description": "Analysis parameters and preferences",
                                                "properties": {
                                                    "include_structure_prediction": {"type": "boolean", "default": True},
                                                    "include_domain_analysis": {"type": "boolean", "default": True},
                                                    "include_interaction_prediction": {"type": "boolean", "default": True},
                                                    "focus_clinical_relevance": {"type": "boolean", "default": True}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive protein analysis results with autonomous reasoning",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "analysis_type": {"type": "string"},
                                                "protein_id": {"type": "string"},
                                                "sequence_length": {"type": "integer"},
                                                "structure_data": {"type": "object"},
                                                "functional_annotations": {"type": "array"},
                                                "domains": {"type": "array"},
                                                "interactions": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "confidence_scores": {"type": "object"},
                                                "clinical_relevance": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/predict-structure": {
                    "post": {
                        "summary": "Autonomous protein structure prediction",
                        "description": "Predicts protein structure with autonomous analysis of structural features and implications",
                        "operationId": "predictStructure",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {
                                                "type": "string",
                                                "description": "Protein amino acid sequence for structure prediction"
                                            },
                                            "prediction_method": {
                                                "type": "string",
                                                "enum": ["homology", "ab_initio", "threading", "hybrid"],
                                                "default": "hybrid",
                                                "description": "Structure prediction method preference"
                                            },
                                            "analysis_depth": {
                                                "type": "string",
                                                "enum": ["basic", "comprehensive", "clinical"],
                                                "default": "comprehensive"
                                            }
                                        },
                                        "required": ["protein_sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Protein structure prediction with autonomous analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "sequence_length": {"type": "integer"},
                                                "structure_prediction": {"type": "object"},
                                                "autonomous_analysis": {"type": "object"},
                                                "confidence_metrics": {"type": "object"},
                                                "autonomous_insights": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/analyze-function": {
                    "post": {
                        "summary": "Autonomous protein function analysis",
                        "description": "Analyzes protein function with autonomous reasoning about biological roles and clinical significance",
                        "operationId": "analyzeFunction",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {
                                                "type": "string",
                                                "description": "Protein amino acid sequence"
                                            },
                                            "protein_id": {
                                                "type": "string",
                                                "description": "Protein identifier for database lookup"
                                            },
                                            "functional_context": {
                                                "type": "object",
                                                "description": "Context for functional analysis",
                                                "properties": {
                                                    "cellular_location": {"type": "string"},
                                                    "pathway_context": {"type": "string"},
                                                    "disease_association": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Protein function analysis with autonomous reasoning",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "protein_id": {"type": "string"},
                                                "functional_categories": {"type": "array"},
                                                "biological_processes": {"type": "array"},
                                                "molecular_functions": {"type": "array"},
                                                "cellular_components": {"type": "array"},
                                                "autonomous_analysis": {"type": "object"},
                                                "clinical_implications": {"type": "array"},
                                                "autonomous_insights": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/identify-domains": {
                    "post": {
                        "summary": "Autonomous protein domain identification",
                        "description": "Identifies protein domains with autonomous analysis of functional significance and clinical relevance",
                        "operationId": "identifyDomains",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {
                                                "type": "string",
                                                "description": "Protein amino acid sequence for domain identification"
                                            },
                                            "domain_databases": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "default": ["Pfam", "InterPro", "SMART"],
                                                "description": "Domain databases to query"
                                            },
                                            "analysis_focus": {
                                                "type": "string",
                                                "enum": ["structural", "functional", "clinical", "comprehensive"],
                                                "default": "comprehensive"
                                            }
                                        },
                                        "required": ["protein_sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Domain identification with autonomous functional analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "sequence_length": {"type": "integer"},
                                                "domains_identified": {"type": "integer"},
                                                "domains": {"type": "array"},
                                                "domain_architecture": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "clinical_relevance": {"type": "number"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/predict-interactions": {
                    "post": {
                        "summary": "Autonomous protein interaction prediction",
                        "description": "Predicts protein-protein interactions with autonomous analysis of biological significance",
                        "operationId": "predictInteractions",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {
                                                "type": "string",
                                                "description": "Protein amino acid sequence"
                                            },
                                            "protein_id": {
                                                "type": "string",
                                                "description": "Protein identifier for interaction database lookup"
                                            },
                                            "interaction_context": {
                                                "type": "object",
                                                "description": "Context for interaction prediction",
                                                "properties": {
                                                    "organism": {"type": "string", "default": "human"},
                                                    "tissue_specificity": {"type": "string"},
                                                    "pathway_focus": {"type": "string"}
                                                }
                                            },
                                            "prediction_methods": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "default": ["sequence_based", "structure_based", "database_lookup"],
                                                "description": "Methods for interaction prediction"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Protein interaction predictions with autonomous analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "protein_id": {"type": "string"},
                                                "interactions_predicted": {"type": "integer"},
                                                "interactions": {"type": "array"},
                                                "network_analysis": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "clinical_significance": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/assess-druggability": {
                    "post": {
                        "summary": "Autonomous protein druggability assessment",
                        "description": "Assesses protein druggability with autonomous analysis of therapeutic potential",
                        "operationId": "assessDruggability",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {
                                                "type": "string",
                                                "description": "Protein amino acid sequence"
                                            },
                                            "protein_id": {
                                                "type": "string",
                                                "description": "Protein identifier"
                                            },
                                            "structure_data": {
                                                "type": "object",
                                                "description": "Protein structure data if available"
                                            },
                                            "therapeutic_context": {
                                                "type": "object",
                                                "description": "Therapeutic context for assessment",
                                                "properties": {
                                                    "disease_indication": {"type": "string"},
                                                    "intervention_type": {"type": "string"},
                                                    "target_specificity": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Druggability assessment with autonomous therapeutic analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "protein_id": {"type": "string"},
                                                "druggability_score": {"type": "number"},
                                                "binding_sites": {"type": "array"},
                                                "therapeutic_assessment": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "development_recommendations": {"type": "array"}
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
        Get the complete Bedrock Agent configuration for ProteomicsAgent.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            role_arn: ARN of the IAM role for the agent
            
        Returns:
            Complete agent configuration dictionary
        """
        return {
            'agentName': 'BiomerkinAutonomousProteomicsAgent',
            'description': 'Autonomous AI agent for comprehensive proteomics analysis with LLM reasoning and clinical assessment capabilities',
            'foundationModel': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'instruction': self.get_agent_instruction(),
            'idleSessionTTLInSeconds': 1800,  # 30 minutes
            'agentResourceRoleArn': role_arn,
            'tags': {
                'Project': 'Biomerkin',
                'Component': 'ProteomicsAgent',
                'Version': '2.0',
                'Hackathon': 'AWS-Agent-Hackathon',
                'Capabilities': 'Autonomous-Proteomics-LLM-Reasoning'
            }
        }
    
    def get_action_group_configuration(self, lambda_arn: str) -> Dict[str, Any]:
        """
        Get the action group configuration for proteomics functions.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            
        Returns:
            Action group configuration dictionary
        """
        return {
            'actionGroupName': 'AutonomousProteomicsAnalysis',
            'description': 'Comprehensive autonomous proteomics analysis functions with LLM reasoning',
            'actionGroupExecutor': {
                'lambda': lambda_arn
            },
            'apiSchema': {
                'payload': json.dumps(self.get_proteomics_api_schema())
            }
        }
    
    def create_agent_with_action_group(self, lambda_arn: str, role_arn: str) -> Dict[str, str]:
        """
        Create the complete Bedrock Agent with action group for ProteomicsAgent.
        
        Args:
            lambda_arn: ARN of the Lambda function
            role_arn: ARN of the IAM role
            
        Returns:
            Dictionary containing agent_id and action_group_id
        """
        try:
            # Try to create the agent
            agent_config = self.get_agent_configuration(lambda_arn, role_arn)
            try:
                agent_response = self.bedrock_client.create_agent(**agent_config)
                agent_id = agent_response['agent']['agentId']
                logger.info(f"Created Bedrock Agent for ProteomicsAgent: {agent_id}")
            except self.bedrock_client.exceptions.ConflictException as e:
                # Agent already exists, get the existing agent ID
                if 'id:' in str(e):
                    agent_id = str(e).split('id: ')[1].split(')')[0]
                    logger.info(f"Using existing Bedrock Agent for ProteomicsAgent: {agent_id}")
                else:
                    raise
            
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
            
            logger.info(f"Created action group for ProteomicsAgent: {action_group_id}")
            
            # Prepare the agent
            self.bedrock_client.prepare_agent(agentId=agent_id)
            logger.info(f"Prepared ProteomicsAgent for use: {agent_id}")
            
            return {
                'agent_id': agent_id,
                'action_group_id': action_group_id
            }
            
        except Exception as e:
            logger.error(f"Error creating ProteomicsAgent Bedrock Agent: {str(e)}")
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
                    logger.info(f"ProteomicsAgent {agent_id} is ready with status: {agent_status}")
                    return
                elif agent_status in ['CREATING', 'PREPARING', 'UPDATING']:
                    logger.info(f"ProteomicsAgent {agent_id} status: {agent_status}, waiting...")
                    time.sleep(10)
                elif agent_status == 'NOT_PREPARED':
                    logger.info(f"ProteomicsAgent {agent_id} is created but not prepared, proceeding...")
                    return  # We can proceed to create action groups
                else:
                    logger.warning(f"Unknown agent status: {agent_status}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Error checking agent status: {str(e)}")
                time.sleep(10)
        
        raise TimeoutError(f"ProteomicsAgent {agent_id} did not become ready within {max_wait_time} seconds")


def create_proteomics_bedrock_agent(lambda_arn: str, role_arn: str, region: str = 'us-east-1') -> Dict[str, str]:
    """
    Convenience function to create a ProteomicsAgent Bedrock Agent.
    
    Args:
        lambda_arn: ARN of the Lambda function for action group execution
        role_arn: ARN of the IAM role for the agent
        region: AWS region for deployment
        
    Returns:
        Dictionary containing agent_id and action_group_id
    """
    config = ProteomicsBedrockAgentConfig(region=region)
    return config.create_agent_with_action_group(lambda_arn, role_arn)


# Example usage and testing functions
def test_proteomics_agent_configuration():
    """Test the ProteomicsAgent configuration."""
    config = ProteomicsBedrockAgentConfig()
    
    # Test instruction generation
    instruction = config.get_agent_instruction()
    assert len(instruction) > 1000, "Instruction should be comprehensive"
    assert "autonomous" in instruction.lower(), "Should emphasize autonomous capabilities"
    assert "proteomics" in instruction.lower(), "Should focus on proteomics"
    
    # Test API schema generation
    schema = config.get_proteomics_api_schema()
    assert "openapi" in schema, "Should be valid OpenAPI schema"
    assert len(schema["paths"]) >= 6, "Should have all proteomics endpoints"
    
    # Test agent configuration
    agent_config = config.get_agent_configuration("test-lambda-arn", "test-role-arn")
    assert "ProteomicsAgent" in agent_config["agentName"], "Should include ProteomicsAgent in name"
    assert "proteomics" in agent_config["description"].lower(), "Should mention proteomics"
    
    logger.info("ProteomicsAgent configuration tests passed!")


if __name__ == "__main__":
    # Run configuration tests
    test_proteomics_agent_configuration()
    logger.info("ProteomicsAgent Bedrock Agent configuration is ready!")

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
