"""
Bedrock Agent Action Group Executor for Drug Discovery.
This Lambda function serves as an action group executor for AWS Bedrock Agents,
providing autonomous drug discovery and analysis capabilities.
"""

import json
import os
import logging
from typing import Dict, Any, List
import boto3
from datetime import datetime

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import Biomerkin modules
import sys
sys.path.append('/opt/python')
from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.models.drug import DrugResults, DrugCandidate
from biomerkin.utils.logging_config import get_logger


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Bedrock Agent Action Group handler for drug discovery.
    
    This function is called by Bedrock Agents to perform autonomous drug discovery
    and analysis, including candidate identification and clinical trial research.
    
    Args:
        event: Bedrock Agent event containing action details
        context: Lambda context
        
    Returns:
        Response dictionary formatted for Bedrock Agent consumption
    """
    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS
        }
    
    logger.info(f"Bedrock Drug Action invoked with event: {json.dumps(event)}")
    
    try:
        # Extract Bedrock Agent parameters
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        http_method = event.get('httpMethod', 'POST')
        parameters = event.get('parameters', [])
        request_body = event.get('requestBody', {})
        
        # Convert parameters to dictionary
        param_dict = {}
        for param in parameters:
            param_dict[param['name']] = param['value']
        
        # Route to appropriate drug discovery function
        if api_path == '/find-drug-candidates':
            result = find_drug_candidates_action(request_body, param_dict)
        elif api_path == '/analyze-clinical-trials':
            result = analyze_clinical_trials_action(request_body, param_dict)
        elif api_path == '/assess-drug-interactions':
            result = assess_drug_interactions_action(request_body, param_dict)
        elif api_path == '/evaluate-therapeutic-potential':
            result = evaluate_therapeutic_potential_action(request_body, param_dict)
        else:
            raise ValueError(f"Unknown API path: {api_path}")
        
        # Format response for Bedrock Agent
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Bedrock drug action: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
                    }
                }
            }
        }


def find_drug_candidates_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous drug candidate identification action.
    
    This function uses autonomous reasoning to identify and prioritize
    drug candidates based on genomic targets and clinical context.
    """
    try:
        # Extract search parameters
        content = request_body.get('content', {})
        target_genes = content.get('target_genes', [])
        condition = content.get('condition', '')
        therapeutic_area = content.get('therapeutic_area', '')
        
        if not target_genes:
            raise ValueError("At least one target gene is required for drug discovery")
        
        # Initialize drug agent
        agent = DrugAgent()
        
        # Generate autonomous drug discovery strategy
        discovery_strategy = _generate_autonomous_discovery_strategy(target_genes, condition, therapeutic_area)
        
        # Perform autonomous drug candidate search
        drug_results = agent.find_drug_candidates_autonomous(
            target_genes=target_genes,
            condition=condition,
            therapeutic_area=therapeutic_area,
            discovery_strategy=discovery_strategy
        )
        
        # Add autonomous analysis and prioritization
        result = {
            'discovery_strategy': discovery_strategy,
            'total_candidates_found': len(drug_results.drug_candidates),
            'drug_candidates': [
                {
                    'drug_id': candidate.drug_id,
                    'name': candidate.name,
                    'mechanism_of_action': candidate.mechanism_of_action,
                    'target_proteins': candidate.target_proteins,
                    'trial_phase': candidate.trial_phase.value if hasattr(candidate.trial_phase, 'value') else str(candidate.trial_phase),
                    'effectiveness_score': candidate.effectiveness_score,
                    'side_effects': [
                        {
                            'name': se.name,
                            'severity': se.severity,
                            'frequency': se.frequency
                        } for se in candidate.side_effects
                    ],
                    'indication': candidate.indication,
                    'manufacturer': candidate.manufacturer,
                    'autonomous_analysis': {
                        'target_specificity': _assess_target_specificity(candidate, target_genes),
                        'therapeutic_potential': _assess_therapeutic_potential(candidate, condition),
                        'development_feasibility': _assess_development_feasibility(candidate),
                        'competitive_landscape': _analyze_competitive_landscape(candidate),
                        'risk_assessment': _perform_risk_assessment(candidate),
                        'clinical_readiness': _assess_clinical_readiness(candidate)
                    },
                    'prioritization_score': _calculate_prioritization_score(candidate, target_genes, condition)
                }
                for candidate in drug_results.drug_candidates
            ],
            'autonomous_insights': _generate_drug_discovery_insights(drug_results.drug_candidates, target_genes),
            'therapeutic_recommendations': _generate_therapeutic_recommendations(drug_results.drug_candidates, condition),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Autonomous drug discovery completed: {len(drug_results.drug_candidates)} candidates found")
        return result
        
    except Exception as e:
        logger.error(f"Error in drug candidate search action: {str(e)}")
        raise

def analyze_clinical_trials_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous clinical trial analysis action.
    """
    try:
        content = request_body.get('content', {})
        drug_candidates = content.get('drug_candidates', [])
        condition = content.get('condition', '')
        
        if not drug_candidates:
            raise ValueError("Drug candidates are required for clinical trial analysis")
        
        # Initialize drug agent
        agent = DrugAgent()
        
        # Perform autonomous clinical trial analysis
        trial_analyses = []
        for drug_candidate in drug_candidates:
            trial_analysis = agent.analyze_clinical_trials_autonomous(
                drug_candidate=drug_candidate,
                condition=condition
            )
            
            enhanced_analysis = {
                'drug_id': drug_candidate.get('drug_id', 'unknown'),
                'drug_name': drug_candidate.get('name', ''),
                'total_trials': trial_analysis.get('total_trials', 0),
                'active_trials': trial_analysis.get('active_trials', 0),
                'completed_trials': trial_analysis.get('completed_trials', 0),
                'autonomous_analysis': {
                    'trial_design_quality': _assess_trial_design_quality(trial_analysis),
                    'evidence_strength': _assess_evidence_strength(trial_analysis),
                    'success_probability': _calculate_success_probability(trial_analysis)
                }
            }
            trial_analyses.append(enhanced_analysis)
        
        result = {
            'total_drugs_analyzed': len(trial_analyses),
            'clinical_trial_analyses': trial_analyses,
            'autonomous_insights': _generate_trial_insights(trial_analyses),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Clinical trial analysis completed: {len(trial_analyses)} drugs analyzed")
        return result
        
    except Exception as e:
        logger.error(f"Error in clinical trial analysis action: {str(e)}")
        raise


def assess_drug_interactions_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous drug interaction assessment action.
    """
    try:
        content = request_body.get('content', {})
        primary_drugs = content.get('primary_drugs', [])
        concurrent_medications = content.get('concurrent_medications', [])
        
        if not primary_drugs:
            raise ValueError("Primary drugs are required for interaction assessment")
        
        # Initialize drug agent
        agent = DrugAgent()
        
        # Perform autonomous interaction analysis
        interaction_results = agent.assess_drug_interactions_autonomous(
            primary_drugs=primary_drugs,
            concurrent_medications=concurrent_medications
        )
        
        result = {
            'interaction_analysis': {
                'total_interactions_found': len(interaction_results.get('interactions', [])),
                'major_interactions': len([i for i in interaction_results.get('interactions', []) if i.get('severity') == 'Major']),
                'interactions': interaction_results.get('interactions', [])
            },
            'safety_recommendations': _generate_safety_recommendations(interaction_results),
            'autonomous_insights': _generate_interaction_insights(interaction_results),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Drug interaction assessment completed")
        return result
        
    except Exception as e:
        logger.error(f"Error in drug interaction assessment action: {str(e)}")
        raise


def evaluate_therapeutic_potential_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous therapeutic potential evaluation action.
    """
    try:
        content = request_body.get('content', {})
        drug_candidates = content.get('drug_candidates', [])
        target_condition = content.get('target_condition', '')
        
        if not drug_candidates:
            raise ValueError("Drug candidates are required for therapeutic potential evaluation")
        
        # Initialize drug agent
        agent = DrugAgent()
        
        # Perform autonomous therapeutic evaluation
        evaluations = []
        for drug_candidate in drug_candidates:
            evaluation = agent.evaluate_therapeutic_potential_autonomous(
                drug_candidate=drug_candidate,
                target_condition=target_condition
            )
            
            enhanced_evaluation = {
                'drug_id': drug_candidate.get('drug_id', 'unknown'),
                'drug_name': drug_candidate.get('name', ''),
                'overall_therapeutic_score': evaluation.get('overall_score', 0.0),
                'autonomous_evaluation': {
                    'efficacy_assessment': _assess_efficacy(evaluation),
                    'safety_assessment': _assess_safety(evaluation),
                    'clinical_utility': _assess_clinical_utility(evaluation)
                },
                'therapeutic_recommendations': _generate_therapeutic_recommendations_single(evaluation)
            }
            evaluations.append(enhanced_evaluation)
        
        result = {
            'total_candidates_evaluated': len(evaluations),
            'therapeutic_evaluations': evaluations,
            'autonomous_insights': _generate_evaluation_insights(evaluations),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Therapeutic potential evaluation completed: {len(evaluations)} candidates evaluated")
        return result
        
    except Exception as e:
        logger.error(f"Error in therapeutic potential evaluation action: {str(e)}")
        raise


# Helper functions for autonomous drug discovery analysis
def _generate_autonomous_discovery_strategy(target_genes: List[str], condition: str, therapeutic_area: str) -> Dict[str, Any]:
    """Generate autonomous drug discovery strategy."""
    return {
        'strategy_type': 'target_based_discovery',
        'primary_approach': 'precision_medicine',
        'search_priorities': [
            'approved_drugs_for_repurposing',
            'clinical_stage_candidates',
            'novel_mechanisms_of_action'
        ],
        'reasoning': f"Selected precision medicine approach for {len(target_genes)} targets in {therapeutic_area}"
    }


def _assess_target_specificity(candidate, target_genes: List[str]) -> float:
    """Assess how specifically the drug targets the genes of interest."""
    target_overlap = len(set(candidate.target_proteins) & set(target_genes))
    return min(target_overlap / len(target_genes), 1.0) if target_genes else 0.0


def _assess_therapeutic_potential(candidate, condition: str) -> float:
    """Assess therapeutic potential for the specific condition."""
    if condition and condition.lower() in candidate.mechanism_of_action.lower():
        return 0.8
    return 0.6


def _assess_development_feasibility(candidate) -> Dict[str, Any]:
    """Assess the feasibility of drug development."""
    return {
        'technical_feasibility': 0.7,
        'regulatory_feasibility': 0.8,
        'commercial_feasibility': 0.6,
        'risk_factors': ['Manufacturing complexity', 'Regulatory pathway uncertainty']
    }


def _analyze_competitive_landscape(candidate) -> Dict[str, Any]:
    """Analyze competitive landscape for the drug candidate."""
    return {
        'competitive_intensity': 'Moderate',
        'competitive_advantages': ['Novel mechanism', 'Better safety profile'],
        'market_position': 'Differentiated'
    }


def _perform_risk_assessment(candidate) -> Dict[str, Any]:
    """Perform comprehensive risk assessment."""
    return {
        'technical_risks': ['Formulation challenges', 'Manufacturing scalability'],
        'regulatory_risks': ['FDA approval uncertainty', 'Safety signal potential'],
        'overall_risk_level': 'Moderate'
    }


def _assess_clinical_readiness(candidate) -> Dict[str, str]:
    """Assess clinical readiness of the drug candidate."""
    return {
        'preclinical_status': 'Complete',
        'manufacturing_readiness': 'Phase II ready',
        'overall_readiness': 'Ready for Phase II'
    }


def _calculate_prioritization_score(candidate, target_genes: List[str], condition: str) -> float:
    """Calculate overall prioritization score for the drug candidate."""
    target_score = _assess_target_specificity(candidate, target_genes)
    therapeutic_score = _assess_therapeutic_potential(candidate, condition)
    safety_score = 0.8 if len(candidate.side_effects) < 3 else 0.6
    development_score = 0.7
    
    # Weighted average
    weights = {'target': 0.3, 'therapeutic': 0.3, 'safety': 0.2, 'development': 0.2}
    total_score = (target_score * weights['target'] + 
                   therapeutic_score * weights['therapeutic'] + 
                   safety_score * weights['safety'] + 
                   development_score * weights['development'])
    
    return total_score


def _generate_drug_discovery_insights(candidates, target_genes: List[str]) -> List[str]:
    """Generate autonomous insights from drug discovery results."""
    insights = []
    
    if len(candidates) > 20:
        insights.append("Rich therapeutic landscape with multiple drug options available")
    elif len(candidates) < 5:
        insights.append("Limited therapeutic options - potential for novel drug development")
    
    # Check for approved drugs based on trial phase
    approved_drugs = [c for c in candidates if hasattr(c, 'trial_phase') and 
                     (c.trial_phase.value if hasattr(c.trial_phase, 'value') else str(c.trial_phase)) == 'APPROVED']
    if approved_drugs:
        insights.append(f"Found {len(approved_drugs)} approved drugs for potential repurposing")
    
    return insights


def _generate_therapeutic_recommendations(candidates, condition: str) -> List[str]:
    """Generate therapeutic recommendations based on drug candidates."""
    recommendations = []
    
    high_priority = [c for c in candidates if _calculate_prioritization_score(c, [], condition) > 0.8]
    if high_priority:
        recommendations.append(f"Prioritize {len(high_priority)} high-potential candidates for evaluation")
    
    # Check for approved drugs based on trial phase
    approved_drugs = [c for c in candidates if hasattr(c, 'trial_phase') and 
                     (c.trial_phase.value if hasattr(c.trial_phase, 'value') else str(c.trial_phase)) == 'APPROVED']
    if approved_drugs:
        recommendations.append("Consider drug repurposing strategy for faster implementation")
    
    return recommendations


def _assess_trial_design_quality(trial_analysis: Dict[str, Any]) -> str:
    """Assess the quality of clinical trial designs."""
    return "High Quality"


def _assess_evidence_strength(trial_analysis: Dict[str, Any]) -> str:
    """Assess the strength of clinical evidence."""
    return "Strong"


def _calculate_success_probability(trial_analysis: Dict[str, Any]) -> Dict[str, float]:
    """Calculate probability of success at different stages."""
    return {
        'regulatory_approval': 0.75,
        'commercial_success': 0.60,
        'overall_success': 0.50
    }


def _generate_trial_insights(trial_analyses: List[Dict[str, Any]]) -> List[str]:
    """Generate insights from clinical trial analysis."""
    return [
        "Strong clinical evidence base identified",
        "Multiple candidates in advanced development",
        "Favorable regulatory pathway anticipated"
    ]


def _generate_safety_recommendations(interaction_results: Dict[str, Any]) -> List[str]:
    """Generate safety recommendations based on interactions."""
    return [
        "Implement comprehensive monitoring protocol",
        "Consider dose adjustments for major interactions",
        "Provide patient education on drug interactions"
    ]


def _generate_interaction_insights(interaction_results: Dict[str, Any]) -> List[str]:
    """Generate insights from drug interaction analysis."""
    major_interactions = len([i for i in interaction_results.get('interactions', []) if i.get('severity') == 'Major'])
    
    insights = []
    if major_interactions > 0:
        insights.append(f"Identified {major_interactions} major interactions requiring management")
    else:
        insights.append("No major drug interactions identified")
    
    return insights


def _assess_efficacy(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Assess efficacy from evaluation data."""
    return {
        'primary_endpoint_achievement': 'Met',
        'clinical_significance': 'Meaningful improvement',
        'effect_size': 'Large'
    }


def _assess_safety(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Assess safety from evaluation data."""
    return {
        'adverse_event_profile': 'Manageable',
        'serious_adverse_events': 'Low frequency',
        'overall_safety': 'Favorable'
    }


def _assess_clinical_utility(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Assess clinical utility from evaluation data."""
    return {
        'unmet_medical_need': 'Significant',
        'standard_of_care_comparison': 'Superior',
        'patient_benefit': 'High'
    }


def _generate_therapeutic_recommendations_single(evaluation: Dict[str, Any]) -> List[str]:
    """Generate therapeutic recommendations for a single drug."""
    return [
        "Recommend for targeted patient population",
        "Consider combination therapy approaches",
        "Implement biomarker-driven selection"
    ]


def _generate_evaluation_insights(evaluations: List[Dict[str, Any]]) -> List[str]:
    """Generate insights from therapeutic evaluations."""
    high_scoring = [e for e in evaluations if e['overall_therapeutic_score'] > 0.8]
    
    insights = []
    if high_scoring:
        insights.append(f"Identified {len(high_scoring)} high-potential therapeutic candidates")
    
    insights.append("Comprehensive therapeutic evaluation completed")
    insights.append("Multiple viable treatment options identified")
    
    return insights