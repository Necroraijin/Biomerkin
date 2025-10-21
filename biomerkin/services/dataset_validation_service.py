"""
Dataset Validation Service for handling unknown/external datasets.
Ensures system can handle judge-provided datasets with high accuracy.
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from Bio import SeqIO
from Bio.Seq import Seq
import hashlib

from ..utils.logging_config import get_logger
from ..models.base import QualityMetrics


class DatasetValidationService:
    """
    Validates and preprocesses unknown datasets for analysis.
    Ensures system handles diverse input formats and data quality.
    """
    
    SUPPORTED_FORMATS = ['fasta', 'fa', 'fna', 'ffn', 'faa', 'frn', 'genbank', 'gb', 'gbk']
    MAX_SEQUENCE_LENGTH = 10_000_000  # 10MB for safety
    MIN_SEQUENCE_LENGTH = 10  # Minimum viable sequence
    
    def __init__(self):
        """Initialize dataset validation service."""
        self.logger = get_logger(__name__)
        self.validation_cache = {}
    
    def validate_dataset(
        self,
        file_path: str,
        expected_type: str = 'auto'
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of input dataset.
        
        Args:
            file_path: Path to dataset file
            expected_type: Expected data type (genomics, proteomics, or auto)
            
        Returns:
            Validation result dictionary with status, format, and metadata
        """
        self.logger.info(f"Validating dataset: {file_path}")
        
        validation_result = {
            'is_valid': False,
            'file_path': file_path,
            'file_format': None,
            'sequence_count': 0,
            'total_length': 0,
            'quality_score': 0.0,
            'warnings': [],
            'errors': [],
            'metadata': {},
            'data_type': expected_type
        }
        
        try:
            # Check file existence
            if not os.path.exists(file_path):
                validation_result['errors'].append(f"File not found: {file_path}")
                return validation_result
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                validation_result['errors'].append("File is empty")
                return validation_result
            
            if file_size > self.MAX_SEQUENCE_LENGTH:
                validation_result['warnings'].append(f"Large file: {file_size} bytes. Processing may take longer.")
            
            # Detect file format
            file_format = self._detect_format(file_path)
            validation_result['file_format'] = file_format
            
            if not file_format:
                validation_result['errors'].append("Unsupported or unknown file format")
                return validation_result
            
            # Parse and validate sequences
            sequences = self._parse_sequences(file_path, file_format)
            validation_result['sequence_count'] = len(sequences)
            
            if not sequences:
                validation_result['errors'].append("No valid sequences found")
                return validation_result
            
            # Analyze sequences
            sequence_analysis = self._analyze_sequences(sequences, expected_type)
            validation_result.update(sequence_analysis)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(validation_result)
            validation_result['quality_score'] = quality_score
            
            # Determine if valid
            validation_result['is_valid'] = (
                len(validation_result['errors']) == 0 and
                quality_score >= 50.0  # Minimum acceptable quality
            )
            
            self.logger.info(f"Validation complete. Valid: {validation_result['is_valid']}, Quality: {quality_score:.1f}")
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            validation_result['errors'].append(f"Validation exception: {str(e)}")
        
        return validation_result
    
    def preprocess_dataset(
        self,
        file_path: str,
        validation_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Preprocess dataset for optimal analysis.
        
        Args:
            file_path: Path to dataset file
            validation_result: Optional pre-computed validation result
            
        Returns:
            Preprocessed data dictionary
        """
        if validation_result is None:
            validation_result = self.validate_dataset(file_path)
        
        if not validation_result['is_valid']:
            raise ValueError(f"Invalid dataset: {validation_result['errors']}")
        
        preprocessed = {
            'original_file': file_path,
            'file_format': validation_result['file_format'],
            'sequences': [],
            'metadata': validation_result['metadata'],
            'preprocessing_applied': []
        }
        
        # Load sequences
        sequences = self._parse_sequences(file_path, validation_result['file_format'])
        
        # Apply preprocessing steps
        for seq_record in sequences:
            processed_seq = self._preprocess_sequence(seq_record, validation_result['data_type'])
            preprocessed['sequences'].append(processed_seq)
        
        return preprocessed
    
    def _detect_format(self, file_path: str) -> Optional[str]:
        """
        Detect file format from extension and content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Detected format or None
        """
        # Check extension
        extension = Path(file_path).suffix.lower().lstrip('.')
        if extension in self.SUPPORTED_FORMATS:
            return 'fasta' if extension in ['fasta', 'fa', 'fna', 'ffn', 'faa', 'frn'] else 'genbank'
        
        # Check content
        try:
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                
                # FASTA format check
                if first_line.startswith('>'):
                    return 'fasta'
                
                # GenBank format check
                if first_line.startswith('LOCUS'):
                    return 'genbank'
                
                # Try to parse as raw sequence
                if self._is_valid_sequence(first_line):
                    return 'raw'
        
        except Exception as e:
            self.logger.warning(f"Could not detect format: {e}")
        
        return None
    
    def _parse_sequences(self, file_path: str, file_format: str) -> List[Any]:
        """
        Parse sequences from file.
        
        Args:
            file_path: Path to file
            file_format: File format
            
        Returns:
            List of sequence records
        """
        sequences = []
        
        try:
            if file_format == 'raw':
                # Handle raw sequence data
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    # Remove whitespace and create record
                    seq_string = ''.join(content.split())
                    if self._is_valid_sequence(seq_string):
                        from Bio.SeqRecord import SeqRecord
                        record = SeqRecord(Seq(seq_string), id="sequence_1", description="Raw sequence")
                        sequences.append(record)
            else:
                # Use BioPython for standard formats
                for record in SeqIO.parse(file_path, file_format):
                    sequences.append(record)
        
        except Exception as e:
            self.logger.error(f"Error parsing sequences: {e}")
        
        return sequences
    
    def _analyze_sequences(self, sequences: List[Any], expected_type: str) -> Dict[str, Any]:
        """
        Analyze parsed sequences.
        
        Args:
            sequences: List of sequence records
            expected_type: Expected data type
            
        Returns:
            Analysis results dictionary
        """
        analysis = {
            'total_length': 0,
            'avg_length': 0,
            'gc_content': 0.0,
            'sequence_type': None,
            'has_ambiguous': False,
            'metadata': {}
        }
        
        total_gc = 0
        total_bases = 0
        has_ambiguous = False
        
        for record in sequences:
            seq_str = str(record.seq).upper()
            seq_len = len(seq_str)
            analysis['total_length'] += seq_len
            
            # Calculate GC content
            gc_count = seq_str.count('G') + seq_str.count('C')
            total_gc += gc_count
            total_bases += seq_len
            
            # Check for ambiguous bases
            if any(base not in 'ATGC' for base in seq_str):
                has_ambiguous = True
        
        if total_bases > 0:
            analysis['gc_content'] = (total_gc / total_bases) * 100
            analysis['avg_length'] = analysis['total_length'] / len(sequences)
        
        analysis['has_ambiguous'] = has_ambiguous
        
        # Determine sequence type
        analysis['sequence_type'] = self._determine_sequence_type(sequences[0] if sequences else None, expected_type)
        
        return analysis
    
    def _determine_sequence_type(self, sample_record: Any, expected_type: str) -> str:
        """
        Determine if sequences are DNA, RNA, or protein.
        
        Args:
            sample_record: Sample sequence record
            expected_type: Expected type hint
            
        Returns:
            Sequence type (dna, rna, protein, or unknown)
        """
        if not sample_record:
            return 'unknown'
        
        if expected_type != 'auto':
            return expected_type
        
        seq_str = str(sample_record.seq).upper()
        
        # Check for protein sequences
        protein_chars = set('ARNDCEQGHILKMFPSTWYV')
        dna_chars = set('ATGC')
        rna_chars = set('AUGC')
        
        seq_chars = set(seq_str)
        
        # Remove common ambiguous codes
        seq_chars_clean = seq_chars - set('NX-')
        
        if seq_chars_clean.issubset(protein_chars) and not seq_chars_clean.issubset(dna_chars):
            return 'protein'
        elif 'U' in seq_chars:
            return 'rna'
        elif seq_chars_clean.issubset(dna_chars | set('N')):
            return 'dna'
        
        return 'unknown'
    
    def _is_valid_sequence(self, sequence: str) -> bool:
        """
        Check if string is a valid biological sequence.
        
        Args:
            sequence: Sequence string
            
        Returns:
            True if valid, False otherwise
        """
        # Remove whitespace
        seq = sequence.strip().upper()
        
        # Check length
        if len(seq) < self.MIN_SEQUENCE_LENGTH:
            return False
        
        # Check for valid characters (DNA/RNA/Protein + ambiguous codes)
        valid_chars = set('ATGCURYWSMKBDHVN-')
        return all(c in valid_chars for c in seq)
    
    def _preprocess_sequence(self, seq_record: Any, data_type: str) -> Dict[str, Any]:
        """
        Preprocess individual sequence.
        
        Args:
            seq_record: Sequence record
            data_type: Data type
            
        Returns:
            Preprocessed sequence dictionary
        """
        return {
            'id': seq_record.id,
            'description': seq_record.description,
            'sequence': str(seq_record.seq),
            'length': len(seq_record.seq),
            'checksum': hashlib.md5(str(seq_record.seq).encode()).hexdigest()
        }
    
    def _calculate_quality_score(self, validation_result: Dict[str, Any]) -> float:
        """
        Calculate overall quality score for dataset.
        
        Args:
            validation_result: Validation result dictionary
            
        Returns:
            Quality score (0-100)
        """
        score = 100.0
        
        # Penalize for errors
        score -= len(validation_result['errors']) * 30
        
        # Penalize for warnings
        score -= len(validation_result['warnings']) * 10
        
        # Bonus for having sequences
        if validation_result['sequence_count'] > 0:
            score += 10
        
        # Bonus for reasonable sequence lengths
        if validation_result.get('avg_length', 0) >= self.MIN_SEQUENCE_LENGTH:
            score += 10
        
        # Bonus for known format
        if validation_result['file_format'] in ['fasta', 'genbank']:
            score += 10
        
        # Ensure score is in valid range
        return max(0.0, min(100.0, score))
    
    def generate_quality_report(self, validation_result: Dict[str, Any]) -> str:
        """
        Generate human-readable quality report.
        
        Args:
            validation_result: Validation result
            
        Returns:
            Formatted quality report
        """
        report = []
        report.append("=" * 60)
        report.append("DATASET QUALITY REPORT")
        report.append("=" * 60)
        report.append(f"File: {validation_result['file_path']}")
        report.append(f"Format: {validation_result['file_format']}")
        report.append(f"Valid: {'✓ YES' if validation_result['is_valid'] else '✗ NO'}")
        report.append(f"Quality Score: {validation_result['quality_score']:.1f}/100")
        report.append("")
        report.append(f"Sequences: {validation_result['sequence_count']}")
        report.append(f"Total Length: {validation_result['total_length']:,} bp")
        
        if validation_result.get('gc_content'):
            report.append(f"GC Content: {validation_result['gc_content']:.1f}%")
        
        if validation_result['warnings']:
            report.append("\nWarnings:")
            for warning in validation_result['warnings']:
                report.append(f"  ⚠ {warning}")
        
        if validation_result['errors']:
            report.append("\nErrors:")
            for error in validation_result['errors']:
                report.append(f"  ✗ {error}")
        
        report.append("=" * 60)
        
        return '\n'.join(report)


# Singleton instance
_dataset_validation_service = None


def get_dataset_validation_service() -> DatasetValidationService:
    """Get or create dataset validation service instance."""
    global _dataset_validation_service
    if _dataset_validation_service is None:
        _dataset_validation_service = DatasetValidationService()
    return _dataset_validation_service

