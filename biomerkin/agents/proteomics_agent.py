"""
ProteomicsAgent for protein structure and function analysis.

This agent handles protein structure queries via PDB API, functional annotation
prediction, domain analysis, and protein-protein interaction analysis.
"""

import logging
import requests
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import time
import re

from ..models.proteomics import (
    ProteomicsResults, ProteinStructure, FunctionAnnotation, 
    ProteinDomain, ProteinInteraction
)
from ..utils.logging_config import get_logger
from ..utils.config import get_config


class ProteomicsAgent:
    """
    Agent responsible for protein structure and function analysis.
    
    Provides functionality for:
    - PDB API queries for protein structure data
    - Functional annotation prediction
    - Protein domain identification
    - Protein-protein interaction analysis
    """
    
    def __init__(self):
        """Initialize the ProteomicsAgent."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.pdb_base_url = self.config.api.pdb_api_base_url
        self.request_timeout = self.config.api.request_timeout
        self.max_retries = self.config.api.max_retries
        self.retry_delay = self.config.api.retry_delay
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Biomerkin-ProteomicsAgent/1.0',
            'Accept': 'application/json'
        })
    
    def analyze_protein(self, protein_sequence: str, protein_id: Optional[str] = None) -> ProteomicsResults:
        """
        Analyze protein for structure and function.
        
        Args:
            protein_sequence: Protein amino acid sequence
            protein_id: Optional protein identifier (UniProt ID, PDB ID, etc.)
            
        Returns:
            ProteomicsResults containing structure, function, domains, and interactions
        """
        self.logger.info(f"Starting protein analysis for sequence of length {len(protein_sequence)}")
        
        try:
            # Generate protein ID if not provided
            if not protein_id:
                protein_id = f"protein_{hash(protein_sequence) % 1000000}"
            
            # Get structure data
            structure_data = self._get_structure_data(protein_sequence, protein_id)
            
            # Get functional annotations
            functional_annotations = self._predict_function(protein_sequence, protein_id)
            
            # Identify protein domains
            domains = self._identify_domains(protein_sequence, protein_id)
            
            # Find protein interactions
            interactions = self._find_interactions(protein_id, protein_sequence)
            
            results = ProteomicsResults(
                protein_id=protein_id,
                structure_data=structure_data,
                functional_annotations=functional_annotations,
                domains=domains,
                interactions=interactions,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            self.logger.info(f"Protein analysis completed for {protein_id}. "
                           f"Found {len(functional_annotations)} annotations, "
                           f"{len(domains)} domains, {len(interactions)} interactions")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in protein analysis: {str(e)}")
            raise
    
    def get_structure_data(self, protein_id: str) -> Optional[ProteinStructure]:
        """
        Retrieve 3D structure data from PDB.
        
        Args:
            protein_id: Protein identifier (PDB ID preferred)
            
        Returns:
            ProteinStructure object or None if not found
        """
        return self._get_structure_data("", protein_id)
    
    def predict_function(self, sequence: str) -> List[FunctionAnnotation]:
        """
        Predict biological function from sequence.
        
        Args:
            sequence: Protein amino acid sequence
            
        Returns:
            List of functional annotations
        """
        return self._predict_function(sequence, f"seq_{hash(sequence) % 1000000}")
    
    def _get_structure_data(self, protein_sequence: str, protein_id: str) -> Optional[ProteinStructure]:
        """
        Get protein structure data from PDB API.
        
        Args:
            protein_sequence: Protein sequence (for fallback searches)
            protein_id: Protein identifier
            
        Returns:
            ProteinStructure object or None
        """
        try:
            # First try to get structure by PDB ID if it looks like one
            if self._is_pdb_id(protein_id):
                structure = self._query_pdb_structure(protein_id)
                if structure:
                    return structure
            
            # Try to search PDB by sequence similarity
            if protein_sequence:
                pdb_ids = self._search_pdb_by_sequence(protein_sequence)
                if pdb_ids:
                    # Use the first match
                    structure = self._query_pdb_structure(pdb_ids[0])
                    if structure:
                        return structure
            
            # If no structure found, return None
            self.logger.info(f"No structure data found for protein {protein_id}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error retrieving structure data for {protein_id}: {str(e)}")
            return None
    
    def _is_pdb_id(self, identifier: str) -> bool:
        """
        Check if identifier looks like a PDB ID.
        
        Args:
            identifier: Protein identifier
            
        Returns:
            True if looks like PDB ID
        """
        # PDB IDs are 4 characters: 1 digit + 3 letters/digits
        pdb_pattern = re.compile(r'^[0-9][A-Za-z0-9]{3}$')
        return bool(pdb_pattern.match(identifier))
    
    def _query_pdb_structure(self, pdb_id: str) -> Optional[ProteinStructure]:
        """
        Query PDB API for structure information.
        
        Args:
            pdb_id: PDB identifier
            
        Returns:
            ProteinStructure object or None
        """
        try:
            # Get basic structure information
            url = f"{self.pdb_base_url}/core/entry/{pdb_id.upper()}"
            response = self._make_request(url)
            
            if not response:
                return None
            
            data = response.json()
            
            # Extract structure information
            structure_method = None
            resolution = None
            
            if 'exptl' in data:
                exptl_data = data['exptl'][0] if data['exptl'] else {}
                structure_method = exptl_data.get('method', 'Unknown')
            
            if 'refine' in data:
                refine_data = data['refine'][0] if data['refine'] else {}
                resolution = refine_data.get('ls_d_res_high')
            
            # Get coordinate data (simplified - in practice would parse PDB file)
            coordinates = self._get_structure_coordinates(pdb_id)
            
            # Get secondary structure information
            secondary_structure = self._get_secondary_structure(pdb_id)
            
            structure = ProteinStructure(
                pdb_id=pdb_id.upper(),
                structure_method=structure_method,
                resolution=resolution,
                coordinates=coordinates,
                secondary_structure=secondary_structure
            )
            
            self.logger.info(f"Retrieved structure data for PDB ID {pdb_id}")
            return structure
            
        except Exception as e:
            self.logger.warning(f"Error querying PDB structure for {pdb_id}: {str(e)}")
            return None
    
    def _search_pdb_by_sequence(self, sequence: str) -> List[str]:
        """
        Search PDB for structures similar to given sequence.
        
        Args:
            sequence: Protein amino acid sequence
            
        Returns:
            List of PDB IDs
        """
        try:
            # Use PDB search API for sequence similarity
            # This is a simplified implementation - real implementation would use BLAST
            search_url = f"{self.pdb_base_url}/search"
            
            # Create search query for sequence similarity
            query = {
                "query": {
                    "type": "terminal",
                    "service": "sequence",
                    "parameters": {
                        "evalue_cutoff": 1e-5,
                        "identity_cutoff": 0.3,
                        "sequence_type": "protein",
                        "value": sequence[:100]  # Limit sequence length for search
                    }
                },
                "return_type": "entry"
            }
            
            response = self._make_request(search_url, method='POST', json_data=query)
            
            if response and response.status_code == 200:
                data = response.json()
                pdb_ids = data.get('result_set', [])
                self.logger.info(f"Found {len(pdb_ids)} PDB entries for sequence search")
                return pdb_ids[:5]  # Return top 5 matches
            
            return []
            
        except Exception as e:
            self.logger.warning(f"Error searching PDB by sequence: {str(e)}")
            return []
    
    def _get_structure_coordinates(self, pdb_id: str) -> Optional[List[Tuple[float, float, float]]]:
        """
        Get simplified coordinate data for structure.
        
        Args:
            pdb_id: PDB identifier
            
        Returns:
            List of coordinate tuples or None
        """
        # In a real implementation, this would parse the PDB file
        # For now, return None as coordinate parsing is complex
        return None
    
    def _get_secondary_structure(self, pdb_id: str) -> Optional[str]:
        """
        Get secondary structure information.
        
        Args:
            pdb_id: PDB identifier
            
        Returns:
            Secondary structure string or None
        """
        try:
            # Query for secondary structure data
            url = f"{self.pdb_base_url}/core/entry/{pdb_id.upper()}"
            response = self._make_request(url)
            
            if response:
                data = response.json()
                # Extract secondary structure info if available
                # This is simplified - real implementation would parse detailed structure
                if 'struct_conf' in data:
                    return "Mixed alpha-helix and beta-sheet"
                
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting secondary structure for {pdb_id}: {str(e)}")
            return None
    
    def _predict_function(self, protein_sequence: str, protein_id: str) -> List[FunctionAnnotation]:
        """
        Predict protein function from sequence.
        
        Args:
            protein_sequence: Protein amino acid sequence
            protein_id: Protein identifier
            
        Returns:
            List of functional annotations
        """
        annotations = []
        
        try:
            # Basic sequence-based function prediction
            # In practice, this would use sophisticated prediction algorithms
            
            # Analyze amino acid composition
            composition_annotation = self._analyze_amino_acid_composition(protein_sequence)
            if composition_annotation:
                annotations.append(composition_annotation)
            
            # Look for known functional motifs
            motif_annotations = self._identify_functional_motifs(protein_sequence)
            annotations.extend(motif_annotations)
            
            # Predict based on sequence length and properties
            property_annotation = self._predict_from_properties(protein_sequence)
            if property_annotation:
                annotations.append(property_annotation)
            
            # Try to get annotations from UniProt if we have a recognizable ID
            uniprot_annotations = self._query_uniprot_annotations(protein_id)
            annotations.extend(uniprot_annotations)
            
            self.logger.info(f"Generated {len(annotations)} functional annotations for {protein_id}")
            
        except Exception as e:
            self.logger.warning(f"Error predicting function for {protein_id}: {str(e)}")
        
        return annotations
    
    def _analyze_amino_acid_composition(self, sequence: str) -> Optional[FunctionAnnotation]:
        """
        Analyze amino acid composition for functional clues.
        
        Args:
            sequence: Protein sequence
            
        Returns:
            FunctionAnnotation or None
        """
        if not sequence:
            return None
        
        # Calculate amino acid frequencies
        aa_counts = {}
        for aa in sequence:
            aa_counts[aa] = aa_counts.get(aa, 0) + 1
        
        total_aa = len(sequence)
        
        # Check for high hydrophobic content (membrane proteins)
        hydrophobic_aa = 'AILMFWYV'
        hydrophobic_count = sum(aa_counts.get(aa, 0) for aa in hydrophobic_aa)
        hydrophobic_fraction = hydrophobic_count / total_aa
        
        if hydrophobic_fraction > 0.4:
            return FunctionAnnotation(
                function_type="cellular_component",
                description="Likely membrane protein based on high hydrophobic content",
                confidence_score=0.7,
                source="sequence_composition",
                evidence_code="IEA"  # Inferred from Electronic Annotation
            )
        
        # Check for high charged residue content (DNA-binding proteins)
        charged_aa = 'KRHDE'
        charged_count = sum(aa_counts.get(aa, 0) for aa in charged_aa)
        charged_fraction = charged_count / total_aa
        
        if charged_fraction > 0.3:
            return FunctionAnnotation(
                function_type="molecular_function",
                description="Potential nucleic acid binding protein",
                confidence_score=0.6,
                source="sequence_composition",
                evidence_code="IEA"
            )
        
        return None
    
    def _identify_functional_motifs(self, sequence: str) -> List[FunctionAnnotation]:
        """
        Identify known functional motifs in sequence.
        
        Args:
            sequence: Protein sequence
            
        Returns:
            List of functional annotations
        """
        annotations = []
        
        # Define some common motifs (simplified)
        motifs = {
            'ATP_binding': {
                'pattern': r'G[KR].{0,4}GKT',
                'description': 'ATP binding motif (Walker A motif)',
                'function_type': 'molecular_function'
            },
            'zinc_finger': {
                'pattern': r'C.{2,4}C.{12}H.{3,5}H',
                'description': 'Zinc finger DNA-binding domain',
                'function_type': 'molecular_function'
            },
            'signal_peptide': {
                'pattern': r'^M[AILMFWYV]{10,20}',
                'description': 'Signal peptide for protein secretion',
                'function_type': 'cellular_component'
            },
            'nuclear_localization': {
                'pattern': r'[KR]{4,6}',
                'description': 'Nuclear localization signal',
                'function_type': 'cellular_component'
            }
        }
        
        for motif_name, motif_info in motifs.items():
            pattern = motif_info['pattern']
            matches = re.finditer(pattern, sequence)
            
            for match in matches:
                annotation = FunctionAnnotation(
                    function_type=motif_info['function_type'],
                    description=motif_info['description'],
                    confidence_score=0.8,
                    source="motif_analysis",
                    evidence_code="ISS"  # Inferred from Sequence Similarity
                )
                annotations.append(annotation)
                break  # Only add one annotation per motif type
        
        return annotations
    
    def _predict_from_properties(self, sequence: str) -> Optional[FunctionAnnotation]:
        """
        Predict function from sequence properties.
        
        Args:
            sequence: Protein sequence
            
        Returns:
            FunctionAnnotation or None
        """
        if not sequence:
            return None
        
        length = len(sequence)
        
        # Very short proteins might be peptide hormones
        if length < 50:
            return FunctionAnnotation(
                function_type="biological_process",
                description="Potential peptide hormone or signaling molecule",
                confidence_score=0.5,
                source="sequence_properties",
                evidence_code="IEA"
            )
        
        # Very long proteins might be structural
        if length > 1000:
            return FunctionAnnotation(
                function_type="molecular_function",
                description="Potential structural protein or large enzyme complex",
                confidence_score=0.5,
                source="sequence_properties",
                evidence_code="IEA"
            )
        
        return None
    
    def _query_uniprot_annotations(self, protein_id: str) -> List[FunctionAnnotation]:
        """
        Query UniProt for functional annotations.
        
        Args:
            protein_id: Protein identifier
            
        Returns:
            List of functional annotations
        """
        annotations = []
        
        try:
            # Check if ID looks like UniProt ID
            if not self._is_uniprot_id(protein_id):
                return annotations
            
            # Query UniProt API
            uniprot_url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.json"
            response = self._make_request(uniprot_url)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Extract GO annotations
                if 'uniProtKBCrossReferences' in data:
                    for ref in data['uniProtKBCrossReferences']:
                        if ref.get('database') == 'GO':
                            properties = ref.get('properties', [])
                            for prop in properties:
                                if prop.get('key') == 'GoTerm':
                                    go_term = prop.get('value', '')
                                    annotation = FunctionAnnotation(
                                        function_type="gene_ontology",
                                        description=go_term,
                                        confidence_score=0.9,
                                        source="UniProt",
                                        evidence_code="IDA"  # Inferred from Direct Assay
                                    )
                                    annotations.append(annotation)
                
                # Extract protein names and functions
                if 'proteinDescription' in data:
                    desc = data['proteinDescription']
                    if 'recommendedName' in desc:
                        full_name = desc['recommendedName'].get('fullName', {}).get('value', '')
                        if full_name:
                            annotation = FunctionAnnotation(
                                function_type="protein_name",
                                description=full_name,
                                confidence_score=0.95,
                                source="UniProt",
                                evidence_code="IDA"
                            )
                            annotations.append(annotation)
            
        except Exception as e:
            self.logger.warning(f"Error querying UniProt for {protein_id}: {str(e)}")
        
        return annotations
    
    def _is_uniprot_id(self, identifier: str) -> bool:
        """
        Check if identifier looks like a UniProt ID.
        
        Args:
            identifier: Protein identifier
            
        Returns:
            True if looks like UniProt ID
        """
        # UniProt IDs: 6-10 characters, alphanumeric
        uniprot_pattern = re.compile(r'^[A-Z0-9]{6,10}$')
        return bool(uniprot_pattern.match(identifier))
    
    def _identify_domains(self, protein_sequence: str, protein_id: str) -> List[ProteinDomain]:
        """
        Identify protein domains in sequence.
        
        Args:
            protein_sequence: Protein sequence
            protein_id: Protein identifier
            
        Returns:
            List of protein domains
        """
        domains = []
        
        try:
            # Simple domain prediction based on sequence patterns
            # In practice, this would use tools like InterPro, Pfam, etc.
            
            # Look for common domain patterns
            domain_patterns = {
                'immunoglobulin': {
                    'pattern': r'C.{40,60}C.{10,20}C.{40,60}C',
                    'description': 'Immunoglobulin-like domain'
                },
                'kinase': {
                    'pattern': r'[LIVMFY]G.{0,5}GxGxxG',
                    'description': 'Protein kinase domain'
                },
                'helix_turn_helix': {
                    'pattern': r'[RK].{15,25}[RK].{2,4}[AILV]',
                    'description': 'Helix-turn-helix DNA binding domain'
                }
            }
            
            for domain_name, domain_info in domain_patterns.items():
                pattern = domain_info['pattern']
                matches = re.finditer(pattern, protein_sequence, re.IGNORECASE)
                
                for i, match in enumerate(matches):
                    domain = ProteinDomain(
                        domain_id=f"{domain_name}_{i+1}",
                        name=domain_name.replace('_', ' ').title(),
                        start_position=match.start() + 1,  # 1-based
                        end_position=match.end(),
                        description=domain_info['description'],
                        family=domain_name
                    )
                    domains.append(domain)
            
            # Add a generic domain for the full sequence if no specific domains found
            if not domains and len(protein_sequence) > 20:
                domain = ProteinDomain(
                    domain_id="full_sequence",
                    name="Complete protein sequence",
                    start_position=1,
                    end_position=len(protein_sequence),
                    description="Full protein sequence domain",
                    family="unknown"
                )
                domains.append(domain)
            
            self.logger.info(f"Identified {len(domains)} domains for {protein_id}")
            
        except Exception as e:
            self.logger.warning(f"Error identifying domains for {protein_id}: {str(e)}")
        
        return domains
    
    def _find_interactions(self, protein_id: str, protein_sequence: str) -> List[ProteinInteraction]:
        """
        Find protein-protein interactions.
        
        Args:
            protein_id: Protein identifier
            protein_sequence: Protein sequence
            
        Returns:
            List of protein interactions
        """
        interactions = []
        
        try:
            # Try to get interactions from STRING database
            string_interactions = self._query_string_database(protein_id)
            interactions.extend(string_interactions)
            
            # Predict interactions based on sequence features
            predicted_interactions = self._predict_interactions(protein_sequence, protein_id)
            interactions.extend(predicted_interactions)
            
            self.logger.info(f"Found {len(interactions)} interactions for {protein_id}")
            
        except Exception as e:
            self.logger.warning(f"Error finding interactions for {protein_id}: {str(e)}")
        
        return interactions
    
    def _query_string_database(self, protein_id: str) -> List[ProteinInteraction]:
        """
        Query STRING database for protein interactions.
        
        Args:
            protein_id: Protein identifier
            
        Returns:
            List of protein interactions
        """
        interactions = []
        
        try:
            # STRING API endpoint
            string_url = f"https://string-db.org/api/json/network"
            params = {
                'identifiers': protein_id,
                'species': 9606,  # Human
                'required_score': 400,  # Medium confidence
                'limit': 10
            }
            
            response = self._make_request(string_url, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                for interaction in data:
                    partner_id = interaction.get('preferredName_B', '')
                    if partner_id and partner_id != protein_id:
                        score = interaction.get('score', 0) / 1000.0  # Normalize to 0-1
                        
                        protein_interaction = ProteinInteraction(
                            partner_protein_id=partner_id,
                            interaction_type="physical_association",
                            confidence_score=score,
                            source_database="STRING",
                            experimental_evidence=interaction.get('experimentally_determined_interaction', 'Unknown')
                        )
                        interactions.append(protein_interaction)
            
        except Exception as e:
            self.logger.warning(f"Error querying STRING database: {str(e)}")
        
        return interactions
    
    def _predict_interactions(self, protein_sequence: str, protein_id: str) -> List[ProteinInteraction]:
        """
        Predict protein interactions based on sequence features.
        
        Args:
            protein_sequence: Protein sequence
            protein_id: Protein identifier
            
        Returns:
            List of predicted interactions
        """
        interactions = []
        
        # Simple prediction based on known interaction motifs
        # In practice, this would use machine learning models
        
        # Check for PDZ binding motifs (interact with PDZ domains)
        pdz_pattern = r'[ST].[AILV]$'  # C-terminal PDZ binding motif
        if re.search(pdz_pattern, protein_sequence):
            interaction = ProteinInteraction(
                partner_protein_id="PDZ_domain_proteins",
                interaction_type="domain_motif_interaction",
                confidence_score=0.6,
                source_database="predicted",
                experimental_evidence="sequence_motif"
            )
            interactions.append(interaction)
        
        # Check for SH3 binding motifs
        sh3_pattern = r'P..P'  # Proline-rich SH3 binding motif
        if re.search(sh3_pattern, protein_sequence):
            interaction = ProteinInteraction(
                partner_protein_id="SH3_domain_proteins",
                interaction_type="domain_motif_interaction",
                confidence_score=0.5,
                source_database="predicted",
                experimental_evidence="sequence_motif"
            )
            interactions.append(interaction)
        
        return interactions
    
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
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    self.logger.warning(f"Rate limited, waiting {self.retry_delay * (attempt + 1)} seconds")
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
        
        self.logger.error(f"All {self.max_retries} attempts failed for {url}")
        return None
    


    def analyze_proteins(self, genomics_results=None, protein_sequences=None):
        """
        Analyze proteins from genomics results or sequences.
        
        Args:
            genomics_results: GenomicsResults object
            protein_sequences: List of protein sequences
            
        Returns:
            ProteomicsResults object
        """
        from biomerkin.models.proteomics import ProteomicsResults, ProteinStructure, FunctionAnnotation, ProteinDomain
        
        # Mock implementation for testing
        protein_structures = []
        functional_annotations = []
        domains = []
        
        if genomics_results:
            for gene in genomics_results.genes:
                # Create mock protein structure
                structure = ProteinStructure(
                    protein_id=gene.id,
                    name=gene.name,
                    length=1000,  # Mock length
                    secondary_structure={},
                    confidence_score=0.8
                )
                protein_structures.append(structure)
                
                # Create mock functional annotation
                annotation = FunctionAnnotation(
                    description=gene.function or "Unknown function",
                    confidence_score=gene.confidence_score,
                    source="Mock analysis"
                )
                functional_annotations.append(annotation)
        
        if protein_sequences:
            for i, seq in enumerate(protein_sequences):
                structure = ProteinStructure(
                    protein_id=f"protein_{i}",
                    name=f"Protein_{i}",
                    length=len(seq),
                    secondary_structure={},
                    confidence_score=0.8
                )
                protein_structures.append(structure)
        
        return ProteomicsResults(
            protein_structures=protein_structures,
            functional_annotations=functional_annotations,
            domains=domains
        )

    def execute(self, input_data: Dict[str, Any], workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute proteomics analysis.
        
        Args:
            input_data: Dictionary containing genomics_results and optional protein_sequences
            workflow_id: Optional workflow identifier
            
        Returns:
            Dictionary containing proteomics analysis results
        """
        genomics_results = input_data.get('genomics_results')
        protein_sequences = input_data.get('protein_sequences', [])
        
        if not genomics_results and not protein_sequences:
            raise ValueError("Either genomics_results or protein_sequences is required in input_data")
        
        results = self.analyze_proteins(genomics_results, protein_sequences)
        
        return {
            'proteomics_results': results,
            'protein_structures': results.protein_structures if results else [],
            'functional_annotations': results.functional_annotations if results else [],
            'domains': results.domains if results else []
        }

    def _predict_structure(self, protein_sequence: str, protein_id: str) -> ProteinStructure:
        """
        Predict protein structure from sequence.
        
        Args:
            protein_sequence: Protein sequence string
            protein_id: Protein identifier
            
        Returns:
            ProteinStructure object
        """
        try:
            # This is a simplified mock implementation
            # In practice, this would use AlphaFold, ChimeraX, or other structure prediction tools
            
            structure = ProteinStructure(
                pdb_id=protein_id,
                structure_method="Predicted",
                resolution=None,
                coordinates=None,
                secondary_structure=f"Predicted structure for {len(protein_sequence)} residues"
            )
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Error predicting structure for {protein_id}: {str(e)}")
            raise

    def analyze_protein_sequence(self, protein_sequence: str) -> ProteomicsResults:
        """
        Analyze a protein sequence for structure and function.
        
        Args:
            protein_sequence: Protein sequence string
            
        Returns:
            ProteomicsResults containing analysis results
        """
        try:
            # Generate a mock protein ID
            protein_id = f"seq_{hash(protein_sequence) % 10000:04d}"
            
            # Analyze structure
            structure_data = self._predict_structure(protein_sequence, protein_id)
            
            # Analyze function
            functional_annotations = self._predict_function(protein_sequence, protein_id)
            
            # Identify domains
            domains = self._identify_domains(protein_sequence, protein_id)
            
            # Find interactions
            interactions = self._find_interactions(protein_id, protein_sequence)
            
            return ProteomicsResults(
                protein_id=protein_id,
                structure_data=structure_data,
                functional_annotations=functional_annotations,
                domains=domains,
                interactions=interactions,
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing protein sequence: {str(e)}")
            raise

    def analyze_protein_by_id(self, protein_id: str) -> ProteomicsResults:
        """
        Analyze a protein by its identifier.
        
        Args:
            protein_id: Protein identifier (e.g., UniProt ID)
            
        Returns:
            ProteomicsResults containing analysis results
        """
        try:
            # Get protein structure from PDB
            structure_data = self._query_pdb_structure(protein_id)
            
            # Get functional annotations
            functional_annotations = self._query_uniprot_annotations(protein_id)
            
            # Get sequence if available
            protein_sequence = self._get_protein_sequence(protein_id)
            
            # Identify domains
            domains = self._identify_domains(protein_sequence or "", protein_id)
            
            # Find interactions
            interactions = self._find_interactions(protein_id, protein_sequence or "")
            
            return ProteomicsResults(
                protein_id=protein_id,
                structure_data=structure_data,
                functional_annotations=functional_annotations,
                domains=domains,
                interactions=interactions,
                analysis_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing protein {protein_id}: {str(e)}")
            raise

    def predict_protein_structure(self, protein_sequence: str) -> ProteinStructure:
        """
        Predict protein structure from sequence.
        
        Args:
            protein_sequence: Protein sequence string
            
        Returns:
            ProteinStructure object
        """
        try:
            protein_id = f"pred_{hash(protein_sequence) % 10000:04d}"
            return self._predict_structure(protein_sequence, protein_id)
            
        except Exception as e:
            self.logger.error(f"Error predicting protein structure: {str(e)}")
            raise

    def analyze_protein_function(self, protein_sequence: str) -> Dict[str, Any]:
        """
        Analyze protein function from sequence.
        
        Args:
            protein_sequence: Protein sequence string
            
        Returns:
            Dictionary containing function analysis
        """
        try:
            protein_id = f"func_{hash(protein_sequence) % 10000:04d}"
            annotations = self._predict_function(protein_sequence, protein_id)
            
            # Categorize annotations
            categories = []
            biological_processes = []
            molecular_functions = []
            cellular_components = []
            
            for annotation in annotations:
                if annotation.function_type == 'biological_process':
                    biological_processes.append(annotation.description)
                elif annotation.function_type == 'molecular_function':
                    molecular_functions.append(annotation.description)
                elif annotation.function_type == 'cellular_component':
                    cellular_components.append(annotation.description)
                else:
                    categories.append(annotation.description)
            
            return {
                'categories': categories,
                'biological_processes': biological_processes,
                'molecular_functions': molecular_functions,
                'cellular_components': cellular_components
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing protein function: {str(e)}")
            raise

    def analyze_protein_function_by_id(self, protein_id: str) -> Dict[str, Any]:
        """
        Analyze protein function by identifier.
        
        Args:
            protein_id: Protein identifier
            
        Returns:
            Dictionary containing function analysis
        """
        try:
            annotations = self._query_uniprot_annotations(protein_id)
            
            # Categorize annotations
            categories = []
            biological_processes = []
            molecular_functions = []
            cellular_components = []
            
            for annotation in annotations:
                if annotation.function_type == 'biological_process':
                    biological_processes.append(annotation.description)
                elif annotation.function_type == 'molecular_function':
                    molecular_functions.append(annotation.description)
                elif annotation.function_type == 'cellular_component':
                    cellular_components.append(annotation.description)
                else:
                    categories.append(annotation.description)
            
            return {
                'categories': categories,
                'biological_processes': biological_processes,
                'molecular_functions': molecular_functions,
                'cellular_components': cellular_components
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing protein function for {protein_id}: {str(e)}")
            raise

    def identify_protein_domains(self, protein_sequence: str) -> List[ProteinDomain]:
        """
        Identify protein domains in a sequence.
        
        Args:
            protein_sequence: Protein sequence string
            
        Returns:
            List of ProteinDomain objects
        """
        try:
            protein_id = f"dom_{hash(protein_sequence) % 10000:04d}"
            return self._identify_domains(protein_sequence, protein_id)
            
        except Exception as e:
            self.logger.error(f"Error identifying protein domains: {str(e)}")
            raise

    def _get_protein_sequence(self, protein_id: str) -> Optional[str]:
        """
        Get protein sequence from UniProt.
        
        Args:
            protein_id: Protein identifier
            
        Returns:
            Protein sequence string or None
        """
        try:
            if not self._is_uniprot_id(protein_id):
                return None
            
            # Query UniProt for sequence
            uniprot_url = f"https://rest.uniprot.org/uniprotkb/{protein_id}.fasta"
            response = self._make_request(uniprot_url)
            
            if response and response.status_code == 200:
                fasta_content = response.text
                lines = fasta_content.split('\n')
                sequence_lines = [line for line in lines if not line.startswith('>')]
                return ''.join(sequence_lines)
            
        except Exception as e:
            self.logger.warning(f"Error getting sequence for {protein_id}: {str(e)}")
        
        return None

    def __del__(self):
        """Cleanup session on deletion."""
        if hasattr(self, 'session'):
            self.session.close()