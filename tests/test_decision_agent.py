"""
Unit tests for DecisionAgent.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from biomerkin.agents.decision_agent import DecisionAgent, BedrockClient
from biomerkin.models.analysis import CombinedAnalysis
from biomerkin.models.genomics import GenomicsResults, Gene, Mutation, MutationType, ProteinSequence, QualityMetrics
from biomerkin.models.proteomics import ProteomicsResults, FunctionAnnotation, ProteinDomain, ProteinInteraction
from biomerkin.models.literature import LiteratureResults, LiteratureSummary, Article, StudySummary
from biomerkin.models.drug import DrugResults, DrugCandidate, SideEffect, TrialPhase, DrugType
from biomerkin.models.medical import (
    MedicalReport, RiskAssessment, RiskLevel, RiskFactor, 
    TreatmentOption, TreatmentType, DrugRecommendation
)
from biomerkin.models.base import GenomicLocation


class TestBedrockClient:
    """Test cases for BedrockClient."""
    
    @patch('boto3.client')
    def test_bedrock_client_initialization_success(self, mock_boto_client):
        """Test successful Bedrock client initialization."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        bedrock_client = BedrockClient(region="us-east-1")
        
        assert bedrock_client.client == mock_client
        assert bedrock_client.region == "us-east-1"
        mock_boto_client.assert_called_once_with('bedrock-runtime', region_name="us-east-1")
    
    @patch('boto3.client')
    def test_bedrock_client_initialization_failure(self, mock_boto_client):
        """Test Bedrock client initialization failure."""
        mock_boto_client.side_effect = Exception("AWS credentials not found")
        
        bedrock_client = BedrockClient()
        
        assert bedrock_client.client is None
    
    @patch('boto3.client')
    def test_generate_text_anthropic_success(self, mock_boto_client):
        """Test successful text generation with Anthropic model."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = b'{"content": [{"text": "Generated medical report text"}]}'
        mock_client.invoke_model.return_value = mock_response
        
        bedrock_client = BedrockClient(model_id="anthropic.claude-3-sonnet-20240229-v1:0")
        result = bedrock_client.generate_text("Test prompt")
        
        assert result == "Generated medical report text"
        mock_client.invoke_model.assert_called_once()
    
    @patch('boto3.client')
    def test_generate_text_other_model_success(self, mock_boto_client):
        """Test successful text generation with non-Anthropic model."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        # Mock response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = b'{"results": [{"outputText": "Generated text"}]}'
        mock_client.invoke_model.return_value = mock_response
        
        bedrock_client = BedrockClient(model_id="amazon.titan-text-express-v1")
        result = bedrock_client.generate_text("Test prompt")
        
        assert result == "Generated text"
    
    @patch('boto3.client')
    def test_generate_text_failure(self, mock_boto_client):
        """Test text generation failure."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.invoke_model.side_effect = Exception("API error")
        
        bedrock_client = BedrockClient()
        result = bedrock_client.generate_text("Test prompt")
        
        assert result is None
    
    def test_generate_text_no_client(self):
        """Test text generation when client is not initialized."""
        with patch('boto3.client', side_effect=Exception("No credentials")):
            bedrock_client = BedrockClient()
            result = bedrock_client.generate_text("Test prompt")
            
            assert result is None


class TestDecisionAgent:
    """Test cases for DecisionAgent."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.aws.region = "us-east-1"
        config.aws.bedrock_model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        return config
    
    @pytest.fixture
    def sample_genomics_results(self):
        """Sample genomics results for testing."""
        genes = [
            Gene(
                id="GENE001",
                name="BRCA1",
                location=GenomicLocation(chromosome="17", start_position=43044295, end_position=43125483),
                function="Tumor suppressor gene involved in DNA repair",
                confidence_score=0.95,
                synonyms=["BRCA1", "BRCAI"]
            ),
            Gene(
                id="GENE002", 
                name="CYP2D6",
                location=GenomicLocation(chromosome="22", start_position=42522500, end_position=42531000),
                function="Cytochrome P450 enzyme involved in drug metabolism",
                confidence_score=0.88,
                synonyms=["CYP2D6"]
            )
        ]
        
        mutations = [
            Mutation(
                position=43045677,
                reference_base="C",
                alternate_base="T",
                mutation_type=MutationType.SNP,
                gene_id="GENE001",
                clinical_significance="Pathogenic"
            ),
            Mutation(
                position=42526694,
                reference_base="G",
                alternate_base="A", 
                mutation_type=MutationType.SNP,
                gene_id="GENE002",
                clinical_significance="Benign"
            )
        ]
        
        protein_sequences = [
            ProteinSequence(
                sequence="MDFQVDLTKQVKGQGVPINTNSSPDDQIGYYRRATRRIRGGDGKMKDLSPRWYFYYLGTGPEAGLPYGANKDGIIWVATEGALNTPKDHIGTRNPANNAAIVLQLPQGTTLPKGFYAEGSRGGSQASSRSSSRSRNSSRNSTPGSSRGTSPARMAGNGGDAALALLLLDRLNQLESKMSGKGQQQQGQTVTKKSAAEASKKPRQKRTATKAYNVTQAFGRRGPEQTQGNFGDQELIRQGTDYKHWPQIAQFAPSASAFFGMSRIGMEVTPSGTWLTYTGAIKLDDKDPNFKDQVILLNKHIDAYKTFPPTEPKKDKKKKADETQALPQRQKKQQTVTLLPAADLDDFSKQLQQSMSSADSTQA",
                gene_id="GENE001",
                length=1863,
                molecular_weight=207721.0
            )
        ]
        
        quality_metrics = QualityMetrics(
            coverage_depth=0.95,
            quality_score=0.92,
            confidence_level=0.89
        )
        
        return GenomicsResults(
            genes=genes,
            mutations=mutations,
            protein_sequences=protein_sequences,
            quality_metrics=quality_metrics
        )
    
    @pytest.fixture
    def sample_proteomics_results(self):
        """Sample proteomics results for testing."""
        functional_annotations = [
            FunctionAnnotation(
                function_type="molecular_function",
                description="DNA repair protein involved in homologous recombination",
                confidence_score=0.92,
                source="UniProt",
                evidence_code="IDA"
            )
        ]
        
        domains = [
            ProteinDomain(
                domain_id="PF00533",
                name="BRCT domain",
                start_position=1650,
                end_position=1863,
                description="BRCA1 C-terminal domain involved in protein-protein interactions"
            )
        ]
        
        interactions = [
            ProteinInteraction(
                partner_protein_id="BARD1",
                interaction_type="Physical",
                confidence_score=0.95,
                source_database="BioGRID"
            )
        ]
        
        return ProteomicsResults(
            protein_id="P38398",
            structure_data=None,
            functional_annotations=functional_annotations,
            domains=domains,
            interactions=interactions
        )
    
    @pytest.fixture
    def sample_literature_results(self):
        """Sample literature results for testing."""
        articles = [
            Article(
                pmid="12345678",
                title="BRCA1 mutations and breast cancer risk",
                authors=["Smith J", "Doe A"],
                journal="Nature Genetics",
                publication_date="2023-01",
                abstract="Study of BRCA1 mutations in breast cancer patients...",
                doi="10.1038/ng.2023.001",
                relevance_score=0.95
            )
        ]
        
        study_summaries = [
            StudySummary(
                study_type="Cohort Study",
                key_findings=["BRCA1 mutations increase breast cancer risk by 5-fold"],
                sample_size=10000,
                statistical_significance="p < 0.001",
                limitations=["Limited ethnic diversity"]
            )
        ]
        
        summary = LiteratureSummary(
            search_terms=["BRCA1", "breast cancer", "mutation"],
            total_articles_found=150,
            articles_analyzed=25,
            key_findings=[
                "BRCA1 mutations significantly increase breast cancer risk",
                "Early screening recommended for carriers",
                "Preventive surgery options available"
            ],
            relevant_studies=study_summaries,
            research_gaps=["Limited data on non-European populations"],
            confidence_level=0.85,
            analysis_timestamp="2024-01-15T10:30:00"
        )
        
        return LiteratureResults(
            articles=articles,
            summary=summary,
            search_metadata={"search_terms_used": ["BRCA1"], "articles_found": 150}
        )
    
    @pytest.fixture
    def sample_drug_results(self):
        """Sample drug results for testing."""
        side_effects = [
            SideEffect(
                name="Nausea",
                frequency="Common",
                severity="Mild"
            )
        ]
        
        drug_candidates = [
            DrugCandidate(
                drug_id="DB00001",
                name="Olaparib",
                drug_type=DrugType.SMALL_MOLECULE,
                mechanism_of_action="PARP inhibitor",
                target_proteins=["BRCA1", "BRCA2"],
                trial_phase=TrialPhase.PHASE_III,
                effectiveness_score=0.85,
                side_effects=side_effects
            )
        ]
        
        return DrugResults(
            target_genes=["BRCA1", "BRCA2"],
            drug_candidates=drug_candidates,
            clinical_trials=[],
            interaction_analysis=None
        )
    
    @pytest.fixture
    def sample_combined_analysis(self, sample_genomics_results, sample_proteomics_results, 
                               sample_literature_results, sample_drug_results):
        """Sample combined analysis for testing."""
        return CombinedAnalysis(
            workflow_id="WF_12345678",
            genomics_results=sample_genomics_results,
            proteomics_results=sample_proteomics_results,
            literature_results=sample_literature_results,
            drug_results=sample_drug_results,
            medical_report=None,
            analysis_start_time=datetime.now(),
            analysis_end_time=datetime.now(),
            total_processing_time=120.5
        )
    
    def test_decision_agent_initialization(self, mock_config):
        """Test DecisionAgent initialization."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent(config=mock_config)
            
            assert agent.config == mock_config
            assert agent.bedrock_client is not None
    
    @patch('biomerkin.utils.config.get_config')
    @patch('boto3.client')
    def test_generate_medical_report_success(self, mock_boto_client, mock_get_config, 
                                           mock_config, sample_combined_analysis):
        """Test successful medical report generation."""
        mock_get_config.return_value = mock_config
        
        # Mock Bedrock client
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_response = {'body': Mock()}
        mock_response['body'].read.return_value = b'{"content": [{"text": "AI generated report section"}]}'
        mock_client.invoke_model.return_value = mock_response
        
        agent = DecisionAgent()
        report = agent.generate_medical_report(sample_combined_analysis, "PAT_001")
        
        assert isinstance(report, MedicalReport)
        assert report.patient_id == "PAT_001"
        assert report.report_id.startswith("RPT_")
        assert len(report.drug_recommendations) > 0
        assert len(report.treatment_options) > 0
        assert isinstance(report.risk_assessment, RiskAssessment)
        assert len(report.clinical_recommendations) > 0
        assert len(report.follow_up_recommendations) > 0
    
    def test_aggregate_analysis_data(self, mock_config, sample_combined_analysis):
        """Test data aggregation from combined analysis."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            aggregated = agent._aggregate_analysis_data(sample_combined_analysis)
            
            assert 'genes_analyzed' in aggregated
            assert 'mutations_found' in aggregated
            assert 'protein_functions' in aggregated
            assert 'drug_candidates' in aggregated
            assert 'literature_findings' in aggregated
            assert 'analysis_quality' in aggregated
            
            assert len(aggregated['genes_analyzed']) == 2
            assert len(aggregated['mutations_found']) == 2
            assert len(aggregated['drug_candidates']) == 1
    
    def test_assess_genetic_risks_high_risk(self, mock_config, sample_genomics_results):
        """Test genetic risk assessment with high-risk mutations."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            risk_assessment = agent._assess_genetic_risks(sample_genomics_results, None)
            
            assert isinstance(risk_assessment, RiskAssessment)
            assert risk_assessment.overall_risk_level == RiskLevel.HIGH
            assert len(risk_assessment.risk_factors) > 0
            assert risk_assessment.confidence_score > 0.5
            
            # Check for pathogenic mutation risk factor
            pathogenic_factors = [rf for rf in risk_assessment.risk_factors 
                                if 'pathogenic' in rf.factor_name.lower()]
            assert len(pathogenic_factors) > 0
    
    def test_assess_genetic_risks_no_data(self, mock_config):
        """Test genetic risk assessment with no genomics data."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            risk_assessment = agent._assess_genetic_risks(None, None)
            
            assert risk_assessment.overall_risk_level == RiskLevel.LOW
            assert len(risk_assessment.risk_factors) == 0
            assert risk_assessment.confidence_score == 0.1
    
    def test_generate_drug_recommendations(self, mock_config, sample_drug_results, 
                                         sample_genomics_results):
        """Test drug recommendation generation."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            # Create mock risk assessment
            risk_assessment = RiskAssessment(
                overall_risk_level=RiskLevel.HIGH,
                risk_factors=[],
                protective_factors=[],
                recommendations=[],
                confidence_score=0.8
            )
            
            recommendations = agent._generate_drug_recommendations(
                sample_drug_results, sample_genomics_results, risk_assessment
            )
            
            assert len(recommendations) > 0
            assert isinstance(recommendations[0], DrugRecommendation)
            assert recommendations[0].drug_name == "Olaparib"
            assert "PARP inhibitor" in recommendations[0].rationale
    
    def test_generate_drug_recommendations_no_data(self, mock_config):
        """Test drug recommendation generation with no drug data."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            risk_assessment = RiskAssessment(
                overall_risk_level=RiskLevel.LOW,
                risk_factors=[],
                protective_factors=[],
                recommendations=[],
                confidence_score=0.5
            )
            
            recommendations = agent._generate_drug_recommendations(None, None, risk_assessment)
            
            assert len(recommendations) == 1
            assert "No specific drugs identified" in recommendations[0].drug_name
    
    def test_generate_treatment_options(self, mock_config, sample_combined_analysis):
        """Test treatment options generation."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            risk_assessment = RiskAssessment(
                overall_risk_level=RiskLevel.HIGH,
                risk_factors=[],
                protective_factors=[],
                recommendations=[],
                confidence_score=0.8
            )
            
            treatment_options = agent._generate_treatment_options(sample_combined_analysis, risk_assessment)
            
            assert len(treatment_options) > 0
            
            # Check for different treatment types
            treatment_types = [option.treatment_type for option in treatment_options]
            assert TreatmentType.MEDICATION in treatment_types
            assert TreatmentType.GENETIC_COUNSELING in treatment_types
            assert TreatmentType.PREVENTIVE in treatment_types
            assert TreatmentType.LIFESTYLE in treatment_types
            assert TreatmentType.MONITORING in treatment_types
    
    def test_determine_dosage_recommendation_metabolic_genes(self, mock_config, sample_genomics_results):
        """Test dosage recommendation with metabolic gene variants."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            # Create mock drug candidate
            drug = DrugCandidate(
                drug_id="DB00001",
                name="Test Drug",
                drug_type=DrugType.SMALL_MOLECULE,
                mechanism_of_action="Test mechanism",
                target_proteins=[],
                trial_phase=TrialPhase.PHASE_III,
                effectiveness_score=0.8,
                side_effects=[]
            )
            
            dosage_rec = agent._determine_dosage_recommendation(drug, sample_genomics_results)
            
            # Should recommend enhanced monitoring due to CYP2D6 gene
            assert "monitoring" in dosage_rec.lower() or "standard" in dosage_rec.lower()
    
    def test_generate_clinical_recommendations(self, mock_config, sample_combined_analysis):
        """Test clinical recommendations generation."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            risk_assessment = RiskAssessment(
                overall_risk_level=RiskLevel.HIGH,
                risk_factors=[],
                protective_factors=[],
                recommendations=[],
                confidence_score=0.8
            )
            
            recommendations = agent._generate_clinical_recommendations(sample_combined_analysis, risk_assessment)
            
            assert len(recommendations) > 0
            assert any("genetic counselor" in rec.lower() for rec in recommendations)
            assert any("screening" in rec.lower() for rec in recommendations)
    
    def test_generate_follow_up_recommendations(self, mock_config):
        """Test follow-up recommendations generation."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            risk_assessment = RiskAssessment(
                overall_risk_level=RiskLevel.HIGH,
                risk_factors=[],
                protective_factors=[],
                recommendations=[],
                confidence_score=0.8
            )
            
            treatment_options = [
                TreatmentOption(
                    treatment_id="MED_001",
                    name="Test Treatment",
                    treatment_type=TreatmentType.MEDICATION,
                    description="Test description",
                    effectiveness_rating=0.8,
                    evidence_level="B",
                    contraindications=[],
                    monitoring_requirements=[]
                )
            ]
            
            follow_up = agent._generate_follow_up_recommendations(risk_assessment, treatment_options)
            
            assert len(follow_up) > 0
            assert any("3-6 months" in rec for rec in follow_up)  # High risk follow-up
            assert any("medication" in rec.lower() for rec in follow_up)  # Medication monitoring
    
    def test_fallback_methods(self, mock_config):
        """Test fallback methods when AI is not available."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            # Test data
            aggregated_data = {
                'genes_analyzed': [{'name': 'BRCA1', 'function': 'DNA repair', 'confidence': 0.9}],
                'mutations_found': [{'type': 'SNV', 'position': 12345, 'significance': 'Pathogenic', 'reference': 'C', 'alternate': 'T'}],
                'protein_functions': [{'description': 'DNA repair protein', 'confidence': 0.8, 'source': 'UniProt'}],
                'literature_findings': ['BRCA1 mutations increase cancer risk']
            }
            
            # Test fallback methods
            summary = agent._generate_fallback_summary(aggregated_data)
            genetic_findings = agent._generate_fallback_genetic_findings(aggregated_data)
            protein_analysis = agent._generate_fallback_protein_analysis(aggregated_data)
            literature_insights = agent._generate_fallback_literature_insights(aggregated_data)
            
            assert len(summary) > 0
            assert "BRCA1" in genetic_findings
            assert "DNA repair protein" in protein_analysis
            assert "BRCA1 mutations increase cancer risk" in literature_insights
    
    def test_create_error_report(self, mock_config):
        """Test error report creation."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            error_report = agent._create_error_report("PAT_001", "Test error message")
            
            assert isinstance(error_report, MedicalReport)
            assert error_report.patient_id == "PAT_001"
            assert error_report.report_id.startswith("ERR_")
            assert "Test error message" in error_report.analysis_summary
            assert error_report.risk_assessment.confidence_score == 0.0
    
    @patch('biomerkin.utils.config.get_config')
    @patch('boto3.client')
    def test_generate_medical_report_with_ai_failure(self, mock_boto_client, mock_get_config, 
                                                   mock_config, sample_combined_analysis):
        """Test medical report generation when AI fails."""
        mock_get_config.return_value = mock_config
        
        # Mock Bedrock client to fail
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.invoke_model.side_effect = Exception("AI service unavailable")
        
        agent = DecisionAgent()
        report = agent.generate_medical_report(sample_combined_analysis, "PAT_001")
        
        # Should still generate report with fallback methods
        assert isinstance(report, MedicalReport)
        assert report.patient_id == "PAT_001"
        assert len(report.analysis_summary) > 0  # Should have fallback content
    
    def test_prepare_ai_context(self, mock_config):
        """Test AI context preparation."""
        with patch('biomerkin.utils.config.get_config', return_value=mock_config), \
             patch('boto3.client'):
            agent = DecisionAgent()
            
            aggregated_data = {
                'genes_analyzed': [{'name': 'BRCA1', 'function': 'DNA repair', 'confidence': 0.9}],
                'mutations_found': [{'type': 'SNV', 'position': 12345, 'significance': 'Pathogenic'}],
                'protein_functions': [{'description': 'DNA repair protein'}],
                'drug_candidates': [{'name': 'Olaparib'}],
                'literature_findings': ['Key finding 1', 'Key finding 2']
            }
            
            context = agent._prepare_ai_context(aggregated_data)
            
            assert "Genes analyzed: 1 genes" in context
            assert "BRCA1" in context
            assert "Mutations identified: 1 variants" in context
            assert "Protein functions: 1 annotations" in context
            assert "Drug candidates: 1 identified" in context
            assert "Literature findings: 2 key insights" in context


if __name__ == "__main__":
    pytest.main([__file__])