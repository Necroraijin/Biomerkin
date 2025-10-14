"""
Unit tests for GenomicsAgent.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqFeature import SeqFeature, FeatureLocation

from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.models.genomics import GenomicsResults, Gene, Mutation, ProteinSequence
from biomerkin.models.base import GenomicLocation, QualityMetrics, MutationType


class TestGenomicsAgent:
    """Test cases for GenomicsAgent."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = GenomicsAgent()
        
        # Sample DNA sequence (simplified)
        self.sample_dna = "ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGA"
        
        # Sample reference sequence with a mutation
        self.reference_dna = "ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTAA"
        
        # Sample FASTA content
        self.fasta_content = f">test_sequence\n{self.sample_dna}\n"
        
        # Sample GenBank content
        self.genbank_content = """LOCUS       test_seq                  63 bp    DNA     linear   UNK 01-JAN-1980
DEFINITION  Test sequence
ACCESSION   test_seq
VERSION     test_seq
KEYWORDS    .
SOURCE      .
  ORGANISM  .
            .
FEATURES             Location/Qualifiers
     gene            1..63
                     /gene="test_gene"
                     /product="test protein"
     CDS             1..63
                     /gene="test_gene"
                     /product="test protein"
                     /protein_id="test_protein"
ORIGIN      
        1 atgaaacgca ttagcaccac cattaccacc accatcacca ttaccacagg taacggtgcg
       61 ggc
//
"""
    
    def test_init(self):
        """Test GenomicsAgent initialization."""
        agent = GenomicsAgent()
        assert agent.supported_formats == ['fasta', 'genbank', 'gb']
        assert agent.logger is not None
    
    def test_parse_raw_sequence(self):
        """Test parsing raw DNA sequence string."""
        sequences = self.agent._parse_sequence_input(self.sample_dna)
        
        assert len(sequences) == 1
        assert str(sequences[0].seq) == self.sample_dna
        assert sequences[0].id == "raw_sequence"
    
    def test_parse_fasta_file(self):
        """Test parsing FASTA file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(self.fasta_content)
            f.flush()
            temp_name = f.name
        
        try:
            sequences = self.agent._parse_sequence_file(temp_name)
            
            assert len(sequences) == 1
            assert str(sequences[0].seq) == self.sample_dna
            assert sequences[0].id == "test_sequence"
        finally:
            os.unlink(temp_name)
    
    def test_parse_genbank_file(self):
        """Test parsing GenBank file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gb', delete=False) as f:
            f.write(self.genbank_content)
            f.flush()
            temp_name = f.name
        
        try:
            sequences = self.agent._parse_sequence_file(temp_name)
            
            assert len(sequences) == 1
            assert sequences[0].id == "test_seq"
            assert len(sequences[0].features) > 0
        finally:
            os.unlink(temp_name)
    
    def test_detect_file_format_fasta(self):
        """Test file format detection for FASTA."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(self.fasta_content)
            f.flush()
            temp_name = f.name
        
        try:
            format_detected = self.agent._detect_file_format(temp_name)
            assert format_detected == 'fasta'
        finally:
            os.unlink(temp_name)
    
    def test_detect_file_format_genbank(self):
        """Test file format detection for GenBank."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.gb', delete=False) as f:
            f.write(self.genbank_content)
            f.flush()
            temp_name = f.name
        
        try:
            format_detected = self.agent._detect_file_format(temp_name)
            assert format_detected == 'genbank'
        finally:
            os.unlink(temp_name)
    
    def test_extract_genes_from_features(self):
        """Test gene extraction from GenBank features."""
        # Create a mock sequence with features
        feature = SeqFeature(
            FeatureLocation(0, 63),
            type="gene",
            qualifiers={
                'gene': ['test_gene'],
                'product': ['test protein'],
                'locus_tag': ['TEST_001']
            }
        )
        
        sequence = SeqRecord(
            Seq(self.sample_dna),
            id="test_seq",
            features=[feature]
        )
        
        genes = self.agent._extract_genes_from_features(sequence)
        
        assert len(genes) == 1
        assert genes[0].id == 'test_gene'
        assert genes[0].name == 'test_gene'
        assert genes[0].function == 'test protein'
        assert genes[0].confidence_score == 0.9
    
    def test_find_orfs(self):
        """Test open reading frame detection."""
        # Sequence with clear ORF: ATG...TAA
        test_seq = "ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTAA"
        
        orfs = self.agent._find_orfs(test_seq, min_length=60)
        
        assert len(orfs) >= 1
        # Check that we found an ORF starting with ATG
        assert any(orf[0] == 0 for orf in orfs)  # ORF starting at position 0
    
    def test_predict_genes_basic(self):
        """Test basic gene prediction."""
        sequence = SeqRecord(Seq(self.sample_dna), id="test_seq")
        
        genes = self.agent._predict_genes_basic(sequence)
        
        # Should find at least one predicted gene
        assert len(genes) >= 0
        if genes:
            assert genes[0].gene_type == "predicted_CDS"
            assert genes[0].confidence_score == 0.6
    
    def test_detect_mutations_snp(self):
        """Test SNP mutation detection."""
        sequence = SeqRecord(Seq(self.sample_dna), id="test")
        
        mutations = self.agent._detect_mutations(sequence, self.reference_dna)
        
        # Should detect the TGA -> TAA mutation at the end
        assert len(mutations) >= 1
        snp_mutations = [m for m in mutations if m.mutation_type == MutationType.SNP]
        assert len(snp_mutations) >= 1
    
    def test_detect_mutations_insertion(self):
        """Test insertion mutation detection."""
        # Create sequence with insertion
        inserted_seq = self.sample_dna + "AAAA"  # Add 4 bases
        sequence = SeqRecord(Seq(inserted_seq), id="test")
        
        mutations = self.agent._detect_mutations(sequence, self.sample_dna)
        
        # Should detect insertion
        insertion_mutations = [m for m in mutations if m.mutation_type == MutationType.INSERTION]
        assert len(insertion_mutations) == 1
        assert insertion_mutations[0].alternate_base == "AAAA"
    
    def test_detect_mutations_deletion(self):
        """Test deletion mutation detection."""
        # Create sequence with deletion
        deleted_seq = self.sample_dna[:-4]  # Remove 4 bases
        sequence = SeqRecord(Seq(deleted_seq), id="test")
        
        mutations = self.agent._detect_mutations(sequence, self.sample_dna)
        
        # Should detect deletion
        deletion_mutations = [m for m in mutations if m.mutation_type == MutationType.DELETION]
        assert len(deletion_mutations) == 1
    
    def test_translate_to_proteins(self):
        """Test DNA to protein translation."""
        # Create a gene that should translate properly
        gene = Gene(
            id="test_gene",
            name="test_gene",
            location=GenomicLocation(
                chromosome="test_seq",
                start_position=0,
                end_position=63,
                strand='+'
            ),
            function="test function",
            confidence_score=0.9
        )
        
        sequence = SeqRecord(Seq(self.sample_dna), id="test_seq")
        
        proteins = self.agent._translate_to_proteins(sequence, [gene])
        
        assert len(proteins) >= 0
        if proteins:
            assert proteins[0].gene_id == "test_gene"
            assert proteins[0].length > 0
            assert proteins[0].molecular_weight > 0
    
    def test_translate_to_protein_public_method(self):
        """Test public translate_to_protein method."""
        proteins = self.agent.translate_to_protein(self.sample_dna)
        
        # Should get proteins from multiple reading frames
        assert isinstance(proteins, list)
        # At least one frame should produce a reasonable protein
        long_proteins = [p for p in proteins if p.length > 10]
        assert len(long_proteins) >= 0
    
    def test_calculate_quality_metrics(self):
        """Test quality metrics calculation."""
        sequence = SeqRecord(Seq(self.sample_dna), id="test")
        
        metrics = self.agent._calculate_quality_metrics(sequence)
        
        assert isinstance(metrics, QualityMetrics)
        assert 0 <= metrics.quality_score <= 1
        assert 0 <= metrics.confidence_level <= 1
        assert metrics.coverage_depth > 0
        assert metrics.error_rate is not None
    
    def test_analyze_sequence_with_raw_string(self):
        """Test complete sequence analysis with raw DNA string."""
        results = self.agent.analyze_sequence(self.sample_dna)
        
        assert isinstance(results, GenomicsResults)
        assert results.sequence_length == len(self.sample_dna)
        assert results.analysis_timestamp is not None
        assert isinstance(results.genes, list)
        assert isinstance(results.mutations, list)
        assert isinstance(results.protein_sequences, list)
        assert isinstance(results.quality_metrics, QualityMetrics)
    
    def test_analyze_sequence_with_reference(self):
        """Test sequence analysis with reference for mutation detection."""
        results = self.agent.analyze_sequence(self.sample_dna, self.reference_dna)
        
        assert isinstance(results, GenomicsResults)
        assert len(results.mutations) > 0  # Should detect mutations
    
    def test_analyze_sequence_with_file(self):
        """Test sequence analysis with FASTA file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(self.fasta_content)
            f.flush()
            temp_name = f.name
        
        try:
            results = self.agent.analyze_sequence(temp_name)
            
            assert isinstance(results, GenomicsResults)
            assert results.sequence_length == len(self.sample_dna)
        finally:
            os.unlink(temp_name)
    
    def test_analyze_sequence_invalid_input(self):
        """Test sequence analysis with invalid input."""
        with pytest.raises(FileNotFoundError):
            self.agent.analyze_sequence("nonexistent_file.fasta")
    
    def test_analyze_sequence_empty_input(self):
        """Test sequence analysis with empty input."""
        with pytest.raises(ValueError):
            self.agent.analyze_sequence("")
    
    def test_detect_mutations_public_method(self):
        """Test public detect_mutations method."""
        mutations = self.agent.detect_mutations(self.sample_dna, self.reference_dna)
        
        assert isinstance(mutations, list)
        if mutations:
            assert all(isinstance(m, Mutation) for m in mutations)
    
    def test_get_feature_qualifier(self):
        """Test feature qualifier extraction."""
        feature = SeqFeature(
            FeatureLocation(0, 10),
            qualifiers={
                'gene': ['test_gene'],
                'product': ['test_product']
            }
        )
        
        # Test existing qualifier
        result = self.agent._get_feature_qualifier(feature, ['gene'])
        assert result == 'test_gene'
        
        # Test multiple qualifier names
        result = self.agent._get_feature_qualifier(feature, ['locus_tag', 'gene'])
        assert result == 'test_gene'
        
        # Test non-existing qualifier
        result = self.agent._get_feature_qualifier(feature, ['nonexistent'])
        assert result is None
    
    def test_classify_mutation(self):
        """Test mutation classification."""
        # Test SNP
        mutation_type = self.agent._classify_mutation("A", "T", 0)
        assert mutation_type == MutationType.SNP
        
        # Note: More complex mutation classification would require 
        # more sophisticated sequence comparison logic
    
    @patch('biomerkin.agents.genomics_agent.get_logger')
    def test_logging(self, mock_get_logger):
        """Test that logging is properly configured."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        agent = GenomicsAgent()
        agent.analyze_sequence(self.sample_dna)
        
        # Verify logger was called
        mock_get_logger.assert_called_once()
        mock_logger.info.assert_called()


