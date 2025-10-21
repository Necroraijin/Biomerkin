"""
Bedrock Agent Configuration for Autonomous DecisionAgent.
This module contains the configuration and setup for the DecisionAgent Bedrock Agent
with enhanced autonomous capabilities and LLM reasoning for medical decision making.
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DecisionBedrockAgentConfig:
    """Configuration class for DecisionAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the configuration."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        
    def get_agent_instruction(self) -> str:
        """
        Get the comprehensive instruction for the autonomous DecisionAgent.
        
        This instruction defines the agent's autonomous capabilities, reasoning approach,
        and integration with medical decision-making processes.
        """
        return """
        You are an autonomous AI agent specialized in medical decision-making, comprehensive report generation, 
        and treatment recommendation based on multi-modal bioinformatics analysis.
        
        ## Core Capabilities
        
        You are an expert medical decision-making agent with the following autonomous capabilities:
        
        1. **Comprehensive Data Integration**: Autonomously integrate genomics, proteomics, literature, and drug discovery data
        2. **Medical Report Generation**: Generate professional medical reports with clinical-grade accuracy
        3. **Risk Assessment**: Perform comprehensive genetic and clinical risk assessments with autonomous reasoning
        4. **Treatment Recommendations**: Generate personalized treatment recommendations based on multi-modal analysis
        5. **Clinical Decision Support**: Provide evidence-based clinical decision support with autonomous insights
        6. **Therapeutic Planning**: Develop comprehensive therapeutic plans with monitoring strategies
        
        ## Autonomous Reasoning Framework
        
        When conducting medical decision-making and report generation, you should:
        
        1. **Multi-Modal Integration**: Autonomously synthesize findings from genomics, proteomics, literature, and drug analysis
        2. **Clinical Correlation**: Correlate genetic findings with clinical phenotypes and disease mechanisms
        3. **Evidence Synthesis**: Integrate scientific evidence with clinical guidelines for decision-making
        4. **Risk Stratification**: Perform autonomous risk stratification based on genetic and clinical factors
        5. **Treatment Prioritization**: Prioritize treatment options using evidence-based autonomous reasoning
        6. **Personalized Medicine**: Generate personalized recommendations based on individual genetic profiles
        7. **Clinical Guidelines Integration**: Incorporate current clinical guidelines and best practices
        
        ## Decision-Making Process
        
        For each medical analysis, you should:
        
        - **Comprehensive Assessment**: Evaluate all available genetic, protein, literature, and drug data
        - **Clinical Significance**: Determine clinical significance of genetic variants and protein functions
        - **Risk-Benefit Analysis**: Perform comprehensive risk-benefit analysis for treatment options
        - **Evidence Grading**: Grade evidence quality and strength for all recommendations
        - **Personalization**: Tailor recommendations to individual patient genetic profiles
        - **Safety Prioritization**: Prioritize patient safety in all clinical recommendations
        - **Monitoring Strategy**: Develop comprehensive monitoring and follow-up strategies
        
        ## Integration Capabilities
        
        You can autonomously:
        
        - **Aggregate Multi-Modal Data**: Integrate findings from genomics, proteomics, literature, and drug agents
        - **Generate Medical Reports**: Create comprehensive, professional medical reports
        - **Assess Genetic Risks**: Evaluate genetic risk factors with clinical correlation
        - **Recommend Treatments**: Generate evidence-based treatment recommendations
        - **Plan Monitoring**: Develop personalized monitoring and follow-up plans
        - **Provide Clinical Insights**: Generate autonomous clinical insights and decision support
        
        ## Clinical Reasoning Standards
        
        Always follow these medical standards:
        
        1. **Evidence-Based Medicine**: Base all recommendations on high-quality scientific evidence
        2. **Clinical Guidelines**: Adhere to current clinical practice guidelines and standards
        3. **Patient Safety**: Prioritize patient safety in all recommendations and decisions
        4. **Personalized Medicine**: Consider individual genetic profiles and patient characteristics
        5. **Ethical Considerations**: Consider ethical implications of genetic findings and recommendations
        6. **Professional Standards**: Maintain professional medical communication standards
        7. **Continuous Monitoring**: Recommend appropriate monitoring and follow-up care
        
        ## Output Format
        
        Provide structured outputs with:
        
        - **Medical Report**: Comprehensive medical report with professional formatting
        - **Risk Assessment**: Detailed genetic and clinical risk assessment
        - **Treatment Recommendations**: Evidence-based treatment recommendations with rationale
        - **Clinical Insights**: Autonomous clinical insights and decision support
        - **Monitoring Plan**: Comprehensive monitoring and follow-up strategy
        - **Safety Considerations**: Patient safety considerations and contraindications
        
        ## Autonomous Capabilities Demonstration
        
        For the AWS hackathon, specifically demonstrate:
        
        1. **Autonomous Medical Decision-Making**: Independent analysis and clinical decision-making
        2. **LLM-Powered Report Generation**: Advanced reasoning for medical report creation
        3. **Multi-Agent Data Integration**: Seamless integration of findings from multiple bioinformatics agents
        4. **Personalized Treatment Planning**: Autonomous generation of personalized treatment plans
        5. **Clinical Decision Support**: Advanced clinical decision support with autonomous insights
        
        Remember: You are an autonomous medical decision-making agent capable of independent 
        clinical analysis and treatment recommendation. Always provide clear reasoning for your 
        recommendations and demonstrate your autonomous capabilities in medical decision-making 
        and comprehensive patient care planning.
        """
    
    def get_decision_api_schema(self) -> Dict[str, Any]:
        """
        Get the comprehensive API schema for medical decision-making functions.
        
        This schema defines all the autonomous medical decision-making capabilities
        available to the Bedrock Agent.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Autonomous Medical Decision-Making API",
                "version": "2.0.0",
                "description": "Comprehensive API for autonomous medical decision-making with LLM reasoning"
            },
            "paths": {
                "/generate-medical-report": {
                    "post": {
                        "summary": "Autonomous medical report generation with comprehensive analysis",
                        "description": "Generates comprehensive medical reports with autonomous reasoning about genetic findings, clinical implications, and treatment recommendations",
                        "operationId": "generateMedicalReport",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "patient_id": {
                                                "type": "string",
                                                "description": "Unique patient identifier"
                                            },
                                            "genomics_results": {
                                                "type": "object",
                                                "description": "Results from genomics analysis",
                                                "properties": {
                                                    "genes": {"type": "array"},
                                                    "mutations": {"type": "array"},
                                                    "protein_sequences": {"type": "array"},
                                                    "quality_metrics": {"type": "object"}
                                                }
                                            },
                                            "proteomics_results": {
                                                "type": "object",
                                                "description": "Results from proteomics analysis",
                                                "properties": {
                                                    "functional_annotations": {"type": "array"},
                                                    "domains": {"type": "array"},
                                                    "interactions": {"type": "array"}
                                                }
                                            },
                                            "literature_results": {
                                                "type": "object",
                                                "description": "Results from literature analysis",
                                                "properties": {
                                                    "summary": {"type": "object"},
                                                    "key_findings": {"type": "array"},
                                                    "confidence_level": {"type": "number"}
                                                }
                                            },
                                            "drug_results": {
                                                "type": "object",
                                                "description": "Results from drug discovery analysis",
                                                "properties": {
                                                    "drug_candidates": {"type": "array"},
                                                    "interactions": {"type": "array"},
                                                    "recommendations": {"type": "array"}
                                                }
                                            },
                                            "report_parameters": {
                                                "type": "object",
                                                "description": "Parameters for report generation",
                                                "properties": {
                                                    "include_risk_assessment": {"type": "boolean", "default": True},
                                                    "include_treatment_recommendations": {"type": "boolean", "default": True},
                                                    "report_format": {"type": "string", "default": "comprehensive"},
                                                    "target_audience": {"type": "string", "default": "medical_professional"}
                                                }
                                            }
                                        },
                                        "required": ["patient_id"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive medical report with autonomous analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "medical_report": {"type": "object"},
                                                "risk_assessment": {"type": "object"},
                                                "treatment_recommendations": {"type": "array"},
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
                "/assess-genetic-risks": {
                    "post": {
                        "summary": "Autonomous genetic risk assessment with clinical correlation",
                        "description": "Performs comprehensive genetic risk assessment with autonomous reasoning about clinical implications and disease predisposition",
                        "operationId": "assessGeneticRisks",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "genomics_data": {
                                                "type": "object",
                                                "description": "Genomics analysis results",
                                                "properties": {
                                                    "genes": {"type": "array"},
                                                    "mutations": {"type": "array"},
                                                    "variants": {"type": "array"}
                                                }
                                            },
                                            "proteomics_data": {
                                                "type": "object",
                                                "description": "Proteomics analysis results"
                                            },
                                            "patient_context": {
                                                "type": "object",
                                                "description": "Patient clinical context",
                                                "properties": {
                                                    "age": {"type": "integer"},
                                                    "gender": {"type": "string"},
                                                    "family_history": {"type": "array"},
                                                    "clinical_presentation": {"type": "string"}
                                                }
                                            },
                                            "assessment_parameters": {
                                                "type": "object",
                                                "description": "Parameters for risk assessment",
                                                "properties": {
                                                    "include_penetrance": {"type": "boolean", "default": True},
                                                    "consider_modifiers": {"type": "boolean", "default": True},
                                                    "population_context": {"type": "string", "default": "general"}
                                                }
                                            }
                                        },
                                        "required": ["genomics_data"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive genetic risk assessment with autonomous analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "overall_risk_assessment": {"type": "object"},
                                                "risk_factors": {"type": "array"},
                                                "protective_factors": {"type": "array"},
                                                "clinical_recommendations": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "confidence_metrics": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/generate-treatment-recommendations": {
                    "post": {
                        "summary": "Autonomous treatment recommendation generation with personalized medicine approach",
                        "description": "Generates personalized treatment recommendations with autonomous reasoning about therapeutic options, drug selection, and monitoring strategies",
                        "operationId": "generateTreatmentRecommendations",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "patient_profile": {
                                                "type": "object",
                                                "description": "Comprehensive patient profile",
                                                "properties": {
                                                    "genetic_profile": {"type": "object"},
                                                    "clinical_data": {"type": "object"},
                                                    "current_medications": {"type": "array"},
                                                    "allergies": {"type": "array"}
                                                }
                                            },
                                            "analysis_results": {
                                                "type": "object",
                                                "description": "Combined analysis results from all agents",
                                                "properties": {
                                                    "genomics": {"type": "object"},
                                                    "proteomics": {"type": "object"},
                                                    "literature": {"type": "object"},
                                                    "drug_discovery": {"type": "object"}
                                                }
                                            },
                                            "treatment_goals": {
                                                "type": "object",
                                                "description": "Treatment goals and objectives",
                                                "properties": {
                                                    "primary_indication": {"type": "string"},
                                                    "secondary_goals": {"type": "array"},
                                                    "quality_of_life_priorities": {"type": "array"}
                                                }
                                            },
                                            "recommendation_parameters": {
                                                "type": "object",
                                                "description": "Parameters for treatment recommendations",
                                                "properties": {
                                                    "evidence_threshold": {"type": "string", "default": "moderate"},
                                                    "safety_priority": {"type": "string", "default": "high"},
                                                    "include_experimental": {"type": "boolean", "default": False}
                                                }
                                            }
                                        },
                                        "required": ["patient_profile", "analysis_results"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Personalized treatment recommendations with autonomous analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "treatment_plan": {"type": "object"},
                                                "drug_recommendations": {"type": "array"},
                                                "monitoring_strategy": {"type": "object"},
                                                "alternative_options": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "safety_considerations": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/provide-clinical-decision-support": {
                    "post": {
                        "summary": "Autonomous clinical decision support with evidence-based recommendations",
                        "description": "Provides comprehensive clinical decision support with autonomous reasoning about diagnostic and therapeutic decisions",
                        "operationId": "provideClinicalDecisionSupport",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "clinical_scenario": {
                                                "type": "object",
                                                "description": "Clinical scenario requiring decision support",
                                                "properties": {
                                                    "patient_presentation": {"type": "string"},
                                                    "diagnostic_question": {"type": "string"},
                                                    "therapeutic_dilemma": {"type": "string"}
                                                }
                                            },
                                            "available_data": {
                                                "type": "object",
                                                "description": "All available patient data",
                                                "properties": {
                                                    "genetic_data": {"type": "object"},
                                                    "clinical_data": {"type": "object"},
                                                    "laboratory_results": {"type": "object"},
                                                    "imaging_results": {"type": "object"}
                                                }
                                            },
                                            "decision_context": {
                                                "type": "object",
                                                "description": "Context for clinical decision-making",
                                                "properties": {
                                                    "urgency_level": {"type": "string"},
                                                    "resource_constraints": {"type": "array"},
                                                    "patient_preferences": {"type": "object"}
                                                }
                                            }
                                        },
                                        "required": ["clinical_scenario", "available_data"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Clinical decision support with autonomous recommendations",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "decision_recommendations": {"type": "array"},
                                                "evidence_summary": {"type": "object"},
                                                "risk_benefit_analysis": {"type": "object"},
                                                "alternative_approaches": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "follow_up_recommendations": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/develop-monitoring-strategy": {
                    "post": {
                        "summary": "Autonomous monitoring strategy development with personalized protocols",
                        "description": "Develops comprehensive monitoring strategies with autonomous reasoning about surveillance protocols and follow-up care",
                        "operationId": "developMonitoringStrategy",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "patient_profile": {
                                                "type": "object",
                                                "description": "Patient profile for monitoring strategy"
                                            },
                                            "treatment_plan": {
                                                "type": "object",
                                                "description": "Current treatment plan requiring monitoring"
                                            },
                                            "risk_factors": {
                                                "type": "array",
                                                "description": "Identified risk factors requiring monitoring"
                                            },
                                            "monitoring_goals": {
                                                "type": "object",
                                                "description": "Goals and objectives for monitoring",
                                                "properties": {
                                                    "safety_monitoring": {"type": "boolean", "default": True},
                                                    "efficacy_monitoring": {"type": "boolean", "default": True},
                                                    "progression_monitoring": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["patient_profile", "treatment_plan"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive monitoring strategy with autonomous protocols",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "monitoring_protocol": {"type": "object"},
                                                "surveillance_schedule": {"type": "array"},
                                                "biomarker_monitoring": {"type": "object"},
                                                "safety_parameters": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "escalation_criteria": {"type": "object"}
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
    
    def create_bedrock_agent(self, agent_name: str, role_arn: str, 
                           foundation_model: str = "anthropic.claude-3-sonnet-20240229-v1:0") -> Dict[str, Any]:
        """
        Create Bedrock Agent for autonomous medical decision-making.
        
        Args:
            agent_name: Name for the Bedrock Agent
            role_arn: IAM role ARN for the agent
            foundation_model: Foundation model to use
            
        Returns:
            Dictionary containing agent creation response
        """
        try:
            response = self.bedrock_client.create_agent(
                agentName=agent_name,
                foundationModel=foundation_model,
                instruction=self.get_agent_instruction(),
                agentResourceRoleArn=role_arn,
                description="Autonomous medical decision-making agent for comprehensive bioinformatics analysis"
            )
            
            logger.info(f"Created Bedrock Agent: {agent_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating Bedrock Agent: {e}")
            raise
    
    def create_action_group(self, agent_id: str, action_group_name: str, 
                          lambda_function_arn: str) -> Dict[str, Any]:
        """
        Create action group for the DecisionAgent Bedrock Agent.
        
        Args:
            agent_id: Bedrock Agent ID
            action_group_name: Name for the action group
            lambda_function_arn: Lambda function ARN for action execution
            
        Returns:
            Dictionary containing action group creation response
        """
        try:
            response = self.bedrock_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=action_group_name,
                description="Medical decision-making and report generation actions",
                actionGroupExecutor={
                    'lambda': lambda_function_arn
                },
                apiSchema={
                    'payload': json.dumps(self.get_decision_api_schema())
                }
            )
            
            logger.info(f"Created action group: {action_group_name}")
            return response
            
        except Exception as e:
            logger.error(f"Error creating action group: {e}")
            raise
    
    def prepare_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Prepare the Bedrock Agent for use.
        
        Args:
            agent_id: Bedrock Agent ID
            
        Returns:
            Dictionary containing preparation response
        """
        try:
            response = self.bedrock_client.prepare_agent(
                agentId=agent_id
            )
            
            logger.info(f"Prepared Bedrock Agent: {agent_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error preparing Bedrock Agent: {e}")
            raise
    
    def get_deployment_config(self) -> Dict[str, Any]:
        """
        Get deployment configuration for the DecisionAgent Bedrock Agent.
        
        Returns:
            Dictionary containing deployment configuration
        """
        return {
            "agent_config": {
                "name": "biomerkin-decision-agent",
                "description": "Autonomous medical decision-making agent for comprehensive bioinformatics analysis",
                "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0",
                "instruction": self.get_agent_instruction()
            },
            "action_groups": [
                {
                    "name": "medical-decision-actions",
                    "description": "Medical decision-making and report generation actions",
                    "api_schema": self.get_decision_api_schema()
                }
            ],
            "lambda_functions": [
                {
                    "name": "bedrock-decision-action",
                    "description": "Lambda function for executing medical decision-making actions",
                    "handler": "bedrock_decision_action.handler",
                    "runtime": "python3.9",
                    "timeout": 300,
                    "memory": 1024
                }
            ]
        }


def main():
    """Main function for testing the configuration."""
    config = DecisionBedrockAgentConfig()
    
    # Print agent instruction
    print("Agent Instruction:")
    print(config.get_agent_instruction())
    print("\n" + "="*80 + "\n")
    
    # Print API schema
    print("API Schema:")
    print(json.dumps(config.get_decision_api_schema(), indent=2))
    print("\n" + "="*80 + "\n")
    
    # Print deployment config
    print("Deployment Configuration:")
    print(json.dumps(config.get_deployment_config(), indent=2))


if __name__ == "__main__":
    main()

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
