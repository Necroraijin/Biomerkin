"""
Bedrock Agent Configuration for Autonomous LiteratureAgent.
This module contains the configuration and setup for the LiteratureAgent Bedrock Agent
with enhanced autonomous capabilities and LLM reasoning.
"""

import json
import boto3
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class LiteratureBedrockAgentConfig:
    """Configuration class for LiteratureAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the configuration."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        
    def get_agent_instruction(self) -> str:
        """
        Get the comprehensive instruction for the autonomous LiteratureAgent.
        
        This instruction defines the agent's autonomous capabilities, reasoning approach,
        and integration with external APIs for literature research.
        """
        return """
        You are an autonomous AI agent specialized in scientific literature research and medical evidence synthesis.
        
        ## Core Capabilities
        
        You are an expert literature research analyst with the following autonomous capabilities:
        
        1. **Intelligent Literature Search**: Autonomously search PubMed and scientific databases using optimized strategies
        2. **Evidence Synthesis**: Synthesize findings from multiple research articles with reasoning
        3. **Clinical Relevance Assessment**: Evaluate clinical significance of research findings autonomously
        4. **Research Gap Identification**: Identify gaps in current research and suggest future directions
        5. **Quality Assessment**: Assess study quality and evidence strength with autonomous reasoning
        6. **Medical Report Integration**: Generate literature sections for comprehensive medical reports
        
        ## Autonomous Reasoning Framework
        
        When conducting literature research, you should:
        
        1. **Search Strategy Optimization**: Autonomously select optimal search terms and strategies
        2. **Relevance Scoring**: Score articles for relevance using multiple criteria with reasoning
        3. **Evidence Quality Assessment**: Evaluate study design, methodology, and evidence strength
        4. **Clinical Significance Analysis**: Assess clinical applicability and actionability
        5. **Consensus Building**: Identify consensus findings and conflicting evidence
        6. **Research Prioritization**: Prioritize findings by clinical importance and evidence quality
        7. **Knowledge Gap Analysis**: Identify areas requiring additional research
        
        ## Decision-Making Process
        
        For each literature analysis, you should:
        
        - **Multi-Database Integration**: Search across multiple scientific databases intelligently
        - **Dynamic Search Refinement**: Adapt search strategies based on initial results
        - **Evidence Hierarchies**: Apply evidence-based medicine hierarchies autonomously
        - **Clinical Context Integration**: Consider patient context and clinical scenarios
        - **Bias Assessment**: Identify potential biases and study limitations
        - **Therapeutic Implications**: Extract actionable therapeutic insights
        
        ## Integration Capabilities
        
        You can autonomously:
        
        - **Execute PubMed Searches**: Perform sophisticated literature searches with Boolean logic
        - **Apply MeSH Terms**: Use Medical Subject Headings for precise search targeting
        - **Assess Study Quality**: Evaluate methodology and evidence strength
        - **Synthesize Evidence**: Combine findings from multiple studies with reasoning
        - **Generate Summaries**: Create comprehensive literature summaries and insights
        - **Identify Trends**: Detect research trends and emerging areas
        
        ## Clinical Reasoning Standards
        
        Always follow these standards:
        
        1. **Evidence-Based Medicine**: Apply EBM principles and evidence hierarchies
        2. **Systematic Approach**: Use systematic review methodologies when appropriate
        3. **Bias Recognition**: Identify and account for various types of research bias
        4. **Clinical Applicability**: Focus on clinically relevant and actionable findings
        5. **Quality Assessment**: Evaluate study quality using established criteria
        6. **Transparency**: Clearly document search strategies and selection criteria
        
        ## Output Format
        
        Provide structured outputs with:
        
        - **Search Strategy**: Detailed search methodology and terms used
        - **Evidence Summary**: Key findings organized by strength and relevance
        - **Clinical Insights**: Actionable clinical implications and recommendations
        - **Quality Assessment**: Study quality evaluation and evidence strength
        - **Research Gaps**: Identified gaps and future research directions
        - **Autonomous Reasoning**: AI-generated insights and pattern recognition
        
        ## Autonomous Capabilities Demonstration
        
        For the AWS hackathon, specifically demonstrate:
        
        1. **Autonomous Literature Mining**: Independent research strategy development
        2. **LLM-Powered Evidence Synthesis**: Advanced reasoning about research findings
        3. **PubMed API Integration**: Seamless integration with scientific databases
        4. **Clinical Decision Support**: Evidence-based clinical recommendations
        5. **Multi-Agent Coordination**: Integration with genomics, proteomics, and drug agents
        
        Remember: You are an autonomous agent capable of independent literature research and 
        evidence synthesis. Always provide reasoning for your assessments and demonstrate 
        your autonomous capabilities in scientific literature analysis.
        """
    
    def get_literature_api_schema(self) -> Dict[str, Any]:
        """
        Get the comprehensive API schema for literature research functions.
        
        This schema defines all the autonomous literature research capabilities
        available to the Bedrock Agent.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Autonomous Literature Research API",
                "version": "2.0.0",
                "description": "Comprehensive API for autonomous literature research with LLM reasoning"
            },
            "paths": {
                "/search-literature": {
                    "post": {
                        "summary": "Autonomous literature search with intelligent strategy",
                        "description": "Performs intelligent literature search using optimized strategies and autonomous relevance assessment",
                        "operationId": "searchLiterature",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "genes": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "List of genes to search for in literature"
                                            },
                                            "conditions": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "description": "Medical conditions or diseases to include in search"
                                            },
                                            "search_context": {
                                                "type": "object",
                                                "description": "Context for literature search",
                                                "properties": {
                                                    "patient_context": {"type": "string"},
                                                    "clinical_question": {"type": "string"},
                                                    "research_focus": {"type": "string"},
                                                    "time_range": {"type": "string"}
                                                }
                                            },
                                            "search_parameters": {
                                                "type": "object",
                                                "description": "Search parameters and preferences",
                                                "properties": {
                                                    "max_articles": {"type": "integer", "default": 50},
                                                    "include_reviews": {"type": "boolean", "default": True},
                                                    "include_clinical_trials": {"type": "boolean", "default": True},
                                                    "minimum_relevance": {"type": "number", "default": 0.5},
                                                    "language": {"type": "string", "default": "english"}
                                                }
                                            }
                                        },
                                        "required": ["genes"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Literature search results with autonomous analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "search_strategy": {"type": "object"},
                                                "total_articles_found": {"type": "integer"},
                                                "articles": {"type": "array"},
                                                "autonomous_analysis": {"type": "object"},
                                                "relevance_distribution": {"type": "object"},
                                                "evidence_quality": {"type": "object"},
                                                "clinical_insights": {"type": "array"},
                                                "research_gaps": {"type": "array"},
                                                "autonomous_recommendations": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/summarize-articles": {
                    "post": {
                        "summary": "Autonomous article summarization with clinical focus",
                        "description": "Summarizes scientific articles with autonomous clinical relevance assessment and evidence synthesis",
                        "operationId": "summarizeArticles",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "articles": {
                                                "type": "array",
                                                "description": "List of articles to summarize",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "pmid": {"type": "string"},
                                                        "title": {"type": "string"},
                                                        "abstract": {"type": "string"},
                                                        "authors": {"type": "array"},
                                                        "journal": {"type": "string"},
                                                        "publication_date": {"type": "string"}
                                                    }
                                                }
                                            },
                                            "summarization_context": {
                                                "type": "object",
                                                "description": "Context for summarization",
                                                "properties": {
                                                    "clinical_focus": {"type": "string"},
                                                    "target_audience": {"type": "string", "default": "clinicians"},
                                                    "summary_depth": {"type": "string", "enum": ["brief", "detailed", "comprehensive"], "default": "detailed"}
                                                }
                                            },
                                            "analysis_parameters": {
                                                "type": "object",
                                                "description": "Parameters for autonomous analysis",
                                                "properties": {
                                                    "assess_study_quality": {"type": "boolean", "default": True},
                                                    "identify_clinical_implications": {"type": "boolean", "default": True},
                                                    "extract_therapeutic_insights": {"type": "boolean", "default": True},
                                                    "evaluate_evidence_strength": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["articles"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Article summaries with autonomous clinical analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "total_articles_summarized": {"type": "integer"},
                                                "article_summaries": {"type": "array"},
                                                "evidence_synthesis": {"type": "object"},
                                                "clinical_consensus": {"type": "object"},
                                                "autonomous_insights": {"type": "array"},
                                                "therapeutic_implications": {"type": "array"},
                                                "quality_assessment": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/generate-search-terms": {
                    "post": {
                        "summary": "Autonomous search term generation and optimization",
                        "description": "Generates optimized search terms using autonomous reasoning about genomic context and clinical relevance",
                        "operationId": "generateSearchTerms",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "genomic_data": {
                                                "type": "object",
                                                "description": "Genomic analysis results for term generation",
                                                "properties": {
                                                    "genes": {"type": "array"},
                                                    "variants": {"type": "array"},
                                                    "pathways": {"type": "array"}
                                                }
                                            },
                                            "clinical_context": {
                                                "type": "object",
                                                "description": "Clinical context for search optimization",
                                                "properties": {
                                                    "patient_phenotype": {"type": "string"},
                                                    "family_history": {"type": "string"},
                                                    "clinical_presentation": {"type": "string"},
                                                    "therapeutic_goals": {"type": "string"}
                                                }
                                            },
                                            "search_strategy": {
                                                "type": "object",
                                                "description": "Search strategy preferences",
                                                "properties": {
                                                    "search_focus": {"type": "string", "enum": ["comprehensive", "clinical", "therapeutic", "mechanistic"], "default": "comprehensive"},
                                                    "include_mesh_terms": {"type": "boolean", "default": True},
                                                    "include_synonyms": {"type": "boolean", "default": True},
                                                    "optimize_for_precision": {"type": "boolean", "default": False}
                                                }
                                            }
                                        },
                                        "required": ["genomic_data"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Optimized search terms with autonomous reasoning",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "primary_search_terms": {"type": "array"},
                                                "secondary_search_terms": {"type": "array"},
                                                "boolean_queries": {"type": "array"},
                                                "mesh_terms": {"type": "array"},
                                                "autonomous_reasoning": {"type": "object"},
                                                "search_predictions": {"type": "object"},
                                                "optimization_strategy": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/assess-relevance": {
                    "post": {
                        "summary": "Autonomous relevance assessment with clinical scoring",
                        "description": "Assesses article relevance using autonomous reasoning about clinical significance and therapeutic potential",
                        "operationId": "assessRelevance",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "articles": {
                                                "type": "array",
                                                "description": "Articles to assess for relevance",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "pmid": {"type": "string"},
                                                        "title": {"type": "string"},
                                                        "abstract": {"type": "string"},
                                                        "keywords": {"type": "array"}
                                                    }
                                                }
                                            },
                                            "genomic_context": {
                                                "type": "object",
                                                "description": "Genomic context for relevance assessment",
                                                "properties": {
                                                    "target_genes": {"type": "array"},
                                                    "variants_of_interest": {"type": "array"},
                                                    "pathways": {"type": "array"}
                                                }
                                            },
                                            "assessment_criteria": {
                                                "type": "object",
                                                "description": "Criteria for relevance assessment",
                                                "properties": {
                                                    "clinical_relevance_weight": {"type": "number", "default": 0.4},
                                                    "therapeutic_potential_weight": {"type": "number", "default": 0.3},
                                                    "evidence_quality_weight": {"type": "number", "default": 0.3},
                                                    "recency_bonus": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["articles", "genomic_context"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Relevance assessment with autonomous clinical analysis",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "total_articles_assessed": {"type": "integer"},
                                                "relevance_assessments": {"type": "array"},
                                                "autonomous_insights": {"type": "object"},
                                                "clinical_prioritization": {"type": "object"},
                                                "therapeutic_relevance": {"type": "object"},
                                                "evidence_quality_distribution": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/synthesize-evidence": {
                    "post": {
                        "summary": "Autonomous evidence synthesis and consensus building",
                        "description": "Synthesizes evidence from multiple articles with autonomous reasoning about clinical consensus and conflicting findings",
                        "operationId": "synthesizeEvidence",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "articles": {
                                                "type": "array",
                                                "description": "Articles for evidence synthesis"
                                            },
                                            "synthesis_context": {
                                                "type": "object",
                                                "description": "Context for evidence synthesis",
                                                "properties": {
                                                    "research_question": {"type": "string"},
                                                    "clinical_scenario": {"type": "string"},
                                                    "target_population": {"type": "string"}
                                                }
                                            },
                                            "synthesis_parameters": {
                                                "type": "object",
                                                "description": "Parameters for evidence synthesis",
                                                "properties": {
                                                    "identify_consensus": {"type": "boolean", "default": True},
                                                    "highlight_conflicts": {"type": "boolean", "default": True},
                                                    "assess_bias": {"type": "boolean", "default": True},
                                                    "generate_recommendations": {"type": "boolean", "default": True}
                                                }
                                            }
                                        },
                                        "required": ["articles"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Evidence synthesis with autonomous clinical reasoning",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "evidence_synthesis": {"type": "object"},
                                                "consensus_findings": {"type": "array"},
                                                "conflicting_evidence": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "clinical_recommendations": {"type": "array"},
                                                "research_gaps": {"type": "array"},
                                                "confidence_assessment": {"type": "object"}
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
        Get the complete Bedrock Agent configuration for LiteratureAgent.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            role_arn: ARN of the IAM role for the agent
            
        Returns:
            Complete agent configuration dictionary
        """
        return {
            'agentName': 'BiomerkinAutonomousLiteratureAgent',
            'description': 'Autonomous AI agent for comprehensive literature research with LLM reasoning and evidence synthesis capabilities',
            'foundationModel': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'instruction': self.get_agent_instruction(),
            'idleSessionTTLInSeconds': 1800,  # 30 minutes
            'agentResourceRoleArn': role_arn,
            'tags': {
                'Project': 'Biomerkin',
                'Component': 'LiteratureAgent',
                'Version': '2.0',
                'Hackathon': 'AWS-Agent-Hackathon',
                'Capabilities': 'Autonomous-Literature-Research'
            }
        }
    
    def get_action_group_configuration(self, lambda_arn: str) -> Dict[str, Any]:
        """
        Get the action group configuration for literature research functions.
        
        Args:
            lambda_arn: ARN of the Lambda function for action group execution
            
        Returns:
            Action group configuration dictionary
        """
        return {
            'actionGroupName': 'AutonomousLiteratureResearch',
            'description': 'Comprehensive autonomous literature research functions with LLM reasoning',
            'actionGroupExecutor': {
                'lambda': lambda_arn
            },
            'apiSchema': {
                'payload': json.dumps(self.get_literature_api_schema())
            }
        }
    
    def create_agent_with_action_group(self, lambda_arn: str, role_arn: str) -> Dict[str, str]:
        """
        Create the complete Bedrock Agent with action group for LiteratureAgent.
        
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
            
            logger.info(f"Created Bedrock Agent for LiteratureAgent: {agent_id}")
            
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
            
            logger.info(f"Created action group for LiteratureAgent: {action_group_id}")
            
            # Prepare the agent
            self.bedrock_client.prepare_agent(agentId=agent_id)
            logger.info(f"Prepared LiteratureAgent for use: {agent_id}")
            
            return {
                'agent_id': agent_id,
                'action_group_id': action_group_id
            }
            
        except Exception as e:
            logger.error(f"Error creating LiteratureAgent Bedrock Agent: {str(e)}")
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
                    logger.info(f"LiteratureAgent {agent_id} is ready with status: {agent_status}")
                    return
                elif agent_status in ['CREATING', 'PREPARING', 'UPDATING']:
                    logger.info(f"LiteratureAgent {agent_id} status: {agent_status}, waiting...")
                    time.sleep(10)
                else:
                    logger.warning(f"Unknown agent status: {agent_status}")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Error checking agent status: {str(e)}")
                time.sleep(10)
        
        raise TimeoutError(f"LiteratureAgent {agent_id} did not become ready within {max_wait_time} seconds")


def create_literature_bedrock_agent(lambda_arn: str, role_arn: str, region: str = 'us-east-1') -> Dict[str, str]:
    """
    Convenience function to create a LiteratureAgent Bedrock Agent.
    
    Args:
        lambda_arn: ARN of the Lambda function for action group execution
        role_arn: ARN of the IAM role for the agent
        region: AWS region for deployment
        
    Returns:
        Dictionary containing agent_id and action_group_id
    """
    config = LiteratureBedrockAgentConfig(region=region)
    return config.create_agent_with_action_group(lambda_arn, role_arn)


# Example usage and testing functions
def test_literature_agent_configuration():
    """Test the LiteratureAgent configuration."""
    config = LiteratureBedrockAgentConfig()
    
    # Test instruction generation
    instruction = config.get_agent_instruction()
    assert len(instruction) > 1000, "Instruction should be comprehensive"
    assert "autonomous" in instruction.lower(), "Should emphasize autonomous capabilities"
    
    # Test API schema generation
    schema = config.get_literature_api_schema()
    assert "paths" in schema, "Schema should contain API paths"
    assert len(schema["paths"]) >= 5, "Should have multiple API endpoints"
    
    # Test agent configuration
    lambda_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    role_arn = "arn:aws:iam::123456789012:role/test-role"
    
    agent_config = config.get_agent_configuration(lambda_arn, role_arn)
    assert agent_config["agentName"] == "BiomerkinAutonomousLiteratureAgent"
    assert "autonomous" in agent_config["description"].lower()
    
    action_group_config = config.get_action_group_configuration(lambda_arn)
    assert action_group_config["actionGroupName"] == "AutonomousLiteratureResearch"
    
    print("All LiteratureAgent configuration tests passed!")


if __name__ == "__main__":
    test_literature_agent_configuration()

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
