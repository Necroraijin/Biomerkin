"""
Unit tests for DrugAgent.

Tests drug candidate identification, clinical trial queries, drug interaction analysis,
and effectiveness scoring with mocked API responses.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.models.drug import (
    DrugResults, DrugCandidate, TrialInformation, InteractionAnalysis,
    SideEffect, TrialPhase, DrugType
)


class TestDrugAgent:
    """Test cases for DrugAgent functionality."""
    
    @pytest.fixture
    def drug_agent(self):
        """Create DrugAgent instance for testing."""
        with patch('biomerkin.agents.drug_agent.get_config') as mock_config:
            # Mock configuration
            mock_config.return_value.api.drugbank_api_key = "test_key"
            mock_config.return_value.api.clinicaltrials_api_base_url = "https://clinicaltrials.gov/api"
            mock_config.return_value.api.request_timeout = 30
            mock_config.return_value.api.max_retries = 3
            mock_config.return_value.api.retry_delay = 1.0
            
            agent = DrugAgent()
            return agent
    
    @pytest.fixture
    def sample_target_data(self):
        """Sample target data for testing."""
        return {
            'genes': ['BRCA1', 'TP53'],
            'proteins': ['BRCA1 protein', 'p53 protein'],
            'conditions': ['breast cancer', 'ovarian cancer'],
            'pathways': ['DNA repair pathway']
        }
    
    @pytest.fixture
    def mock_drugbank_response(self):
        """Mock DrugBank API response."""
        return {
            'results': [
                {
                    'drugbank_id': 'DB00001',
                    'name': 'Olaparib',
                    'type': 'small molecule',
                    'mechanism_of_action': 'PARP inhibitor',
                    'status': 'approved',
                    'groups': ['approved'],
                    'targets': [
                        {'name': 'BRCA1'},
                        {'name': 'PARP1'}
                    ],
                    'indication': 'Ovarian cancer',
                    'manufacturer': 'AstraZeneca',
                    'adverse_reactions': [
                        {'name': 'Nausea', 'severity': 'moderate', 'frequency': 'common'},
                        {'name': 'Fatigue', 'severity': 'mild', 'frequency': 'common'}
                    ]
                },
                {
                    'drugbank_id': 'DB00002',
                    'name': 'Talazoparib',
                    'type': 'small molecule',
                    'mechanism_of_action': 'PARP inhibitor',
                    'status': 'approved',
                    'groups': ['approved'],
                    'targets': [
                        {'name': 'BRCA1'},
                        {'name': 'PARP1'}
                    ],
                    'indication': 'Breast cancer',
                    'manufacturer': 'Pfizer'
                }
            ]
        }
    
    @pytest.fixture
    def mock_clinical_trials_response(self):
        """Mock ClinicalTrials.gov API response."""
        return {
            'FullStudiesResponse': {
                'FullStudies': [
                    {
                        'Study': {
                            'ProtocolSection': {
                                'IdentificationModule': {
                                    'NCTId': 'NCT12345678',
                                    'BriefTitle': 'Phase II Study of Olaparib in BRCA-mutated Cancers'
                                },
                                'StatusModule': {
                                    'OverallStatus': 'Recruiting',
                                    'StartDateStruct': {'StartDate': '2024-01-01'},
                                    'CompletionDateStruct': {'CompletionDate': '2025-12-31'}
                                },
                                'DesignModule': {
                                    'PhaseList': {'Phase': ['Phase 2']},
                                    'EnrollmentInfo': {'EnrollmentCount': '150'}
                                },
                                'ConditionsModule': {
                                    'ConditionList': {'Condition': ['Ovarian Cancer']}
                                },
                                'InterventionsModule': {
                                    'InterventionList': {
                                        'Intervention': [
                                            {'InterventionName': 'Olaparib'}
                                        ]
                                    }
                                },
                                'OutcomesModule': {
                                    'PrimaryOutcomeList': {
                                        'PrimaryOutcome': [
                                            {'PrimaryOutcomeMeasure': 'Progression-free survival'}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
    
    def test_initialization(self, drug_agent):
        """Test DrugAgent initialization."""
        assert drug_agent is not None
        assert drug_agent.drugbank_api_key == "test_key"
        assert drug_agent.clinicaltrials_base_url == "https://clinicaltrials.gov/api"
        assert drug_agent.request_timeout == 30
        assert drug_agent.max_retries == 3
    
    @patch('biomerkin.agents.drug_agent.DrugAgent._make_request')
    def test_find_drug_candidates_success(self, mock_request, drug_agent, sample_target_data, 
                                        mock_drugbank_response, mock_clinical_trials_response):
        """Test successful drug candidate identification."""
        # Mock DrugBank API response
        mock_drugbank_resp = Mock()
        mock_drugbank_resp.status_code = 200
        mock_drugbank_resp.json.return_value = mock_drugbank_response
        
        # Mock ClinicalTrials.gov API response
        mock_trials_resp = Mock()
        mock_trials_resp.status_code = 200
        mock_trials_resp.json.return_value = mock_clinical_trials_response
        
        # Configure mock to return different responses based on URL
        def mock_request_side_effect(url, **kwargs):
            if 'drugbank.com' in url:
                return mock_drugbank_resp
            elif 'clinicaltrials.gov' in url:
                return mock_trials_resp
            return None
        
        mock_request.side_effect = mock_request_side_effect
        
        # Test drug candidate identification
        results = drug_agent.find_drug_candidates(sample_target_data)
        
        # Verify results
        assert isinstance(results, DrugResults)
        assert len(results.drug_candidates) > 0
        assert len(results.clinical_trials) > 0
        assert results.target_genes == sample_target_data['genes']
        assert results.analysis_timestamp is not None
        
        # Verify drug candidate properties
        drug = results.drug_candidates[0]
        assert isinstance(drug, DrugCandidate)
        assert drug.drug_id is not None
        assert drug.name is not None
        assert isinstance(drug.drug_type, DrugType)
        assert isinstance(drug.trial_phase, TrialPhase)
        assert 0.0 <= drug.effectiveness_score <= 1.0
        assert isinstance(drug.side_effects, list)
    
    @patch('biomerkin.agents.drug_agent.DrugAgent._search_drugbank_by_target')
    @patch('biomerkin.agents.drug_agent.DrugAgent._search_clinical_trials_by_drug')
    @patch('biomerkin.agents.drug_agent.DrugAgent._search_clinical_trials_by_condition')
    @patch('biomerkin.agents.drug_agent.DrugAgent._search_clinical_trials_by_gene')
    def test_find_drug_candidates_api_failure(self, mock_gene_search, mock_condition_search, 
                                            mock_drug_search, mock_drugbank_search, 
                                            drug_agent, sample_target_data):
        """Test drug candidate identification with API failure (fallback to mock data)."""
        # Mock API failures - return empty lists to trigger fallback
        mock_drugbank_search.return_value = []
        mock_drug_search.return_value = []
        mock_condition_search.return_value = []
        mock_gene_search.return_value = []
        
        # Test drug candidate identification
        results = drug_agent.find_drug_candidates(sample_target_data)
        
        # Verify fallback results
        assert isinstance(results, DrugResults)
        assert len(results.drug_candidates) > 0  # Should have mock candidates
        assert len(results.clinical_trials) > 0  # Should have mock trials
        assert results.target_genes == sample_target_data['genes']
    
    def test_classify_drug_type(self, drug_agent):
        """Test drug type classification."""
        # Test antibody classification
        drug_data = {'type': 'antibody', 'name': 'Trastuzumab'}
        drug_type = drug_agent._classify_drug_type(drug_data)
        assert drug_type == DrugType.ANTIBODY
        
        # Test small molecule classification
        drug_data = {'type': 'small molecule', 'name': 'Aspirin'}
        drug_type = drug_agent._classify_drug_type(drug_data)
        assert drug_type == DrugType.SMALL_MOLECULE
        
        # Test biologic classification
        drug_data = {'type': 'biologic', 'name': 'Insulin'}
        drug_type = drug_agent._classify_drug_type(drug_data)
        assert drug_type == DrugType.BIOLOGIC
        
        # Test vaccine classification
        drug_data = {'type': 'vaccine', 'name': 'COVID-19 vaccine'}
        drug_type = drug_agent._classify_drug_type(drug_data)
        assert drug_type == DrugType.VACCINE
    
    def test_determine_trial_phase(self, drug_agent):
        """Test trial phase determination."""
        # Test approved drug
        drug_data = {'status': 'approved', 'groups': ['approved']}
        phase = drug_agent._determine_trial_phase(drug_data)
        assert phase == TrialPhase.APPROVED
        
        # Test Phase III
        drug_data = {'status': 'phase 3 trial'}
        phase = drug_agent._determine_trial_phase(drug_data)
        assert phase == TrialPhase.PHASE_III
        
        # Test Phase II
        drug_data = {'status': 'phase ii trial'}
        phase = drug_agent._determine_trial_phase(drug_data)
        assert phase == TrialPhase.PHASE_II
        
        # Test withdrawn
        drug_data = {'status': 'withdrawn'}
        phase = drug_agent._determine_trial_phase(drug_data)
        assert phase == TrialPhase.WITHDRAWN
    
    def test_calculate_effectiveness_score(self, drug_agent):
        """Test effectiveness score calculation."""
        # Test approved drug with multiple targets
        drug_data = {
            'status': 'approved',
            'groups': ['approved'],
            'targets': [{'name': 'target1'}, {'name': 'target2'}],
            'efficacy_data': True
        }
        score = drug_agent._calculate_effectiveness_score(drug_data)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be higher than base score
        
        # Test investigational drug
        drug_data = {'status': 'investigational', 'targets': []}
        score = drug_agent._calculate_effectiveness_score(drug_data)
        assert 0.0 <= score <= 1.0
    
    def test_extract_side_effects(self, drug_agent):
        """Test side effect extraction."""
        drug_data = {
            'adverse_reactions': [
                {'name': 'Nausea', 'severity': 'moderate', 'frequency': 'common'},
                {'name': 'Headache', 'severity': 'mild', 'frequency': 'uncommon'},
                'Fatigue'  # Test string format
            ]
        }
        
        side_effects = drug_agent._extract_side_effects(drug_data)
        
        assert len(side_effects) == 3
        assert all(isinstance(effect, SideEffect) for effect in side_effects)
        assert side_effects[0].name == 'Nausea'
        assert side_effects[0].severity == 'moderate'
        assert side_effects[0].frequency == 'common'
        assert side_effects[2].name == 'Fatigue'
    
    def test_parse_trial_phase(self, drug_agent):
        """Test trial phase parsing."""
        assert drug_agent._parse_trial_phase('Phase 4') == TrialPhase.PHASE_IV
        assert drug_agent._parse_trial_phase('Phase III') == TrialPhase.PHASE_III
        assert drug_agent._parse_trial_phase('Phase 2') == TrialPhase.PHASE_II
        assert drug_agent._parse_trial_phase('Phase I') == TrialPhase.PHASE_I
        assert drug_agent._parse_trial_phase('Phase 0') == TrialPhase.PHASE_0
        assert drug_agent._parse_trial_phase('Not Applicable') == TrialPhase.PRECLINICAL
    
    def test_parse_clinical_trial(self, drug_agent, mock_clinical_trials_response):
        """Test clinical trial data parsing."""
        study_data = mock_clinical_trials_response['FullStudiesResponse']['FullStudies'][0]
        
        trial = drug_agent._parse_clinical_trial(study_data)
        
        assert isinstance(trial, TrialInformation)
        assert trial.trial_id == 'NCT12345678'
        assert trial.title == 'Phase II Study of Olaparib in BRCA-mutated Cancers'
        assert trial.phase == TrialPhase.PHASE_II
        assert trial.status == 'Recruiting'
        assert trial.condition == 'Ovarian Cancer'
        assert trial.intervention == 'Olaparib'
        assert trial.enrollment == 150
    
    def test_analyze_drug_interactions(self, drug_agent):
        """Test drug interaction analysis."""
        drugs = ['Drug A', 'Drug B', 'Drug C']
        
        analysis = drug_agent.analyze_drug_interactions(drugs)
        
        assert isinstance(analysis, InteractionAnalysis)
        assert len(analysis.drug_pairs) == 3  # 3 choose 2 = 3 pairs
        assert analysis.interaction_severity in ['low', 'moderate', 'high']
        assert analysis.interaction_type is not None
        assert analysis.clinical_significance is not None
        assert isinstance(analysis.recommendations, list)
        assert len(analysis.recommendations) > 0
    
    def test_assess_interaction_severity(self, drug_agent):
        """Test interaction severity assessment."""
        # Test high severity (many pairs)
        many_pairs = [('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'C')]
        severity = drug_agent._assess_interaction_severity(many_pairs)
        assert severity == 'high'
        
        # Test moderate severity
        few_pairs = [('A', 'B'), ('A', 'C')]
        severity = drug_agent._assess_interaction_severity(few_pairs)
        assert severity == 'moderate'
        
        # Test low severity
        one_pair = [('A', 'B')]
        severity = drug_agent._assess_interaction_severity(one_pair)
        assert severity == 'low'
    
    def test_generate_interaction_recommendations(self, drug_agent):
        """Test interaction recommendation generation."""
        drug_pairs = [('Drug A', 'Drug B')]
        
        # Test high severity recommendations
        recommendations = drug_agent._generate_interaction_recommendations(drug_pairs, 'high')
        assert len(recommendations) > 0
        assert any('alternative medications' in rec.lower() for rec in recommendations)
        
        # Test moderate severity recommendations
        recommendations = drug_agent._generate_interaction_recommendations(drug_pairs, 'moderate')
        assert len(recommendations) > 0
        assert any('monitor' in rec.lower() for rec in recommendations)
        
        # Test low severity recommendations
        recommendations = drug_agent._generate_interaction_recommendations(drug_pairs, 'low')
        assert len(recommendations) > 0
    
    def test_generate_mock_drug_candidates(self, drug_agent):
        """Test mock drug candidate generation."""
        target_genes = ['BRCA1', 'TP53']
        target_proteins = ['BRCA1 protein']
        
        candidates = drug_agent._generate_mock_drug_candidates(target_genes, target_proteins)
        
        assert len(candidates) > 0
        assert all(isinstance(candidate, DrugCandidate) for candidate in candidates)
        assert all(candidate.drug_id.startswith('MOCK_') for candidate in candidates)
        assert all(len(candidate.side_effects) > 0 for candidate in candidates)
    
    def test_generate_mock_trials(self, drug_agent):
        """Test mock clinical trial generation."""
        target_genes = ['BRCA1']
        drug_candidates = [
            DrugCandidate(
                drug_id='TEST001',
                name='Test Drug',
                drug_type=DrugType.SMALL_MOLECULE,
                mechanism_of_action='Test mechanism',
                target_proteins=['BRCA1'],
                trial_phase=TrialPhase.PHASE_II,
                effectiveness_score=0.7,
                side_effects=[]
            )
        ]
        
        trials = drug_agent._generate_mock_trials(target_genes, drug_candidates)
        
        assert len(trials) > 0
        assert all(isinstance(trial, TrialInformation) for trial in trials)
        assert all(trial.trial_id.startswith('NCT') for trial in trials)
        assert all(trial.phase == TrialPhase.PHASE_II for trial in trials)
    
    @patch('biomerkin.agents.drug_agent.DrugAgent._make_request')
    def test_get_trial_information(self, mock_request, drug_agent, mock_clinical_trials_response):
        """Test getting trial information for specific drug."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_clinical_trials_response
        mock_request.return_value = mock_resp
        
        trials = drug_agent.get_trial_information('Olaparib')
        
        assert len(trials) > 0
        assert all(isinstance(trial, TrialInformation) for trial in trials)
    
    @patch('requests.Session.get')
    @patch('requests.Session.post')
    def test_make_request_retry_logic(self, mock_post, mock_get, drug_agent):
        """Test request retry logic with failures."""
        # Mock rate limiting response
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        
        # Mock successful response
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'data': 'test'}
        
        # Configure mock to fail first, then succeed
        mock_get.side_effect = [rate_limit_response, success_response]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = drug_agent._make_request('http://test.com')
        
        assert response is not None
        assert response.status_code == 200
        assert mock_get.call_count == 2
    
    @patch('biomerkin.agents.drug_agent.requests.Session.get')
    def test_make_request_all_retries_fail(self, mock_get, drug_agent):
        """Test request when all retries fail."""
        # Mock all requests to fail
        mock_get.side_effect = Exception("Connection error")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = drug_agent._make_request('http://test.com')
        
        assert response is None
        assert mock_get.call_count == drug_agent.max_retries
    
    def test_score_drug_candidates(self, drug_agent):
        """Test drug candidate scoring and ranking."""
        candidates = [
            DrugCandidate(
                drug_id='DRUG1',
                name='Drug 1',
                drug_type=DrugType.SMALL_MOLECULE,
                mechanism_of_action='Mechanism 1',
                target_proteins=['BRCA1'],
                trial_phase=TrialPhase.APPROVED,
                effectiveness_score=0.5,
                side_effects=[]
            ),
            DrugCandidate(
                drug_id='DRUG2',
                name='Drug 2',
                drug_type=DrugType.SMALL_MOLECULE,
                mechanism_of_action='Mechanism 2',
                target_proteins=['TP53'],
                trial_phase=TrialPhase.PHASE_II,
                effectiveness_score=0.3,
                side_effects=[]
            )
        ]
        
        targets = ['BRCA1', 'TP53']
        scored_candidates = drug_agent._score_drug_candidates(candidates, targets)
        
        # Verify scoring and sorting
        assert len(scored_candidates) == 2
        assert scored_candidates[0].effectiveness_score >= scored_candidates[1].effectiveness_score
        
        # Verify target match bonus was applied
        brca1_candidate = next(c for c in scored_candidates if 'BRCA1' in c.target_proteins)
        assert brca1_candidate.effectiveness_score > 0.5  # Should have bonus
    
    def test_drug_candidate_serialization(self):
        """Test DrugCandidate serialization and deserialization."""
        side_effects = [
            SideEffect(name="Nausea", severity="moderate", frequency="common"),
            SideEffect(name="Fatigue", severity="mild", frequency="uncommon")
        ]
        
        candidate = DrugCandidate(
            drug_id='TEST001',
            name='Test Drug',
            drug_type=DrugType.ANTIBODY,
            mechanism_of_action='Test mechanism',
            target_proteins=['Target1', 'Target2'],
            trial_phase=TrialPhase.PHASE_III,
            effectiveness_score=0.85,
            side_effects=side_effects,
            indication='Test indication',
            manufacturer='Test Pharma'
        )
        
        # Test serialization
        data = candidate.to_dict()
        assert data['drug_id'] == 'TEST001'
        assert data['drug_type'] == 'antibody'
        assert data['trial_phase'] == 'phase_3'
        assert len(data['side_effects']) == 2
        
        # Test deserialization
        restored_candidate = DrugCandidate.from_dict(data)
        assert restored_candidate.drug_id == candidate.drug_id
        assert restored_candidate.drug_type == candidate.drug_type
        assert restored_candidate.trial_phase == candidate.trial_phase
        assert len(restored_candidate.side_effects) == len(candidate.side_effects)
    
    def test_trial_information_serialization(self):
        """Test TrialInformation serialization and deserialization."""
        trial = TrialInformation(
            trial_id='NCT12345678',
            title='Test Trial',
            phase=TrialPhase.PHASE_II,
            status='Recruiting',
            condition='Test Condition',
            intervention='Test Drug',
            primary_outcome='Safety and Efficacy',
            enrollment=150,
            start_date='2024-01-01',
            completion_date='2025-12-31'
        )
        
        # Test serialization
        data = trial.to_dict()
        assert data['trial_id'] == 'NCT12345678'
        assert data['phase'] == 'phase_2'
        
        # Test deserialization
        restored_trial = TrialInformation.from_dict(data)
        assert restored_trial.trial_id == trial.trial_id
        assert restored_trial.phase == trial.phase
        assert restored_trial.enrollment == trial.enrollment
    
    def test_drug_results_serialization(self):
        """Test DrugResults serialization and deserialization."""
        candidate = DrugCandidate(
            drug_id='TEST001',
            name='Test Drug',
            drug_type=DrugType.SMALL_MOLECULE,
            mechanism_of_action='Test mechanism',
            target_proteins=['Target1'],
            trial_phase=TrialPhase.APPROVED,
            effectiveness_score=0.8,
            side_effects=[]
        )
        
        trial = TrialInformation(
            trial_id='NCT12345678',
            title='Test Trial',
            phase=TrialPhase.PHASE_II,
            status='Recruiting',
            condition='Test Condition',
            intervention='Test Drug'
        )
        
        interaction_analysis = InteractionAnalysis(
            drug_pairs=[('Drug A', 'Drug B')],
            interaction_severity='moderate',
            interaction_type='pharmacokinetic',
            clinical_significance='Monitor patient',
            recommendations=['Monitor closely']
        )
        
        results = DrugResults(
            target_genes=['GENE1'],
            drug_candidates=[candidate],
            clinical_trials=[trial],
            interaction_analysis=interaction_analysis,
            analysis_timestamp='2024-01-01T00:00:00'
        )
        
        # Test serialization
        data = results.to_dict()
        assert data['target_genes'] == ['GENE1']
        assert len(data['drug_candidates']) == 1
        assert len(data['clinical_trials']) == 1
        assert data['interaction_analysis'] is not None
        
        # Test deserialization
        restored_results = DrugResults.from_dict(data)
        assert restored_results.target_genes == results.target_genes
        assert len(restored_results.drug_candidates) == len(results.drug_candidates)
        assert len(restored_results.clinical_trials) == len(results.clinical_trials)
        assert restored_results.interaction_analysis is not None


if __name__ == '__main__':
    pytest.main([__file__])