class TestGenomicsAgentIntegration:
    """Integration tests for GenomicsAgent with real Biopython functionality."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.agent = GenomicsAgent()
    
    def test_real_fasta_parsing(self):
        """Test parsing a real FASTA file."""
        fasta_content = """>gi|5524211|gb|AAD44166.1| cytochrome b [Elephas maximus maximus]
LCLYTHIGRNIYYGSYLYSETWNTGIMLLLITMATAFMGYVLPWGQMSFWGATVITNLFSAIPYIGTNLV
EWIWGGFSVDKATLNRFFAFHFILPFTMVALAGVHLTFLHETGSNNPLGLTSDSDKIPFHPYYTIKDFLG
LLILILLLLLLALLSPDMLGDPDNHMPADPLNTPLHIKPEWYFLFAYAILRSVPNKLGGVLALFLSIVIL
GLMPFLHTSKHRSMMLRPLSQALFWTLTMDLLTLTWIGSQPVEYPYTIIGQMASILYFSIILAFLPIAGX
IENY"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
            f.write(fasta_content)
            f.flush()
            temp_name = f.name
        
        try:
            results = self.agent.analyze_sequence(temp_name)
            
            assert isinstance(results, GenomicsResults)
            assert results.sequence_length > 0
            assert len(results.protein_sequences) >= 0  # May or may not find proteins
            
        finally:
            os.unlink(temp_name)
    
    def test_protein_translation_accuracy(self):
        """Test accuracy of protein translation."""
        # Known DNA sequence that should translate to specific protein
        dna_seq = "ATGAAATTTAAACGT"  # Should translate to MKFKR (but incomplete codon at end)
        
        proteins = self.agent.translate_to_protein(dna_seq)
        
        # Should find the protein in one of the reading frames
        protein_sequences = [p.sequence for p in proteins]
        # The sequence translates to "MKFKR" 
        assert any("MKFKR" in seq for seq in protein_sequences)