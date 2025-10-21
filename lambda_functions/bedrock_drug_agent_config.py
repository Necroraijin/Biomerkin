"""
Bedrock Agent Configuration for Autonomous DrugAgent.
This module contains the configuration and setup for the DrugAgent Bedrock Agent
with enhanced autonomous capabilities and LLM reasoning.
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DrugBedrockAgentConfig:
    """Configuration class for DrugAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the configuration."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        
    def get_agent_instruction(self) -> str:
        """
        Get the comprehensive instruction for the autonomous DrugAgent.
        
        This instruction defines the agent's autonomous capabilities, reasoning approach,
        and integration with external APIs for drug discovery and clinical trials.
        """
        return """
        You are an autonomous AI agent specialized in drug discovery, clinical trial analysis, and therapeutic recommendation.
        
        ## Core Capabilities
        
        You are an expert drug discovery analyst with the following autonomous capabilities:
        
        1. **Intelligent Drug Discovery**: Autonomously identify drug candidates using target-based and phenotype-based approaches
        2. **Clinical Trial Intelligence**: Analyze clinical trial data with autonomous reasoning about success probability
        3. **Therapeutic Assessment**: Evaluate therapeutic potential with comprehensive risk-benefit analysis
        4. **Drug Interaction Analysis**: Assess drug-drug interactions with autonomous safety recommendations
        5. **Treatment Optimization**: Generate personalized treatment recommendations based on genomic profiles
        6. **Regulatory Intelligence**: Assess regulatory pathways and approval probability with reasoning
        
        ## Autonomous Reasoning Framework
        
        When conducting drug discovery and analysis, you should:
        
        1. **Target Validation**: Autonomously assess target druggability and therapeutic potential
        2. **Compound Prioritization**: Rank drug candidates using multi-criteria decision analysis
        3. **Clinical Evidence Synthesis**: Integrate clinical trial data with autonomous reasoning
        4. **Safety Assessment**: Evaluate safety profiles with comprehensive risk analysis
        5. **Efficacy Prediction**: Predict therapeutic efficacy using available evidence
        6. **Market Analysis**: Assess competitive landscape and commercial viability
        7. **Regulatory Strategy**: Develop regulatory pathway recommendations
        
        ## Decision-Making Process
        
        For each drug analysis, you should:
        
        - **Multi-Database Integration**: Query DrugBank, ClinicalTrials.gov, and other databases intelligently
        - **Evidence-Based Ranking**: Rank candidates based on scientific evidence and clinical potential
        - **Risk-Benefit Analysis**: Perform comprehensive risk-benefit assessments
        - **Personalized Medicine**: Consider genomic profiles for personalized recommendations
        - **Safety Prioritization**: Prioritize patient safety in all recommendations
        - **Clinical Actionability**: Focus on clinically actionable therapeutic options
        
        ## Integration Capabilities
        
        You can autonomously:
        
        - **Execute DrugBank Queries**: Search drug databases for target-specific compounds
        - **Analyze Clinical Trials**: Extract insights from ClinicalTrials.gov data
        - **Assess Drug Interactions**: Evaluate potential drug-drug interactions
        - **Predict Therapeutic Outcomes**: Use AI reasoning for outcome prediction
        - **Generate Treatment Plans**: Create comprehensive treatment recommendations
        - **Monitor Drug Development**: Track pipeline drugs and development progress
        
        ## Clinical Reasoning Standards
        
        Always follow these standards:
        
        1. **Evidence-Based Medicine**: Base recommendations on high-quality clinical evidence
        2. **Safety First**: Prioritize patient safety in all therapeutic recommendations
        3. **Personalized Approach**: Consider individual patient characteristics and genomics
        4. **Regulatory Compliance**: Ensure recommendations align with regulatory guidelines
        5. **Ethical Considerations**: Consider ethical implications of treatment recommendations
        6. **Continuous Monitoring**: Recommend ongoing monitoring and safety surveillance
        
        ## Output Format
        
        Provide structured outputs with:
        
        - **Drug Discovery Summary**: Key findings and candidate prioritization
        - **Clinical Evidence**: Comprehensive analysis of trial data and outcomes
        - **Safety Assessment**: Detailed safety profile and risk analysis
        - **Therapeutic Recommendations**: Specific treatment recommendations with rationale
        - **Monitoring Plan**: Ongoing monitoring and safety surveillance recommendations
        - **Autonomous Insights**: AI-generated insights and pattern recognition
        
        ## Autonomous Capabilities Demonstration
        
        For the AWS hackathon, specifically demonstrate:
        
        1. **Autonomous Drug Discovery**: Independent identification and prioritization of drug candidates
        2. **LLM-Powered Clinical Analysis**: Advanced reasoning about clinical trial outcomes
        3. **External API Integration**: Seamless integration with drug databases and clinical trial registries
        4. **Therapeutic Decision Making**: Autonomous generation of treatment recommendations
        5. **Multi-Agent Coordination**: Integration with genomics, proteomics, and literature agents
        
        Remember: You are an autonomous agent capable of independent drug discovery and 
        therapeutic analysis. Always provide reasoning for your recommendations and demonstrate 
        your autonomous capabilities in pharmaceutical research and clinical decision-making.
        """
    
    def get_drug_api_schema(self) -> Dict[str, Any]:
        """
        Get the comprehensive API schema for drug discovery functions.
        
        This schema defines all the autonomous drug discovery capabilities
        available to the Bedrock Agent.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Autonomous Drug Discovery API",
                "version": "2.0.0",
                "description": "Comprehensive API for autonomous drug discovery with LLM reasoning"
            },
            "paths": {
                "/find-drug-candidates": {
                    "post": {
                        "summary": "Autonomous drug candidate identification and prioritization",
                        "description": "Identifies and prioritizes drug candidates using autonomous reasoning about target druggability and therapeutic potential",
                        "operationId": "findDrugCandidates",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "target_genes": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "List of target genes for drug discovery"
                                            },
                                            "condition": {
                                                "type": "string",
                                                "description": "Medical condition or disease for treatment"
                                            },
                                            "therapeutic_area": {
                                                "type": "string",
                                                "description": "Therapeutic area (e.g., oncology, neurology, cardiology)"
                                            },
                                            "patient_context": {
                                                "type": "object",
                                                "description": "Patient context for personalized recommendations",
                                                "properties": {
                                                    "age": {"type": "integer"},
                                                    "gender": {"type": "string"},
                                                    "comorbidities": {"type": "array"},
                                                    "current_medications": {"type": "array"},
                                                    "genomic_profile": {"type": "object"}
                                                }
                                            },
                                            "discovery_parameters": {
                                                "type": "object",
                                                "description": "Parameters for drug discovery",
                                                "properties": {
                                                    "include_approved_drugs": {"type": "boolean", "default": True},
                                                    "include_investigational": {"type": "boolean", "default": True},
                                                    "minimum_efficacy_score": {"type": "number", "default": 0.5},
                                                    "maximum_risk_level": {"type": "string", "default": "moderate"},
                                                    "prioritize_safety": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["target_genes"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Drug candidates with autonomous analysis and prioritization",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "discovery_strategy": {"type": "object"},
                                                "total_candidates_found": {"type": "integer"},
                                                "drug_candidates": {"type": "array"},
                                                "autonomous_analysis": {"type": "object"},
                                                "prioritization_reasoning": {"type": "object"},
                                                "therapeutic_recommendations": {"type": "array"},
                                                "safety_considerations": {"type": "array"},
                                                "autonomous_insights": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/analyze-clinical-trials": {
                    "post": {
                        "summary": "Autonomous clinical trial analysis with success prediction",
                        "description": "Analyzes clinical trials with autonomous reasoning about design quality, success probability, and regulatory outlook",
                        "operationId": "analyzeClinicalTrials",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "drug_candidates": {
                                                "type": "array",
                                                "description": "Drug candidates for clinical trial analysis",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "drug_id": {"type": "string"},
                                                        "name": {"type": "string"},
                                                        "mechanism_of_action": {"type": "string"}
                                                    }
                                                }
                                            },
                                            "condition": {
                                                "type": "string",
                                                "description": "Target medical condition"
                                            },
                                            "analysis_parameters": {
                                                "type": "object",
                                                "description": "Parameters for trial analysis",
                                                "properties": {
                                                    "include_completed_trials": {"type": "boolean", "default": True},
                                                    "include_ongoing_trials": {"type": "boolean", "default": True},
                                                    "minimum_phase": {"type": "string", "default": "Phase I"},
                                                    "assess_success_probability": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["drug_candidates"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Clinical trial analysis with autonomous insights",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "total_drugs_analyzed": {"type": "integer"},
                                                "clinical_trial_analyses": {"type": "array"},
                                                "success_predictions": {"type": "object"},
                                                "regulatory_outlook": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "development_recommendations": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/assess-drug-interactions": {
                    "post": {
                        "summary": "Autonomous drug interaction assessment with safety recommendations",
                        "description": "Assesses drug-drug interactions with autonomous reasoning about clinical significance and safety management",
                        "operationId": "assessDrugInteractions",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "primary_drugs": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Primary drugs for interaction assessment"
                                            },
                                            "concurrent_medications": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Concurrent medications to check for interactions"
                                            },
                                            "patient_factors": {
                                                "type": "object",
                                                "description": "Patient factors affecting drug interactions",
                                                "properties": {
                                                    "age": {"type": "integer"},
                                                    "kidney_function": {"type": "string"},
                                                    "liver_function": {"type": "string"},
                                                    "genetic_variants": {"type": "array"}
                                                }
                                            },
                                            "assessment_parameters": {
                                                "type": "object",
                                                "description": "Parameters for interaction assessment",
                                                "properties": {
                                                    "include_minor_interactions": {"type": "boolean", "default": False},
                                                    "assess_clinical_significance": {"type": "boolean", "default": True},
                                                    "generate_management_plan": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["primary_drugs"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Drug interaction assessment with autonomous safety analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "interaction_analysis": {"type": "object"},
                                                "safety_recommendations": {"type": "array"},
                                                "management_strategies": {"type": "array"},
                                                "monitoring_requirements": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "risk_mitigation": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/evaluate-therapeutic-potential": {
                    "post": {
                        "summary": "Autonomous therapeutic potential evaluation with personalized recommendations",
                        "description": "Evaluates therapeutic potential of drug candidates with autonomous reasoning about efficacy, safety, and patient-specific factors",
                        "operationId": "evaluateTherapeuticPotential",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "drug_candidates": {
                                                "type": "array",
                                                "description": "Drug candidates for therapeutic evaluation",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "drug_id": {"type": "string"},
                                                        "name": {"type": "string"},
                                                        "mechanism_of_action": {"type": "string"},
                                                        "development_stage": {"type": "string"}
                                                    }
                                                }
                                            },
                                            "target_condition": {
                                                "type": "string",
                                                "description": "Target medical condition for treatment"
                                            },
                                            "patient_profile": {
                                                "type": "object",
                                                "description": "Patient profile for personalized evaluation",
                                                "properties": {
                                                    "genomic_markers": {"type": "array"},
                                                    "biomarkers": {"type": "array"},
                                                    "disease_stage": {"type": "string"},
                                                    "prior_treatments": {"type": "array"}
                                                }
                                            },
                                            "evaluation_criteria": {
                                                "type": "object",
                                                "description": "Criteria for therapeutic evaluation",
                                                "properties": {
                                                    "efficacy_weight": {"type": "number", "default": 0.4},
                                                    "safety_weight": {"type": "number", "default": 0.3},
                                                    "accessibility_weight": {"type": "number", "default": 0.2},
                                                    "cost_weight": {"type": "number", "default": 0.1}
                                                }
                                            }
                                        },
                                        "required": ["drug_candidates", "target_condition"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Therapeutic evaluation with autonomous personalized recommendations",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "total_candidates_evaluated": {"type": "integer"},
                                                "therapeutic_evaluations": {"type": "array"},
                                                "personalized_recommendations": {"type": "array"},
                                                "treatment_sequencing": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "clinical_decision_support": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/generate-treatment-plan": {
                    "post": {
                        "summary": "Autonomous treatment plan generation with monitoring strategy",
                        "description": "Generates comprehensive treatment plans with autonomous reasoning about drug selection, dosing, and monitoring",
                        "operationId": "generateTreatmentPlan",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "selected_drugs": {
                                                "type": "array",
                                                "description": "Selected drugs for treatment plan",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "drug_id": {"type": "string"},
                                                        "name": {"type": "string"},
                                                        "indication": {"type": "string"}
                                                    }
                                                }
                                            },
                                            "patient_profile": {
                                                "type": "object",
                                                "description": "Comprehensive patient profile"
                                            },
                                            "treatment_goals": {
                                                "type": "object",
                                                "description": "Treatment goals and objectives",
                                                "properties": {
                                                    "primary_endpoint": {"type": "string"},
                                                    "secondary_endpoints": {"type": "array"},
                                                    "quality_of_life_goals": {"type": "array"}
                                                }
                                            },
                                            "plan_parameters": {
                                                "type": "object",
                                                "description": "Parameters for treatment plan generation",
                                                "properties": {
                                                    "include_combination_therapy": {"type": "boolean", "default": True},
                                                    "consider_drug_interactions": {"type": "boolean", "default": True},
                                                    "optimize_for_adherence": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["selected_drugs", "patient_profile"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive treatment plan with autonomous optimization",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "treatment_plan": {"type": "object"},
                                                "dosing_recommendations": {"type": "array"},
                                                "monitoring_strategy": {"type": "object"},
                                                "safety_considerations": {"type": "array"},
                                                "autonomous_optimizations": {"type": "array"},
                                                "contingency_plans": {"type": "array"}
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
        Get the complete Bedrock Agent configuration for DrugAgent.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            role_arn: ARN of the IAM role for the agent
            
        Returns:
            Complete agent configuration dictionary
        """
        return {
            'agentName': 'BiomerkinAutonomousDrugAgent',
            'description': 'Autonomous AI agent for comprehensive drug discovery and therapeutic analysis with LLM reasoning and clinical decision-making capabilities',
            'foundationModel': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'instruction': self.get_agent_instruction(),
            'idleSessionTTLInSeconds': 1800,  # 30 minutes
            'agentResourceRoleArn': role_arn,
            'tags': {
                'Project': 'Biomerkin',
                'Component': 'DrugAgent',
                'Version': '2.0',
                'Hackathon': 'AWS-Agent-Hackathon',
                'Capabilities': 'Autonomous-LLM-Reasoning'
            }
        }
    
    def get_action_group_configuration(self, lambda_arn: str) -> Dict[str, Any]:
        """
        Get the action group configuration for drug discovery functions.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            
        Returns:
            Action group configuration dictionary
        """
        return {
            'actionGroupName': 'AutonomousDrugDiscovery',
            'description': 'Comprehensive autonomous drug discovery functions with LLM reasoning',
            'actionGroupExecutor': {
                'lambda': lambda_arn
            },
            'apiSchema': {
                'payload': json.dumps(self.get_drug_api_schema())
            }
        }
    
    def create_agent_with_action_group(self, lambda_arn: str, role_arn: str) -> Dict[str, str]:
        """
        Create the complete Bedrock Agent with action group for DrugAgent.
        
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
            
            logger.info(f"Created Bedrock Agent for DrugAgent: {agent_id}")
            
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
            
            logger.info(f"Created action group for DrugAgent: {action_group_id}")
            
            # Prepare the agent
            self.bedrock_client.prepare_agent(agentId=agent_id)
            logger.info(f"Prepared DrugAgent for use: {agent_id}")
            
            return {
                'agent_id': agent_id,
                'action_group_id': action_group_id
            }
            
        except Exception as e:
            logger.error(f"Error creating DrugAgent Bedrock Agent: {str(e)}")
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
                    logger.info(f"DrugAgent {agent_id} is ready with status: {agent_status}")
                    return
                elif agent_status in ['CREATING', 'PREPARING', 'UPDATING']:
                    logger.info(f"DrugAgent {agent_id} status: {agent_status}, waiting...")
                    time.sleep(10)
                else:
                    logger.warning(f"Unknown agent status: {agent_status}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Error checking agent status: {str(e)}")
                time.sleep(10)
        
        raise TimeoutError(f"DrugAgent {agent_id} did not become ready within {max_wait_time} seconds")


def create_drug_bedrock_agent(lambda_arn: str, role_arn: str, region: str = 'us-east-1') -> Dict[str, str]:
    """
    Convenience function to create a DrugAgent Bedrock Agent.
    
    Args:
        lambda_arn: ARN of the Lambda function for action group execution
        role_arn: ARN of the IAM role for the agent
        region: AWS region for deployment
        
    Returns:
        Dictionary containing agent_id and action_group_id
    """
    config = DrugBedrockAgentConfig(region=region)
    return config.create_agent_with_action_group(lambda_arn, role_arn)


# Example usage and testing functions
def test_drug_agent_configuration():
    """Test the DrugAgent configuration."""
    config = DrugBedrockAgentConfig()
    
    # Test instruction generation
    instruction = config.get_agent_instruction()
    assert len(instruction) > 1000, "Instruction should be comprehensive"
    assert "autonomous" in instruction.lower(), "Should emphasize autonomous capabilities"
    
    # Test API schema generation
    schema = config.get_drug_api_schema()
    assert "paths" in schema, "Schema should contain API paths"
    assert len(schema["paths"]) >= 5, "Should have multiple API endpoints"
    
    # Test agent configuration
    agent_config = config.get_agent_configuration("test-lambda-arn", "test-role-arn")
    assert agent_config["agentName"] == "BiomerkinAutonomousDrugAgent", "Agent name should be correct"
    assert "autonomous" in agent_config["description"].lower(), "Description should mention autonomous capabilities"
    
    print("All DrugAgent configuration tests passed!")


if __name__ == "__main__":
    test_drug_agent_configuration()

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
