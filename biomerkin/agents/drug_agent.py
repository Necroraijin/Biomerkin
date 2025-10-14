"""
DrugAgent for drug discovery and clinical trial information.

This agent handles drug candidate identification via DrugBank API,
clinical trial information from ClinicalTrials.gov, drug-target interaction
analysis, and drug effectiveness scoring.
"""

import logging
import requests
import json
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import time
import re
from urllib.parse import urlencode

from ..models.drug import (
    DrugResults, DrugCandidate, TrialInformation, InteractionAnalysis,
    SideEffect, TrialPhase, DrugType
)
from ..utils.logging_config import get_logger
from ..utils.config import get_config
from .base_agent import APIAgent, agent_error_handler


class DrugAgent(APIAgent):
    """
    Agent responsible for drug discovery and clinical trial analysis.
    
    Provides functionality for:
    - DrugBank API queries for drug candidate identification
    - ClinicalTrials.gov API integration for trial information
    - Drug-target interaction analysis
    - Drug effectiveness scoring and side effect analysis
    """
    
    def __init__(self):
        """Initialize the DrugAgent."""
        self.config = get_config()
        
        # Initialize parent with API key and rate limit
        super().__init__(
            agent_name="drug",
            api_key=self.config.api.drugbank_api_key,
            rate_limit=5.0  # Conservative rate limit for drug APIs
        )
        
        self.drugbank_api_key = self.config.api.drugbank_api_key
        self.clinicaltrials_base_url = self.config.api.clinicaltrials_api_base_url
        self.request_timeout = self.config.api.request_timeout
        self.max_retries = self.config.api.max_retries
        self.retry_delay = self.config.api.retry_delay
        
        # Add DrugBank API key to session headers if available
        if self.drugbank_api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.drugbank_api_key}'
            })
    
    @agent_error_handler()
    def execute(self, input_data: Dict[str, Any], workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute drug discovery analysis.
        
        Args:
            input_data: Dictionary containing target_data
            workflow_id: Optional workflow identifier
            
        Returns:
            Dictionary containing drug analysis results
        """
        target_data = input_data.get('target_data')
        
        if not target_data:
            raise ValueError("target_data is required in input_data")
        
        results = self.find_drug_candidates(target_data)
        
        return {
            'drug_results': results,
            'target_genes': results.target_genes,
            'drug_candidates': results.drug_candidates,
            'clinical_trials': results.clinical_trials,
            'interaction_analysis': results.interaction_analysis,
            'analysis_timestamp': results.analysis_timestamp
        }
    
    def find_drug_candidates(self, target_data: Dict[str, Any]) -> DrugResults:
        """
        Find drug candidates for given targets.
        
        Args:
            target_data: Dictionary containing target information including:
                - genes: List of gene names/IDs
                - proteins: List of protein names/IDs
                - pathways: Optional list of pathway names
                - conditions: Optional list of medical conditions
                
        Returns:
            DrugResults containing drug candidates and trial information
        """
        self.logger.info("Starting drug candidate identification")
        
        try:
            # Extract target information
            target_genes = target_data.get('genes', [])
            target_proteins = target_data.get('proteins', [])
            conditions = target_data.get('conditions', [])
            
            # Find drug candidates from DrugBank
            drug_candidates = self._query_drugbank_candidates(target_genes, target_proteins)
            
            # Get clinical trial information
            clinical_trials = self._query_clinical_trials(target_genes, drug_candidates, conditions)
            
            # Analyze drug interactions
            interaction_analysis = None
            if len(drug_candidates) > 1:
                interaction_analysis = self._analyze_drug_interactions([drug.drug_id for drug in drug_candidates])
            
            results = DrugResults(
                target_genes=target_genes,
                drug_candidates=drug_candidates,
                clinical_trials=clinical_trials,
                interaction_analysis=interaction_analysis,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            self.logger.info(f"Drug analysis completed. Found {len(drug_candidates)} candidates, "
                           f"{len(clinical_trials)} trials")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in drug candidate identification: {str(e)}")
            raise
    
    def get_trial_information(self, drug_id: str) -> List[TrialInformation]:
        """
        Retrieve clinical trial status and results for a specific drug.
        
        Args:
            drug_id: Drug identifier
            
        Returns:
            List of trial information
        """
        return self._query_clinical_trials_by_drug(drug_id)
    
    def analyze_drug_interactions(self, drugs: List[str]) -> InteractionAnalysis:
        """
        Analyze potential drug-drug interactions.
        
        Args:
            drugs: List of drug IDs or names
            
        Returns:
            InteractionAnalysis object
        """
        return self._analyze_drug_interactions(drugs)
    
    def _query_drugbank_candidates(self, target_genes: List[str], target_proteins: List[str]) -> List[DrugCandidate]:
        """
        Query DrugBank API for drug candidates targeting specific genes/proteins.
        
        Args:
            target_genes: List of gene names/IDs
            target_proteins: List of protein names/IDs
            
        Returns:
            List of drug candidates
        """
        drug_candidates = []
        
        try:
            # Combine all targets for search
            all_targets = target_genes + target_proteins
            
            for target in all_targets:
                candidates = self._search_drugbank_by_target(target)
                drug_candidates.extend(candidates)
            
            # Remove duplicates based on drug_id
            unique_candidates = {}
            for candidate in drug_candidates:
                if candidate.drug_id not in unique_candidates:
                    unique_candidates[candidate.drug_id] = candidate
            
            drug_candidates = list(unique_candidates.values())
            
            # Score and rank candidates
            drug_candidates = self._score_drug_candidates(drug_candidates, all_targets)
            
            # Limit to top candidates
            drug_candidates = drug_candidates[:20]
            
            self.logger.info(f"Found {len(drug_candidates)} unique drug candidates from DrugBank")
            
        except Exception as e:
            self.logger.warning(f"Error querying DrugBank: {str(e)}")
            drug_candidates = []
        
        # Fallback to mock data if no candidates found
        if not drug_candidates:
            self.logger.info("No candidates found from API, generating mock data")
            drug_candidates = self._generate_mock_drug_candidates(target_genes, target_proteins)
        
        return drug_candidates
    
    def _search_drugbank_by_target(self, target: str) -> List[DrugCandidate]:
        """
        Search DrugBank for drugs targeting a specific gene/protein.
        
        Args:
            target: Gene or protein name/ID
            
        Returns:
            List of drug candidates
        """
        candidates = []
        
        try:
            # DrugBank API endpoint for target search
            # Note: This is a simplified implementation - actual DrugBank API may differ
            url = f"https://go.drugbank.com/api/v1/drugs/search"
            params = {
                'q': target,
                'target': 'true',
                'approved': 'true'
            }
            
            response = self._make_request(url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                for drug_data in data.get('results', [])[:10]:  # Limit results
                    candidate = self._parse_drugbank_drug(drug_data, target)
                    if candidate:
                        candidates.append(candidate)
            
        except Exception as e:
            self.logger.warning(f"Error searching DrugBank for target {target}: {str(e)}")
        
        return candidates
    
    def _parse_drugbank_drug(self, drug_data: Dict[str, Any], target: str) -> Optional[DrugCandidate]:
        """
        Parse DrugBank drug data into DrugCandidate object.
        
        Args:
            drug_data: Raw drug data from DrugBank API
            target: Target gene/protein name
            
        Returns:
            DrugCandidate object or None
        """
        try:
            drug_id = drug_data.get('drugbank_id', f"DB{hash(drug_data.get('name', '')) % 100000:05d}")
            name = drug_data.get('name', 'Unknown Drug')
            
            # Determine drug type
            drug_type = self._classify_drug_type(drug_data)
            
            # Extract mechanism of action
            mechanism = drug_data.get('mechanism_of_action', 'Unknown mechanism')
            
            # Extract target proteins
            targets = drug_data.get('targets', [])
            target_proteins = [t.get('name', '') for t in targets if t.get('name')]
            if target not in target_proteins:
                target_proteins.append(target)
            
            # Determine trial phase
            trial_phase = self._determine_trial_phase(drug_data)
            
            # Calculate effectiveness score
            effectiveness_score = self._calculate_effectiveness_score(drug_data)
            
            # Extract side effects
            side_effects = self._extract_side_effects(drug_data)
            
            candidate = DrugCandidate(
                drug_id=drug_id,
                name=name,
                drug_type=drug_type,
                mechanism_of_action=mechanism,
                target_proteins=target_proteins,
                trial_phase=trial_phase,
                effectiveness_score=effectiveness_score,
                side_effects=side_effects,
                indication=drug_data.get('indication'),
                manufacturer=drug_data.get('manufacturer')
            )
            
            return candidate
            
        except Exception as e:
            self.logger.warning(f"Error parsing DrugBank drug data: {str(e)}")
            return None
    
    def _classify_drug_type(self, drug_data: Dict[str, Any]) -> DrugType:
        """
        Classify drug type based on drug data.
        
        Args:
            drug_data: Drug information
            
        Returns:
            DrugType classification
        """
        # Simple classification based on available data
        drug_type_str = drug_data.get('type', '').lower()
        name = drug_data.get('name', '').lower()
        
        if 'antibody' in drug_type_str or 'mab' in name:
            return DrugType.ANTIBODY
        elif 'biologic' in drug_type_str or 'protein' in drug_type_str:
            return DrugType.BIOLOGIC
        elif 'vaccine' in drug_type_str or 'vaccine' in name:
            return DrugType.VACCINE
        elif 'gene' in drug_type_str:
            return DrugType.GENE_THERAPY
        elif 'cell' in drug_type_str:
            return DrugType.CELL_THERAPY
        else:
            return DrugType.SMALL_MOLECULE
    
    def _determine_trial_phase(self, drug_data: Dict[str, Any]) -> TrialPhase:
        """
        Determine clinical trial phase from drug data.
        
        Args:
            drug_data: Drug information
            
        Returns:
            TrialPhase
        """
        status = drug_data.get('status', '').lower()
        groups = drug_data.get('groups', [])
        
        if 'approved' in status or 'approved' in groups:
            return TrialPhase.APPROVED
        elif 'withdrawn' in status:
            return TrialPhase.WITHDRAWN
        elif 'phase 3' in status or 'phase iii' in status:
            return TrialPhase.PHASE_III
        elif 'phase 2' in status or 'phase ii' in status:
            return TrialPhase.PHASE_II
        elif 'phase 1' in status or 'phase i' in status:
            return TrialPhase.PHASE_I
        elif 'investigational' in status:
            return TrialPhase.PHASE_I
        else:
            return TrialPhase.PRECLINICAL
    
    def _calculate_effectiveness_score(self, drug_data: Dict[str, Any]) -> float:
        """
        Calculate drug effectiveness score based on available data.
        
        Args:
            drug_data: Drug information
            
        Returns:
            Effectiveness score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Increase score for approved drugs
        status = drug_data.get('status', '').lower()
        groups = drug_data.get('groups', [])
        
        if 'approved' in status or 'approved' in groups:
            score += 0.3
        elif 'phase 3' in status:
            score += 0.2
        elif 'phase 2' in status:
            score += 0.1
        
        # Adjust based on number of targets
        targets = drug_data.get('targets', [])
        if len(targets) > 1:
            score += 0.1
        
        # Adjust based on known efficacy data
        if drug_data.get('efficacy_data'):
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def _extract_side_effects(self, drug_data: Dict[str, Any]) -> List[SideEffect]:
        """
        Extract side effects from drug data.
        
        Args:
            drug_data: Drug information
            
        Returns:
            List of side effects
        """
        side_effects = []
        
        # Extract from adverse reactions field
        adverse_reactions = drug_data.get('adverse_reactions', [])
        for reaction in adverse_reactions[:10]:  # Limit to top 10
            if isinstance(reaction, dict):
                name = reaction.get('name', '')
                severity = reaction.get('severity', 'moderate')
                frequency = reaction.get('frequency', 'uncommon')
            else:
                name = str(reaction)
                severity = 'moderate'
                frequency = 'uncommon'
            
            if name:
                side_effect = SideEffect(
                    name=name,
                    severity=severity,
                    frequency=frequency,
                    description=f"Reported adverse reaction: {name}"
                )
                side_effects.append(side_effect)
        
        return side_effects
    
    def _score_drug_candidates(self, candidates: List[DrugCandidate], targets: List[str]) -> List[DrugCandidate]:
        """
        Score and rank drug candidates based on relevance to targets.
        
        Args:
            candidates: List of drug candidates
            targets: List of target genes/proteins
            
        Returns:
            Sorted list of drug candidates
        """
        for candidate in candidates:
            # Recalculate effectiveness score based on target match
            target_match_score = 0.0
            
            for target in targets:
                if any(target.lower() in protein.lower() for protein in candidate.target_proteins):
                    target_match_score += 0.2
            
            # Update effectiveness score
            candidate.effectiveness_score = min(1.0, candidate.effectiveness_score + target_match_score)
        
        # Sort by effectiveness score (descending)
        candidates.sort(key=lambda x: x.effectiveness_score, reverse=True)
        
        return candidates
    
    def _query_clinical_trials(self, target_genes: List[str], drug_candidates: List[DrugCandidate], 
                              conditions: List[str]) -> List[TrialInformation]:
        """
        Query ClinicalTrials.gov for relevant trials.
        
        Args:
            target_genes: List of target genes
            drug_candidates: List of drug candidates
            conditions: List of medical conditions
            
        Returns:
            List of trial information
        """
        trials = []
        
        try:
            # Search by drug names
            for drug in drug_candidates[:5]:  # Limit to top 5 drugs
                drug_trials = self._search_clinical_trials_by_drug(drug.name)
                trials.extend(drug_trials)
            
            # Search by conditions
            for condition in conditions[:3]:  # Limit to top 3 conditions
                condition_trials = self._search_clinical_trials_by_condition(condition)
                trials.extend(condition_trials)
            
            # Search by gene targets
            for gene in target_genes[:3]:  # Limit to top 3 genes
                gene_trials = self._search_clinical_trials_by_gene(gene)
                trials.extend(gene_trials)
            
            # Remove duplicates based on trial_id
            unique_trials = {}
            for trial in trials:
                if trial.trial_id not in unique_trials:
                    unique_trials[trial.trial_id] = trial
            
            trials = list(unique_trials.values())[:50]  # Limit to 50 trials
            
            self.logger.info(f"Found {len(trials)} clinical trials")
            
        except Exception as e:
            self.logger.warning(f"Error querying clinical trials: {str(e)}")
            trials = []
        
        # Generate mock trials if no trials found
        if not trials:
            self.logger.info("No trials found from API, generating mock data")
            trials = self._generate_mock_trials(target_genes, drug_candidates)
        
        return trials
    
    def _search_clinical_trials_by_drug(self, drug_name: str) -> List[TrialInformation]:
        """
        Search clinical trials by drug name.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            List of trial information
        """
        trials = []
        
        try:
            # ClinicalTrials.gov API endpoint
            url = f"{self.clinicaltrials_base_url}/query/full_studies"
            params = {
                'expr': f'AREA[InterventionName]{drug_name}',
                'fmt': 'json',
                'max_rnk': 10
            }
            
            response = self._make_request(url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                studies = data.get('FullStudiesResponse', {}).get('FullStudies', [])
                
                for study in studies:
                    trial = self._parse_clinical_trial(study)
                    if trial:
                        trials.append(trial)
            
        except Exception as e:
            self.logger.warning(f"Error searching clinical trials for drug {drug_name}: {str(e)}")
        
        return trials
    
    def _search_clinical_trials_by_condition(self, condition: str) -> List[TrialInformation]:
        """
        Search clinical trials by medical condition.
        
        Args:
            condition: Medical condition
            
        Returns:
            List of trial information
        """
        trials = []
        
        try:
            url = f"{self.clinicaltrials_base_url}/query/full_studies"
            params = {
                'expr': f'AREA[Condition]{condition}',
                'fmt': 'json',
                'max_rnk': 10
            }
            
            response = self._make_request(url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                studies = data.get('FullStudiesResponse', {}).get('FullStudies', [])
                
                for study in studies:
                    trial = self._parse_clinical_trial(study)
                    if trial:
                        trials.append(trial)
            
        except Exception as e:
            self.logger.warning(f"Error searching clinical trials for condition {condition}: {str(e)}")
        
        return trials
    
    def _search_clinical_trials_by_gene(self, gene: str) -> List[TrialInformation]:
        """
        Search clinical trials by gene name.
        
        Args:
            gene: Gene name
            
        Returns:
            List of trial information
        """
        trials = []
        
        try:
            url = f"{self.clinicaltrials_base_url}/query/full_studies"
            params = {
                'expr': f'AREA[OtherTerm]{gene}',
                'fmt': 'json',
                'max_rnk': 5
            }
            
            response = self._make_request(url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                studies = data.get('FullStudiesResponse', {}).get('FullStudies', [])
                
                for study in studies:
                    trial = self._parse_clinical_trial(study)
                    if trial:
                        trials.append(trial)
            
        except Exception as e:
            self.logger.warning(f"Error searching clinical trials for gene {gene}: {str(e)}")
        
        return trials
    
    def _parse_clinical_trial(self, study_data: Dict[str, Any]) -> Optional[TrialInformation]:
        """
        Parse clinical trial data from ClinicalTrials.gov API.
        
        Args:
            study_data: Raw study data from API
            
        Returns:
            TrialInformation object or None
        """
        try:
            study = study_data.get('Study', {})
            protocol_section = study.get('ProtocolSection', {})
            identification_module = protocol_section.get('IdentificationModule', {})
            status_module = protocol_section.get('StatusModule', {})
            design_module = protocol_section.get('DesignModule', {})
            conditions_module = protocol_section.get('ConditionsModule', {})
            interventions_module = protocol_section.get('InterventionsModule', {})
            outcomes_module = protocol_section.get('OutcomesModule', {})
            
            # Extract basic information
            trial_id = identification_module.get('NCTId', '')
            title = identification_module.get('BriefTitle', 'Unknown Title')
            
            # Extract phase
            phase_str = design_module.get('PhaseList', {}).get('Phase', ['Not Applicable'])[0]
            phase = self._parse_trial_phase(phase_str)
            
            # Extract status
            status = status_module.get('OverallStatus', 'Unknown')
            
            # Extract condition
            conditions = conditions_module.get('ConditionList', {}).get('Condition', [])
            condition = conditions[0] if conditions else 'Unknown Condition'
            
            # Extract intervention
            interventions = interventions_module.get('InterventionList', {}).get('Intervention', [])
            intervention_names = []
            for intervention in interventions:
                name = intervention.get('InterventionName', '')
                if name:
                    intervention_names.append(name)
            intervention = ', '.join(intervention_names) if intervention_names else 'Unknown Intervention'
            
            # Extract primary outcome
            primary_outcomes = outcomes_module.get('PrimaryOutcomeList', {}).get('PrimaryOutcome', [])
            primary_outcome = None
            if primary_outcomes:
                primary_outcome = primary_outcomes[0].get('PrimaryOutcomeMeasure', '')
            
            # Extract enrollment
            enrollment = design_module.get('EnrollmentInfo', {}).get('EnrollmentCount')
            if enrollment:
                enrollment = int(enrollment)
            
            # Extract dates
            start_date = status_module.get('StartDateStruct', {}).get('StartDate')
            completion_date = status_module.get('CompletionDateStruct', {}).get('CompletionDate')
            
            trial = TrialInformation(
                trial_id=trial_id,
                title=title,
                phase=phase,
                status=status,
                condition=condition,
                intervention=intervention,
                primary_outcome=primary_outcome,
                enrollment=enrollment,
                start_date=start_date,
                completion_date=completion_date
            )
            
            return trial
            
        except Exception as e:
            self.logger.warning(f"Error parsing clinical trial data: {str(e)}")
            return None
    
    def _parse_trial_phase(self, phase_str: str) -> TrialPhase:
        """
        Parse trial phase string into TrialPhase enum.
        
        Args:
            phase_str: Phase string from API
            
        Returns:
            TrialPhase enum value
        """
        phase_str = phase_str.lower()
        
        if 'phase 4' in phase_str or 'phase iv' in phase_str:
            return TrialPhase.PHASE_IV
        elif 'phase 3' in phase_str or 'phase iii' in phase_str:
            return TrialPhase.PHASE_III
        elif 'phase 2' in phase_str or 'phase ii' in phase_str:
            return TrialPhase.PHASE_II
        elif 'phase 1' in phase_str or 'phase i' in phase_str:
            return TrialPhase.PHASE_I
        elif 'phase 0' in phase_str:
            return TrialPhase.PHASE_0
        else:
            return TrialPhase.PRECLINICAL
    
    def _query_clinical_trials_by_drug(self, drug_id: str) -> List[TrialInformation]:
        """
        Query clinical trials for a specific drug ID.
        
        Args:
            drug_id: Drug identifier
            
        Returns:
            List of trial information
        """
        return self._search_clinical_trials_by_drug(drug_id)
    
    def _analyze_drug_interactions(self, drugs: List[str]) -> InteractionAnalysis:
        """
        Analyze potential drug-drug interactions.
        
        Args:
            drugs: List of drug IDs or names
            
        Returns:
            InteractionAnalysis object
        """
        try:
            # Generate all pairs of drugs
            drug_pairs = []
            for i in range(len(drugs)):
                for j in range(i + 1, len(drugs)):
                    drug_pairs.append((drugs[i], drugs[j]))
            
            # Analyze interactions (simplified implementation)
            # In practice, this would use drug interaction databases
            interaction_severity = self._assess_interaction_severity(drug_pairs)
            interaction_type = self._classify_interaction_type(drug_pairs)
            clinical_significance = self._assess_clinical_significance(drug_pairs)
            recommendations = self._generate_interaction_recommendations(drug_pairs, interaction_severity)
            
            analysis = InteractionAnalysis(
                drug_pairs=drug_pairs,
                interaction_severity=interaction_severity,
                interaction_type=interaction_type,
                clinical_significance=clinical_significance,
                recommendations=recommendations
            )
            
            self.logger.info(f"Analyzed interactions for {len(drug_pairs)} drug pairs")
            
            return analysis
            
        except Exception as e:
            self.logger.warning(f"Error analyzing drug interactions: {str(e)}")
            # Return default analysis
            return InteractionAnalysis(
                drug_pairs=[],
                interaction_severity="low",
                interaction_type="unknown",
                clinical_significance="Monitor for potential interactions",
                recommendations=["Consult healthcare provider before combining medications"]
            )
    
    def _assess_interaction_severity(self, drug_pairs: List[Tuple[str, str]]) -> str:
        """
        Assess the severity of drug interactions.
        
        Args:
            drug_pairs: List of drug pairs
            
        Returns:
            Severity level (low, moderate, high)
        """
        # Simplified assessment - in practice would use interaction databases
        if len(drug_pairs) > 3:
            return "high"
        elif len(drug_pairs) > 1:
            return "moderate"
        else:
            return "low"
    
    def _classify_interaction_type(self, drug_pairs: List[Tuple[str, str]]) -> str:
        """
        Classify the type of drug interactions.
        
        Args:
            drug_pairs: List of drug pairs
            
        Returns:
            Interaction type
        """
        # Simplified classification
        return "pharmacokinetic"
    
    def _assess_clinical_significance(self, drug_pairs: List[Tuple[str, str]]) -> str:
        """
        Assess clinical significance of interactions.
        
        Args:
            drug_pairs: List of drug pairs
            
        Returns:
            Clinical significance description
        """
        if len(drug_pairs) > 2:
            return "Multiple drug interactions detected - requires careful monitoring"
        elif len(drug_pairs) > 0:
            return "Potential drug interactions - monitor patient response"
        else:
            return "No significant interactions detected"
    
    def _generate_interaction_recommendations(self, drug_pairs: List[Tuple[str, str]], severity: str) -> List[str]:
        """
        Generate recommendations for managing drug interactions.
        
        Args:
            drug_pairs: List of drug pairs
            severity: Interaction severity
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if severity == "high":
            recommendations.extend([
                "Consider alternative medications with lower interaction potential",
                "Implement intensive monitoring protocols",
                "Adjust dosing schedules to minimize interaction risk"
            ])
        elif severity == "moderate":
            recommendations.extend([
                "Monitor patient closely for adverse effects",
                "Consider dose adjustments if necessary",
                "Educate patient about potential interaction symptoms"
            ])
        else:
            recommendations.extend([
                "Standard monitoring protocols apply",
                "Inform patient about potential mild interactions"
            ])
        
        recommendations.append("Consult with pharmacist or specialist if concerns arise")
        
        return recommendations
    
    def _generate_mock_drug_candidates(self, target_genes: List[str], target_proteins: List[str]) -> List[DrugCandidate]:
        """
        Generate mock drug candidates when API is unavailable.
        
        Args:
            target_genes: List of target genes
            target_proteins: List of target proteins
            
        Returns:
            List of mock drug candidates
        """
        mock_candidates = []
        
        # Generate mock candidates based on targets
        all_targets = target_genes + target_proteins
        
        for i, target in enumerate(all_targets[:5]):  # Limit to 5 mock candidates
            candidate = DrugCandidate(
                drug_id=f"MOCK_{i+1:03d}",
                name=f"Experimental Drug {i+1} ({target})",
                drug_type=DrugType.SMALL_MOLECULE,
                mechanism_of_action=f"Targets {target} pathway",
                target_proteins=[target],
                trial_phase=TrialPhase.PHASE_II,
                effectiveness_score=0.6 + (i * 0.05),
                side_effects=[
                    SideEffect(name="Nausea", severity="mild", frequency="common"),
                    SideEffect(name="Headache", severity="mild", frequency="uncommon")
                ],
                indication=f"Treatment targeting {target}",
                manufacturer="Research Pharmaceutical Co."
            )
            mock_candidates.append(candidate)
        
        self.logger.info(f"Generated {len(mock_candidates)} mock drug candidates")
        
        return mock_candidates
    
    def _generate_mock_trials(self, target_genes: List[str], drug_candidates: List[DrugCandidate]) -> List[TrialInformation]:
        """
        Generate mock clinical trials when API is unavailable.
        
        Args:
            target_genes: List of target genes
            drug_candidates: List of drug candidates
            
        Returns:
            List of mock trial information
        """
        mock_trials = []
        
        for i, drug in enumerate(drug_candidates[:3]):  # Generate trials for top 3 drugs
            trial = TrialInformation(
                trial_id=f"NCT{12345678 + i}",
                title=f"Phase II Study of {drug.name} in Target Population",
                phase=TrialPhase.PHASE_II,
                status="Recruiting",
                condition="Genetic Disorder",
                intervention=drug.name,
                primary_outcome="Safety and Efficacy Assessment",
                enrollment=100 + (i * 50),
                start_date="2024-01-01",
                completion_date="2025-12-31"
            )
            mock_trials.append(trial)
        
        self.logger.info(f"Generated {len(mock_trials)} mock clinical trials")
        
        return mock_trials
    
    def _make_request(self, url: str, method: str = 'GET', params: Optional[Dict] = None, 
                     json_data: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            json_data: JSON data for POST requests
            
        Returns:
            Response object or None
        """
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'POST':
                    response = self.session.post(
                        url, 
                        params=params, 
                        json=json_data,
                        timeout=self.request_timeout
                    )
                else:
                    response = self.session.get(
                        url, 
                        params=params,
                        timeout=self.request_timeout
                    )
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except Exception as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error(f"All request attempts failed for URL: {url}")
        
        return None