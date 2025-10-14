"""
Example integration of caching with GenomicsAgent.

This module demonstrates how to integrate the caching layer with
the existing GenomicsAgent for improved performance.
"""

import logging
from typing import List, Dict, Any, Optional
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from ..services.cache_manager import CacheType
from ..utils.cache_decorators import (
    cache_genomics_analysis, cache_computation, CacheKeyGenerator
)
from ..models.genomics import GenomicsResults, Gene, Mutation, ProteinSequence
from ..models.base import GenomicLocation, QualityMetrics, MutationType


logger = logging.getLogger(__name__)


class CachedGenomicsAgent:
    """
    GenomicsAgent with integrated caching for improved performance.
    
    This example shows how to add caching to expensive genomics operations
    while maintaining the same interface as the original agent.
    """
    
    def __init__(self):
        """Initialize the cached genomics agent."""
        self.logger = logging.getLogger(__name__)
    
    @cache_genomics_analysis(ttl_seconds=7200)  # Cache for 2 hours
    def analyze_sequence(self, sequence_data: str, sequence_format: str = "fasta") -> GenomicsResults:
        """
        Analyze DNA sequence with caching.
        
        Args:
            sequence_data: DNA sequence data
            sequence_format: Format of the sequence data
            
        Returns:
            GenomicsResults with analysis results
        """
        self.logger.info(f"Analyzing sequence (format: {sequence_format})")
        
        # Parse sequence
        sequences = self._parse_sequence(sequence_data, sequence_format)
        
        # Analyze each sequence
        all_genes = []
        all_mutations = []
        all_proteins = []
        
        for seq_record in sequences:
            genes = self._identify_genes(seq_record)
            mutations = self._detect_mutations(seq_record)
            proteins = self._translate_to_proteins(seq_record, genes)
            
            all_genes.extend(genes)
            all_mutations.extend(mutations)
            all_proteins.extend(proteins)
        
        quality_metrics = self._calculate_quality_metrics(sequences)
        return GenomicsResults(
            genes=all_genes,
            mutations=all_mutations,
            protein_sequences=all_proteins,
            quality_metrics=QualityMetrics(**quality_metrics)
        )
    
    @cache_computation(CacheType.GENOMICS_ANALYSIS, ttl_seconds=3600)
    def _identify_genes(self, seq_record: SeqRecord) -> List[Gene]:
        """
        Identify genes in sequence with caching.
        
        This method demonstrates caching of expensive gene identification.
        """
        self.logger.debug(f"Identifying genes in sequence: {seq_record.id}")
        
        # Simulate expensive gene identification
        # In real implementation, this would use gene prediction algorithms
        genes = []
        
        # Simple ORF finding as example
        sequence = str(seq_record.seq)
        start_codons = ["ATG"]
        stop_codons = ["TAA", "TAG", "TGA"]
        
        for frame in range(3):
            for i in range(frame, len(sequence) - 2, 3):
                codon = sequence[i:i+3]
                if codon in start_codons:
                    # Look for stop codon
                    for j in range(i + 3, len(sequence) - 2, 3):
                        stop_codon = sequence[j:j+3]
                        if stop_codon in stop_codons:
                            gene = Gene(
                                id=f"gene_{len(genes)+1}",
                                name=f"ORF_{frame}_{i}_{j}",
                                location=GenomicLocation(
                                    chromosome=seq_record.id,
                                    start_position=i,
                                    end_position=j
                                ),
                                function="Unknown",
                                confidence_score=0.8
                            )
                            genes.append(gene)
                            break
        
        self.logger.debug(f"Identified {len(genes)} genes")
        return genes
    
    @cache_computation(CacheType.GENOMICS_ANALYSIS, ttl_seconds=3600)
    def _detect_mutations(self, seq_record: SeqRecord) -> List[Mutation]:
        """
        Detect mutations with caching.
        
        This method demonstrates caching of mutation detection results.
        """
        self.logger.debug(f"Detecting mutations in sequence: {seq_record.id}")
        
        # Simulate mutation detection
        # In real implementation, this would compare against reference genomes
        mutations = []
        
        # Simple example: look for common SNP patterns
        sequence = str(seq_record.seq)
        common_snps = {
            "CG": "TG",  # C to T transition
            "GC": "AC",  # G to A transition
        }
        
        for i in range(len(sequence) - 1):
            dinucleotide = sequence[i:i+2]
            if dinucleotide in common_snps:
                mutation = Mutation(
                    position=i,
                    reference_base=dinucleotide[0],
                    alternate_base=common_snps[dinucleotide][0],
                    mutation_type=MutationType.SNP,
                    clinical_significance="Unknown"
                )
                mutations.append(mutation)
        
        self.logger.debug(f"Detected {len(mutations)} potential mutations")
        return mutations
    
    @cache_computation(CacheType.GENOMICS_ANALYSIS, ttl_seconds=3600)
    def _translate_to_proteins(self, seq_record: SeqRecord, genes: List[Gene]) -> List[ProteinSequence]:
        """
        Translate genes to proteins with caching.
        
        This method demonstrates caching of protein translation results.
        """
        self.logger.debug(f"Translating {len(genes)} genes to proteins")
        
        proteins = []
        sequence = seq_record.seq
        
        for gene in genes:
            try:
                # Extract gene coordinates
                # This is simplified - real implementation would parse location properly
                gene_seq = sequence  # Simplified for example
                
                # Translate to protein
                protein_seq = gene_seq.translate()
                
                protein = ProteinSequence(
                    sequence=str(protein_seq),
                    gene_id=gene.id,
                    length=len(protein_seq),
                    molecular_weight=self._calculate_molecular_weight(str(protein_seq))
                )
                proteins.append(protein)
                
            except Exception as e:
                self.logger.warning(f"Failed to translate gene {gene.id}: {str(e)}")
        
        self.logger.debug(f"Translated to {len(proteins)} proteins")
        return proteins
    
    def _parse_sequence(self, sequence_data: str, sequence_format: str) -> List[SeqRecord]:
        """Parse sequence data into SeqRecord objects."""
        try:
            from io import StringIO
            sequences = list(SeqIO.parse(StringIO(sequence_data), sequence_format))
            self.logger.debug(f"Parsed {len(sequences)} sequences")
            return sequences
        except Exception as e:
            self.logger.error(f"Failed to parse sequence: {str(e)}")
            raise
    
    def _calculate_quality_metrics(self, sequences: List[SeqRecord]) -> Dict[str, float]:
        """Calculate quality metrics for sequences."""
        if not sequences:
            return {"coverage_depth": 0.0, "quality_score": 0.0, "confidence_level": 0.0}
        
        total_length = sum(len(seq.seq) for seq in sequences)
        avg_length = total_length / len(sequences)
        
        return {
            "coverage_depth": avg_length / 1000.0,  # Simplified metric
            "quality_score": 0.95,  # Placeholder
            "confidence_level": 0.9  # Placeholder
        }
    
    def _calculate_molecular_weight(self, protein_sequence: str) -> float:
        """Calculate approximate molecular weight of protein."""
        # Simplified calculation using average amino acid weight
        avg_aa_weight = 110.0  # Daltons
        return len(protein_sequence) * avg_aa_weight
    
    # Cache management methods
    def clear_sequence_cache(self, sequence_data: str):
        """Clear cache for a specific sequence."""
        from ..services.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager()
        cache_key = CacheKeyGenerator.genomics_sequence_key(sequence_data)
        cache_manager.delete(cache_key, CacheType.GENOMICS_ANALYSIS)
        self.logger.info(f"Cleared cache for sequence")
    
    def clear_all_genomics_cache(self):
        """Clear all genomics-related cache entries."""
        from ..services.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager()
        cleared = cache_manager.clear_by_type(CacheType.GENOMICS_ANALYSIS)
        self.logger.info(f"Cleared {cleared} genomics cache entries")
        
        return cleared
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for genomics operations."""
        from ..services.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager()
        metrics = cache_manager.get_metrics()
        
        return {
            "total_requests": metrics.total_requests,
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "hit_rate": metrics.hit_rate,
            "genomics_entries": len(cache_manager.backend.list_keys(CacheType.GENOMICS_ANALYSIS))
        }


# Example usage and integration patterns
class CacheIntegrationExample:
    """
    Example showing different cache integration patterns.
    """
    
    def __init__(self):
        """Initialize example."""
        self.genomics_agent = CachedGenomicsAgent()
    
    def demonstrate_basic_caching(self):
        """Demonstrate basic caching functionality."""
        sample_sequence = ">test_sequence\nATGCGTAAGCTAGCTAGCTAGCTAA"
        
        print("First analysis (will be cached):")
        start_time = time.time()
        result1 = self.genomics_agent.analyze_sequence(sample_sequence)
        time1 = time.time() - start_time
        print(f"Analysis completed in {time1:.3f} seconds")
        print(f"Found {len(result1.genes)} genes, {len(result1.mutations)} mutations")
        
        print("\nSecond analysis (from cache):")
        start_time = time.time()
        result2 = self.genomics_agent.analyze_sequence(sample_sequence)
        time2 = time.time() - start_time
        print(f"Analysis completed in {time2:.3f} seconds")
        print(f"Found {len(result2.genes)} genes, {len(result2.mutations)} mutations")
        
        print(f"\nSpeedup: {time1/time2:.1f}x faster")
        
        # Show cache stats
        stats = self.genomics_agent.get_cache_stats()
        print(f"Cache hit rate: {stats['hit_rate']:.1%}")
    
    def demonstrate_cache_invalidation(self):
        """Demonstrate cache invalidation."""
        sample_sequence = ">test_sequence\nATGCGTAAGCTAGCTAGCTAGCTAA"
        
        # Analyze sequence (will be cached)
        result1 = self.genomics_agent.analyze_sequence(sample_sequence)
        print(f"Initial analysis: {len(result1.genes)} genes")
        
        # Clear cache for this sequence
        self.genomics_agent.clear_sequence_cache(sample_sequence)
        print("Cache cleared for sequence")
        
        # Analyze again (will not use cache)
        result2 = self.genomics_agent.analyze_sequence(sample_sequence)
        print(f"Re-analysis: {len(result2.genes)} genes")
    
    def demonstrate_cache_monitoring(self):
        """Demonstrate cache monitoring."""
        from ..services.cache_monitor import get_cache_monitor
        
        monitor = get_cache_monitor()
        
        # Perform some operations
        sample_sequences = [
            ">seq1\nATGCGTAAGCTAGCTAGCTAGCTAA",
            ">seq2\nGCTAGCTAGCTAGCTAATGCGTAAG",
            ">seq3\nTAGCTAGCTAGCTAAATGCGTAAGC"
        ]
        
        for seq in sample_sequences:
            self.genomics_agent.analyze_sequence(seq)
        
        # Get health status
        health = monitor.health_check()
        print(f"Cache health: {'Healthy' if health.is_healthy else 'Unhealthy'}")
        print(f"Hit rate: {health.hit_rate:.1%}")
        print(f"Total entries: {health.total_entries}")
        
        # Get performance report
        report = monitor.get_performance_report(hours=1)
        print(f"Total requests: {report.total_requests}")
        print(f"Cache hits: {report.cache_hits}")
        print(f"Cache misses: {report.cache_misses}")


if __name__ == "__main__":
    import time
    
    # Run examples
    example = CacheIntegrationExample()
    
    print("=== Basic Caching Demo ===")
    example.demonstrate_basic_caching()
    
    print("\n=== Cache Invalidation Demo ===")
    example.demonstrate_cache_invalidation()
    
    print("\n=== Cache Monitoring Demo ===")
    example.demonstrate_cache_monitoring()