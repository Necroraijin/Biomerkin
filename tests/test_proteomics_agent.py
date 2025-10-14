"""
Unit tests for ProteomicsAgent.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import requests

from biomerkin.agents.proteomics_agent import ProteomicsAgent
from biomerkin.models.proteomics import (
    ProteomicsResults, ProteinStructure, FunctionAnnotation, 
    ProteinDomain, ProteinInteraction
)


class TestProteomicsAgent:
    """Test cases for ProteomicsAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ProteomicsAgent()
        
        # Sample protein sequence (insulin A chain)
        self.sample_protein = "GIVEQCCTSICSLYQLENYCN"
        
        # Sample PDB ID
        self.sample_pdb_id = "1ZNI"
        
        # Sample UniProt ID
        self.sample_uniprot_id = "P01308"
        
        # Mock PDB API response
        self.mock_pdb_response = {
            "exptl": [{"method": "X-RAY DIFFRACTION"}],
            "refine": [{"ls_d_res_high": 1.8}],
            "struct_conf": [{"conf_type_id": "HELX_P"}]
        }
        
        # Mock UniProt API response
        self.mock_uniprot_response = {
            "proteinDescription": {
                "recommendedName": {
                    "fullName": {"value": "Insulin"}
                }
            },
            "uniProtKBCrossReferences": [
                {
                    "database": "GO",
                    "properties": [
                        {"key": "GoTerm", "value": "P:hormone activity"}
                    ]
                }
            ]
        }
        
        # Mock STRING API response
        self.mock_string_response = [
            {
                "preferredName_B": "INSR",
                "score": 900,
                "experimentally_determined_interaction": "yes"
            }
        ]
    
    def test_init(self):
        """Test ProteomicsAgent initialization."""
        agent = ProteomicsAgent()
        assert agent.pdb_base_url is not None
        assert agent.request_timeout > 0
        assert agent.max_retries > 0
        assert agent.session is not None
    
    def test_is_pdb_id_valid(self):
        """Test PDB ID validation."""
        assert self.agent._is_pdb_id("1ZNI") == True
        assert self.agent._is_pdb_id("2ABC") == True
        assert self.agent._is_pdb_id("invalid") == False
        assert self.agent._is_pdb_id("12345") == False
        assert self.agent._is_pdb_id("") == False
    
    def test_is_uniprot_id_valid(self):
        """Test UniProt ID validation."""
        assert self.agent._is_uniprot_id("P01308") == True
        assert self.agent._is_uniprot_id("Q9Y6K9") == True
        assert self.agent._is_uniprot_id("invalid") == False
        assert self.agent._is_uniprot_id("123") == False
        assert self.agent._is_uniprot_id("") == False   
 
    @patch('requests.Session.get')
    def test_query_pdb_structure_success(self, mock_get):
        """Test successful PDB structure query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_pdb_response
        mock_get.return_value = mock_response
        
        structure = self.agent._query_pdb_structure(self.sample_pdb_id)
        
        assert structure is not None
        assert structure.pdb_id == self.sample_pdb_id.upper()
        assert structure.structure_method == "X-RAY DIFFRACTION"
        assert structure.resolution == 1.8
        # Called twice: once for structure info, once for secondary structure
        assert mock_get.call_count == 2
    
    @patch('requests.Session.get')
    def test_query_pdb_structure_failure(self, mock_get):
        """Test PDB structure query failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        structure = self.agent._query_pdb_structure("INVALID")
        
        assert structure is None
        mock_get.assert_called_once()
    
    @patch('requests.Session.post')
    def test_search_pdb_by_sequence(self, mock_post):
        """Test PDB sequence search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result_set": ["1ZNI", "2ABC"]}
        mock_post.return_value = mock_response
        
        pdb_ids = self.agent._search_pdb_by_sequence(self.sample_protein)
        
        assert len(pdb_ids) == 2
        assert "1ZNI" in pdb_ids
        assert "2ABC" in pdb_ids
        mock_post.assert_called_once()
    
    def test_analyze_amino_acid_composition_hydrophobic(self):
        """Test amino acid composition analysis for hydrophobic proteins."""
        # High hydrophobic content sequence
        hydrophobic_seq = "AAAILLLMMMFFFWWWVVV"
        
        annotation = self.agent._analyze_amino_acid_composition(hydrophobic_seq)
        
        assert annotation is not None
        assert annotation.function_type == "cellular_component"
        assert "membrane protein" in annotation.description.lower()
        assert annotation.confidence_score == 0.7
    
    def test_analyze_amino_acid_composition_charged(self):
        """Test amino acid composition analysis for charged proteins."""
        # High charged residue content sequence
        charged_seq = "KKKRRRHHHDDDEEE"
        
        annotation = self.agent._analyze_amino_acid_composition(charged_seq)
        
        assert annotation is not None
        assert annotation.function_type == "molecular_function"
        assert "nucleic acid binding" in annotation.description.lower()
        assert annotation.confidence_score == 0.6
    
    def test_analyze_amino_acid_composition_normal(self):
        """Test amino acid composition analysis for normal proteins."""
        # Normal composition sequence
        normal_seq = "ACDEFGHIKLMNPQRSTVWY"
        
        annotation = self.agent._analyze_amino_acid_composition(normal_seq)
        
        # Should not trigger any specific composition-based annotation
        assert annotation is None
    
    def test_identify_functional_motifs(self):
        """Test functional motif identification."""
        # Sequence with ATP binding motif (Walker A motif)
        atp_seq = "GKSGKTAAAA"  # Fixed pattern: GK followed by GKT
        annotations = self.agent._identify_functional_motifs(atp_seq)
        
        # Should find ATP binding motif
        atp_annotations = [a for a in annotations if "ATP" in a.description]
        assert len(atp_annotations) > 0
        assert atp_annotations[0].function_type == "molecular_function"
    
    def test_predict_from_properties_short(self):
        """Test function prediction for short proteins."""
        short_seq = "MKFKR"  # Very short sequence
        
        annotation = self.agent._predict_from_properties(short_seq)
        
        assert annotation is not None
        assert annotation.function_type == "biological_process"
        assert "peptide hormone" in annotation.description.lower()
        assert annotation.confidence_score == 0.5
    
    def test_predict_from_properties_long(self):
        """Test function prediction for long proteins."""
        long_seq = "A" * 1500  # Very long sequence
        
        annotation = self.agent._predict_from_properties(long_seq)
        
        assert annotation is not None
        assert annotation.function_type == "molecular_function"
        assert "structural protein" in annotation.description.lower()
        assert annotation.confidence_score == 0.5    

    @patch('requests.Session.get')
    def test_query_uniprot_annotations_success(self, mock_get):
        """Test successful UniProt annotation query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_uniprot_response
        mock_get.return_value = mock_response
        
        annotations = self.agent._query_uniprot_annotations(self.sample_uniprot_id)
        
        assert len(annotations) >= 1
        # Should find protein name annotation
        name_annotations = [a for a in annotations if a.function_type == "protein_name"]
        assert len(name_annotations) >= 1
        assert "Insulin" in name_annotations[0].description
        
        # Should find GO annotation
        go_annotations = [a for a in annotations if a.function_type == "gene_ontology"]
        assert len(go_annotations) >= 1
        
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_query_uniprot_annotations_failure(self, mock_get):
        """Test UniProt annotation query failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        annotations = self.agent._query_uniprot_annotations("INVALID")
        
        assert len(annotations) == 0
        mock_get.assert_called_once()
    
    def test_identify_domains(self):
        """Test protein domain identification."""
        # Sequence with immunoglobulin-like pattern
        ig_seq = "C" + "A" * 50 + "C" + "B" * 15 + "C" + "D" * 50 + "C"
        
        domains = self.agent._identify_domains(ig_seq, "test_protein")
        
        # Should find immunoglobulin domain
        ig_domains = [d for d in domains if "immunoglobulin" in d.name.lower()]
        assert len(ig_domains) >= 1
        assert ig_domains[0].start_position > 0
        assert ig_domains[0].end_position > ig_domains[0].start_position
    
    def test_identify_domains_no_patterns(self):
        """Test domain identification when no patterns found."""
        # Simple sequence without recognizable patterns (avoid patterns that match helix-turn-helix)
        simple_seq = "ACDEFGHILMNPQSTVWY" * 3  # Removed K and R to avoid helix-turn-helix pattern
        
        domains = self.agent._identify_domains(simple_seq, "test_protein")
        
        # Should create a generic full-sequence domain
        assert len(domains) == 1
        assert domains[0].domain_id == "full_sequence"
        assert domains[0].start_position == 1
        assert domains[0].end_position == len(simple_seq)
    
    @patch('requests.Session.get')
    def test_query_string_database_success(self, mock_get):
        """Test successful STRING database query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_string_response
        mock_get.return_value = mock_response
        
        interactions = self.agent._query_string_database(self.sample_uniprot_id)
        
        assert len(interactions) >= 1
        assert interactions[0].partner_protein_id == "INSR"
        assert interactions[0].interaction_type == "physical_association"
        assert interactions[0].confidence_score == 0.9  # 900/1000
        assert interactions[0].source_database == "STRING"
        
        mock_get.assert_called_once()
    
    def test_predict_interactions(self):
        """Test interaction prediction from sequence motifs."""
        # Sequence with PDZ binding motif at C-terminus: [ST].[AILV]$
        pdz_seq = "ACDEFGHIKLMNPQRSAV"  # Ends with SAV (matches S.V pattern)
        
        interactions = self.agent._predict_interactions(pdz_seq, "test_protein")
        
        # Should find PDZ domain interaction
        pdz_interactions = [i for i in interactions if "PDZ" in i.partner_protein_id]
        assert len(pdz_interactions) >= 1
        assert pdz_interactions[0].interaction_type == "domain_motif_interaction"
        assert pdz_interactions[0].source_database == "predicted"
    
    def test_predict_interactions_sh3_motif(self):
        """Test SH3 interaction prediction."""
        # Sequence with SH3 binding motif: P..P pattern
        sh3_seq = "ACDEFPABPGHIKLMNPQRSTVWY"  # Contains PABP pattern
        
        interactions = self.agent._predict_interactions(sh3_seq, "test_protein")
        
        # Should find SH3 domain interaction
        sh3_interactions = [i for i in interactions if "SH3" in i.partner_protein_id]
        assert len(sh3_interactions) >= 1
        assert sh3_interactions[0].confidence_score == 0.5
    
    @patch('requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        response = self.agent._make_request("http://test.com")
        
        assert response is not None
        assert response.status_code == 200
        mock_get.assert_called_once()
    
    @patch('requests.Session.get')
    def test_make_request_rate_limited(self, mock_get):
        """Test rate limited HTTP request with retry."""
        # First call returns 429, second call succeeds
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = self.agent._make_request("http://test.com")
        
        assert response is not None
        assert response.status_code == 200
        assert mock_get.call_count == 2
    
    @patch('requests.Session.get')
    def test_make_request_failure(self, mock_get):
        """Test failed HTTP request."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = self.agent._make_request("http://test.com")
        
        assert response is None
        assert mock_get.call_count == 3  # Should retry 3 times    

    @patch.object(ProteomicsAgent, '_get_structure_data')
    @patch.object(ProteomicsAgent, '_predict_function')
    @patch.object(ProteomicsAgent, '_identify_domains')
    @patch.object(ProteomicsAgent, '_find_interactions')
    def test_analyze_protein_complete(self, mock_interactions, mock_domains, 
                                    mock_function, mock_structure):
        """Test complete protein analysis."""
        # Mock return values
        mock_structure.return_value = ProteinStructure(
            pdb_id="1ZNI",
            structure_method="X-RAY DIFFRACTION",
            resolution=1.8
        )
        
        mock_function.return_value = [
            FunctionAnnotation(
                function_type="molecular_function",
                description="hormone activity",
                confidence_score=0.9,
                source="test"
            )
        ]
        
        mock_domains.return_value = [
            ProteinDomain(
                domain_id="domain_1",
                name="Test Domain",
                start_position=1,
                end_position=20
            )
        ]
        
        mock_interactions.return_value = [
            ProteinInteraction(
                partner_protein_id="INSR",
                interaction_type="physical_association",
                confidence_score=0.9,
                source_database="STRING"
            )
        ]
        
        # Run analysis
        results = self.agent.analyze_protein(self.sample_protein, "test_protein")
        
        # Verify results
        assert isinstance(results, ProteomicsResults)
        assert results.protein_id == "test_protein"
        assert results.structure_data is not None
        assert len(results.functional_annotations) == 1
        assert len(results.domains) == 1
        assert len(results.interactions) == 1
        assert results.analysis_timestamp is not None
        
        # Verify all methods were called
        mock_structure.assert_called_once()
        mock_function.assert_called_once()
        mock_domains.assert_called_once()
        mock_interactions.assert_called_once()
    
    def test_analyze_protein_no_id(self):
        """Test protein analysis without providing protein ID."""
        with patch.object(self.agent, '_get_structure_data', return_value=None), \
             patch.object(self.agent, '_predict_function', return_value=[]), \
             patch.object(self.agent, '_identify_domains', return_value=[]), \
             patch.object(self.agent, '_find_interactions', return_value=[]):
            
            results = self.agent.analyze_protein(self.sample_protein)
            
            assert isinstance(results, ProteomicsResults)
            assert results.protein_id.startswith("protein_")
    
    def test_get_structure_data_public_method(self):
        """Test public get_structure_data method."""
        with patch.object(self.agent, '_get_structure_data', return_value=None) as mock_method:
            result = self.agent.get_structure_data(self.sample_pdb_id)
            
            mock_method.assert_called_once_with("", self.sample_pdb_id)
    
    def test_predict_function_public_method(self):
        """Test public predict_function method."""
        with patch.object(self.agent, '_predict_function', return_value=[]) as mock_method:
            result = self.agent.predict_function(self.sample_protein)
            
            mock_method.assert_called_once()
            assert isinstance(result, list)
    
    def test_analyze_protein_error_handling(self):
        """Test error handling in protein analysis."""
        with patch.object(self.agent, '_get_structure_data', side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                self.agent.analyze_protein(self.sample_protein)


class TestProteomicsAgentIntegration:
    """Integration tests for ProteomicsAgent."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.agent = ProteomicsAgent()
    
    def test_real_protein_analysis(self):
        """Test analysis with real protein sequence."""
        # Insulin A chain sequence (21 amino acids, should get full sequence domain)
        insulin_seq = "GIVEQCCTSICSLYQLENYCN"
        
        # This test will make real API calls if not mocked
        # In practice, you might want to mock external APIs for unit tests
        with patch.object(self.agent, '_make_request', return_value=None):
            results = self.agent.analyze_protein(insulin_seq, "insulin_test")
            
            assert isinstance(results, ProteomicsResults)
            assert results.protein_id == "insulin_test"
            # Should have some functional annotations from sequence analysis
            assert len(results.functional_annotations) >= 1  # Should get peptide hormone annotation
            # Should have at least one domain (full sequence domain for sequences > 20 aa)
            assert len(results.domains) >= 1
    
    def test_motif_detection_accuracy(self):
        """Test accuracy of motif detection."""
        # Sequence with known ATP binding motif (Walker A motif: GKSGKT)
        kinase_seq = "LGKSGKTFGKVYKVDLKQFMKIQNHGDLKFDDLKSELGKLYLVFEFLDLDLKRYMEGIPKDQPLGADIVKKFMMQLCKGIAYCHSHRILHRDLKPQNLLINTEGAIKLADFGLARAFGVPVRTYTHEVVTLWYRAPEILLGCKYYSTAVDIWSLGCIFAEMVTRRALFPGDSEIDQLFRIFRTLGTPDEVVWPGVTSMPDYKPSFPKWARQDFSKVVPPLDEDGRSLLSQMLHYDPNKRISAKAALAHPFFQDVTKPVPHLRL"
        
        annotations = self.agent._identify_functional_motifs(kinase_seq)
        
        # Should detect ATP binding motif
        atp_annotations = [a for a in annotations if "ATP" in a.description]
        assert len(atp_annotations) > 0
    
    def test_domain_identification_patterns(self):
        """Test domain identification with known patterns."""
        # Sequence designed to match immunoglobulin pattern
        ig_like_seq = "C" + "A" * 45 + "C" + "G" * 12 + "C" + "T" * 45 + "C"
        
        domains = self.agent._identify_domains(ig_like_seq, "test_ig")
        
        # Should identify immunoglobulin-like domain
        ig_domains = [d for d in domains if "immunoglobulin" in d.name.lower()]
        assert len(ig_domains) >= 1
        
        if ig_domains:
            assert ig_domains[0].start_position == 1
            assert ig_domains[0].end_position > ig_domains[0].start_position
    
    def test_session_cleanup(self):
        """Test that session is properly cleaned up."""
        agent = ProteomicsAgent()
        session = agent.session
        
        # Delete agent
        del agent
        
        # Session should be closed (this is hard to test directly,
        # but we can at least verify the cleanup method exists)
        assert hasattr(ProteomicsAgent, '__del__')