"""
GenomicsAgent for DNA sequence analysis using Biopython.

This agent handles DNA sequence parsing, gene identification, mutation detection,
and DNA to protein translation using Biopython libraries.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import tempfile
import os

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqUtils import molecular_weight
from Bio.SeqFeature import SeqFeature, FeatureLocation
from Bio.Data import CodonTable

from ..models.genomics import GenomicsResults, Gene, Mutation, ProteinSequence
from ..models.base import GenomicLocation, QualityMetrics, MutationType
from ..utils.logging_config import get_logger
from .base_agent import BaseAgent, agent_error_handler


class GenomicsAgent(BaseAgent):
    """
    Agent responsible for genomic sequence analysis.
    
    Provides functionality for:
    - DNA sequence parsing (FASTA, GenBank formats)
    - Gene identification and annotation
    - Mutation detection against reference sequences
    - DNA to protein translation
    """
    
    def __init__(self):
        """Initialize the GenomicsAgent."""
        super().__init__("genomics")
        self.supported_formats = ['fasta', 'genbank', 'gb']
        
    @agent_error_handler()
    def execute(self, input_data: Dict[str, Any], workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute genomics analysis.
        
        Args:
            input_data: Dictionary containing sequence_file and optional reference_sequence
            workflow_id: Optional workflow identifier
            
        Returns:
            Dictionary containing genomics analysis results
        """
        sequence_file = input_data.get('sequence_file') or input_data.get('dna_sequence_file')
        reference_sequence = input_data.get('reference_sequence')
        
        if not sequence_file:
            raise ValueError("sequence_file is required in input_data")
        
        results = self.analyze_sequence(sequence_file, reference_sequence)
        
        return {
            'genomics_results': results,
            'genes': results.genes,
            'mutations': results.mutations,
            'protein_sequences': results.protein_sequences,
            'quality_metrics': results.quality_metrics,
            'sequence_length': results.sequence_length,
            'analysis_timestamp': results.analysis_timestamp
        }
    
    def analyze_sequence(self, sequence_file: str, reference_sequence: Optional[str] = None) -> GenomicsResults:
        """
        Analyze DNA sequence for genes, mutations, and proteins.
        
        Args:
            sequence_file: Path to DNA sequence file or raw sequence string
            reference_sequence: Optional reference sequence for mutation detection
            
        Returns:
            GenomicsResults containing genes, mutations, and protein sequences
        """
        self.logger.info(f"Starting genomic analysis")
        
        try:
            # Parse the sequence
            sequences = self._parse_sequence_input(sequence_file)
            
            if not sequences:
                raise ValueError("No valid sequences found in input")
            
            # For now, analyze the first sequence (can be extended for multiple sequences)
            primary_sequence = sequences[0]
            
            # Identify genes
            genes = self._identify_genes(primary_sequence)
            
            # Detect mutations if reference is provided
            mutations = []
            if reference_sequence:
                mutations = self._detect_mutations(primary_sequence, reference_sequence)
            
            # Translate DNA to proteins
            protein_sequences = self._translate_to_proteins(primary_sequence, genes)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(primary_sequence)
            
            results = GenomicsResults(
                genes=genes,
                mutations=mutations,
                protein_sequences=protein_sequences,
                quality_metrics=quality_metrics,
                sequence_length=len(primary_sequence.seq),
                analysis_timestamp=datetime.now().isoformat()
            )
            
            self.logger.info(f"Genomic analysis completed. Found {len(genes)} genes, "
                           f"{len(mutations)} mutations, {len(protein_sequences)} proteins")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in genomic analysis: {str(e)}")
            raise
    
    def _parse_sequence_input(self, sequence_input: str) -> List[SeqRecord]:
        """
        Parse sequence input which can be a file path or raw sequence.
        
        Args:
            sequence_input: File path or raw sequence string
            
        Returns:
            List of SeqRecord objects
        """
        sequences = []
        
        # Check if input is empty
        if not sequence_input or sequence_input.strip() == "":
            raise ValueError("Empty sequence input provided")
        
        # Check if input looks like a file path
        if ('.' in sequence_input and 
            (sequence_input.endswith('.fasta') or sequence_input.endswith('.fa') or 
             sequence_input.endswith('.gb') or sequence_input.endswith('.genbank'))):
            # Looks like a file path
            if os.path.exists(sequence_input):
                sequences = self._parse_sequence_file(sequence_input)
            else:
                raise FileNotFoundError(f"Sequence file not found: {sequence_input}")
        else:
            # Treat as raw sequence string
            sequences = [SeqRecord(Seq(sequence_input), id="raw_sequence", description="Raw input sequence")]
        
        return sequences
    
    def _parse_sequence_file(self, file_path: str) -> List[SeqRecord]:
        """
        Parse DNA sequence file in FASTA or GenBank format.
        
        Args:
            file_path: Path to sequence file
            
        Returns:
            List of SeqRecord objects
        """
        sequences = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Sequence file not found: {file_path}")
        
        # Determine file format
        file_format = self._detect_file_format(file_path)
        
        try:
            with open(file_path, 'r') as handle:
                sequences = list(SeqIO.parse(handle, file_format))
            
            self.logger.info(f"Parsed {len(sequences)} sequences from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error parsing sequence file {file_path}: {str(e)}")
            raise ValueError(f"Failed to parse sequence file: {str(e)}")
        
        return sequences
    
    def _detect_file_format(self, file_path) -> str:
        """
        Detect file format based on extension and content.
        
        Args:
            file_path: Path to sequence file (string or Path object)
            
        Returns:
            File format string for Biopython
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension in ['.fasta', '.fa', '.fas']:
            return 'fasta'
        elif extension in ['.gb', '.genbank']:
            return 'genbank'
        else:
            # Try to detect from content
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                if first_line.startswith('>'):
                    return 'fasta'
                elif first_line.startswith('LOCUS'):
                    return 'genbank'
        
        # Default to fasta
        return 'fasta'
    
    def _identify_genes(self, sequence: SeqRecord) -> List[Gene]:
        """
        Identify genes in the DNA sequence.
        
        Args:
            sequence: SeqRecord containing DNA sequence
            
        Returns:
            List of identified genes
        """
        genes = []
        
        # If sequence has features (from GenBank), use them
        if sequence.features:
            genes = self._extract_genes_from_features(sequence)
        else:
            # For FASTA sequences, perform basic gene prediction
            genes = self._predict_genes_basic(sequence)
        
        return genes
    
    def _extract_genes_from_features(self, sequence: SeqRecord) -> List[Gene]:
        """
        Extract gene information from GenBank features.
        
        Args:
            sequence: SeqRecord with features
            
        Returns:
            List of Gene objects
        """
        genes = []
        
        for feature in sequence.features:
            if feature.type in ['gene', 'CDS']:
                gene_id = self._get_feature_qualifier(feature, ['gene', 'locus_tag', 'protein_id'])
                gene_name = self._get_feature_qualifier(feature, ['gene', 'product'])
                function = self._get_feature_qualifier(feature, ['product', 'function', 'note'])
                
                if gene_id:
                    location = GenomicLocation(
                        chromosome=sequence.id,
                        start_position=int(feature.location.start),
                        end_position=int(feature.location.end),
                        strand='+' if feature.location.strand == 1 else '-'
                    )
                    
                    gene = Gene(
                        id=gene_id,
                        name=gene_name or gene_id,
                        location=location,
                        function=function or "Unknown function",
                        confidence_score=0.9,  # High confidence for annotated genes
                        gene_type=feature.type
                    )
                    
                    genes.append(gene)
        
        return genes
    
    def _get_feature_qualifier(self, feature: SeqFeature, qualifier_names: List[str]) -> Optional[str]:
        """
        Get qualifier value from feature.
        
        Args:
            feature: SeqFeature object
            qualifier_names: List of qualifier names to try
            
        Returns:
            Qualifier value or None
        """
        for qualifier_name in qualifier_names:
            if qualifier_name in feature.qualifiers:
                return feature.qualifiers[qualifier_name][0]
        return None
    
    def _predict_genes_basic(self, sequence: SeqRecord) -> List[Gene]:
        """
        Basic gene prediction for sequences without annotations.
        
        Args:
            sequence: SeqRecord containing DNA sequence
            
        Returns:
            List of predicted genes
        """
        genes = []
        seq_str = str(sequence.seq).upper()
        
        # Look for open reading frames (ORFs)
        orfs = self._find_orfs(seq_str)
        
        for i, (start, end, frame) in enumerate(orfs):
            gene_id = f"orf_{i+1}"
            
            location = GenomicLocation(
                chromosome=sequence.id,
                start_position=start,
                end_position=end,
                strand='+' if frame > 0 else '-'
            )
            
            gene = Gene(
                id=gene_id,
                name=f"Predicted ORF {i+1}",
                location=location,
                function="Predicted open reading frame",
                confidence_score=0.6,  # Lower confidence for predicted genes
                gene_type="predicted_CDS"
            )
            
            genes.append(gene)
        
        return genes
    
    def _find_orfs(self, sequence: str, min_length: int = 300) -> List[Tuple[int, int, int]]:
        """
        Find open reading frames in DNA sequence.
        
        Args:
            sequence: DNA sequence string
            min_length: Minimum ORF length in nucleotides
            
        Returns:
            List of tuples (start, end, frame)
        """
        orfs = []
        start_codons = ['ATG']
        stop_codons = ['TAA', 'TAG', 'TGA']
        
        # Check all three reading frames
        for frame in range(3):
            i = frame
            while i < len(sequence) - 2:
                codon = sequence[i:i+3]
                
                if codon in start_codons:
                    # Found start codon, look for stop codon
                    start_pos = i
                    j = i + 3
                    
                    while j < len(sequence) - 2:
                        stop_codon = sequence[j:j+3]
                        if stop_codon in stop_codons:
                            # Found stop codon
                            end_pos = j + 3
                            if end_pos - start_pos >= min_length:
                                orfs.append((start_pos, end_pos, frame + 1))
                            break
                        j += 3
                    
                    i = j if j < len(sequence) else len(sequence)
                else:
                    i += 3
        
        return orfs
    
    def _detect_mutations(self, sequence: SeqRecord, reference_sequence: str) -> List[Mutation]:
        """
        Detect mutations by comparing sequence against reference.
        
        Args:
            sequence: SeqRecord to analyze
            reference_sequence: Reference sequence string
            
        Returns:
            List of detected mutations
        """
        mutations = []
        seq_str = str(sequence.seq).upper()
        ref_str = reference_sequence.upper()
        
        # Simple pairwise comparison (can be enhanced with alignment algorithms)
        min_length = min(len(seq_str), len(ref_str))
        
        i = 0
        while i < min_length:
            if seq_str[i] != ref_str[i]:
                # Detect mutation type
                mutation_type = self._classify_mutation(seq_str, ref_str, i)
                
                mutation = Mutation(
                    position=i + 1,  # 1-based position
                    reference_base=ref_str[i],
                    alternate_base=seq_str[i],
                    mutation_type=mutation_type,
                    clinical_significance="Unknown",  # Would need database lookup
                    effect_prediction="Unknown"
                )
                
                mutations.append(mutation)
            
            i += 1
        
        # Check for length differences (insertions/deletions)
        if len(seq_str) != len(ref_str):
            if len(seq_str) > len(ref_str):
                # Insertion
                mutation = Mutation(
                    position=len(ref_str) + 1,
                    reference_base="",
                    alternate_base=seq_str[len(ref_str):],
                    mutation_type=MutationType.INSERTION,
                    clinical_significance="Unknown"
                )
                mutations.append(mutation)
            else:
                # Deletion
                mutation = Mutation(
                    position=len(seq_str) + 1,
                    reference_base=ref_str[len(seq_str):],
                    alternate_base="",
                    mutation_type=MutationType.DELETION,
                    clinical_significance="Unknown"
                )
                mutations.append(mutation)
        
        self.logger.info(f"Detected {len(mutations)} mutations")
        return mutations
    
    def _classify_mutation(self, sequence: str, reference: str, position: int) -> MutationType:
        """
        Classify the type of mutation at a given position.
        
        Args:
            sequence: Sample sequence
            reference: Reference sequence
            position: Position of mutation
            
        Returns:
            MutationType classification
        """
        # For now, simple classification - can be enhanced
        if len(sequence[position]) == 1 and len(reference[position]) == 1:
            return MutationType.SNP
        elif len(sequence[position:position+1]) > len(reference[position:position+1]):
            return MutationType.INSERTION
        elif len(sequence[position:position+1]) < len(reference[position:position+1]):
            return MutationType.DELETION
        else:
            return MutationType.SUBSTITUTION
    
    def _translate_to_proteins(self, sequence: SeqRecord, genes: List[Gene]) -> List[ProteinSequence]:
        """
        Translate DNA sequences to protein sequences.
        
        Args:
            sequence: SeqRecord containing DNA sequence
            genes: List of identified genes
            
        Returns:
            List of protein sequences
        """
        protein_sequences = []
        seq_str = str(sequence.seq)
        
        for gene in genes:
            try:
                # Extract gene sequence
                start = gene.location.start_position
                end = gene.location.end_position
                gene_seq = seq_str[start:end]
                
                # Create Seq object
                dna_seq = Seq(gene_seq)
                
                # Reverse complement if on negative strand
                if gene.location.strand == '-':
                    dna_seq = dna_seq.reverse_complement()
                
                # Translate to protein
                protein_seq = dna_seq.translate()
                
                # Remove stop codons
                protein_str = str(protein_seq).rstrip('*')
                
                if protein_str:  # Only add if translation produced protein
                    # Calculate molecular weight
                    mol_weight = molecular_weight(protein_str, seq_type='protein')
                    
                    protein = ProteinSequence(
                        sequence=protein_str,
                        gene_id=gene.id,
                        length=len(protein_str),
                        molecular_weight=mol_weight,
                        protein_id=f"{gene.id}_protein",
                        description=f"Protein translated from {gene.name}"
                    )
                    
                    protein_sequences.append(protein)
                    
            except Exception as e:
                self.logger.warning(f"Failed to translate gene {gene.id}: {str(e)}")
                continue
        
        self.logger.info(f"Translated {len(protein_sequences)} protein sequences")
        return protein_sequences
    
    def _calculate_quality_metrics(self, sequence: SeqRecord) -> QualityMetrics:
        """
        Calculate quality metrics for the genomic analysis.
        
        Args:
            sequence: SeqRecord to analyze
            
        Returns:
            QualityMetrics object
        """
        seq_str = str(sequence.seq).upper()
        
        # Calculate GC content as a quality indicator
        gc_count = seq_str.count('G') + seq_str.count('C')
        gc_content = gc_count / len(seq_str) if len(seq_str) > 0 else 0
        
        # Calculate N content (unknown bases)
        n_count = seq_str.count('N')
        n_percentage = n_count / len(seq_str) if len(seq_str) > 0 else 0
        
        # Quality score based on sequence composition
        quality_score = max(0, 1.0 - n_percentage)  # Higher quality = fewer N's
        
        # Confidence level based on sequence length and composition
        confidence_level = min(1.0, len(seq_str) / 1000.0)  # Higher confidence for longer sequences
        
        # Coverage depth (placeholder - would come from sequencing data)
        coverage_depth = 30.0  # Default coverage
        
        return QualityMetrics(
            coverage_depth=coverage_depth,
            quality_score=quality_score,
            confidence_level=confidence_level,
            error_rate=n_percentage
        )
    
    def detect_mutations(self, sequence: str, reference: str) -> List[Mutation]:
        """
        Public method to detect mutations between two sequences.
        
        Args:
            sequence: Sample sequence string
            reference: Reference sequence string
            
        Returns:
            List of detected mutations
        """
        # Create temporary SeqRecord for the sequence
        seq_record = SeqRecord(Seq(sequence), id="sample", description="Sample sequence")
        
        return self._detect_mutations(seq_record, reference)
    
    def translate_to_protein(self, dna_sequence: str) -> List[ProteinSequence]:
        """
        Public method to translate DNA sequence to protein sequences.
        
        Args:
            dna_sequence: DNA sequence string
            
        Returns:
            List of protein sequences from all reading frames
        """
        protein_sequences = []
        
        # Translate in all three reading frames
        for frame in range(3):
            try:
                # Extract sequence starting from frame
                frame_seq = dna_sequence[frame:]
                
                # Ensure length is multiple of 3
                frame_seq = frame_seq[:len(frame_seq) - (len(frame_seq) % 3)]
                
                if len(frame_seq) >= 3:
                    dna_seq = Seq(frame_seq)
                    protein_seq = dna_seq.translate()
                    protein_str = str(protein_seq).rstrip('*')
                    
                    if protein_str and len(protein_str) > 3:  # Only keep proteins with more than 3 amino acids
                        mol_weight = molecular_weight(protein_str, seq_type='protein')
                        
                        protein = ProteinSequence(
                            sequence=protein_str,
                            gene_id=f"frame_{frame + 1}",
                            length=len(protein_str),
                            molecular_weight=mol_weight,
                            protein_id=f"frame_{frame + 1}_protein",
                            description=f"Protein from reading frame {frame + 1}"
                        )
                        
                        protein_sequences.append(protein)
                        
            except Exception as e:
                self.logger.warning(f"Failed to translate reading frame {frame + 1}: {str(e)}")
                continue
        
        return protein_sequences